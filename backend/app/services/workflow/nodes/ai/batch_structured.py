from app.locales import schema_field_description
import asyncio
import os
from typing import Any, Dict, List, Optional, AsyncIterator, Union, TYPE_CHECKING
from loguru import logger
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from ...engine.async_executor import ProgressEvent

from app.services.ai.core.model_builder import build_model_from_json_schema
from app.services.ai.core.llm_service import generate_structured
from ...registry import register_node
from ..base import BaseNode
from app.db.models import CardType
from app.services.card_type_service_utils import get_card_type_by_identifier
from app.schemas.response_registry import RESPONSE_MODEL_MAP
from sqlmodel import select


class BatchStructuredInput(BaseModel):
    items: List[Any] = Field(..., description=schema_field_description("items"))
    llm_config_id: int = Field(..., description=schema_field_description("llm_config_id"), json_schema_extra={"x-component": "LLMSelect"})
    prompt_template: str = Field(..., description=schema_field_description("prompt_template"), json_schema_extra={"x-component": "Textarea"})
    response_model_id: str = Field(..., description=schema_field_description("response_model_id"), json_schema_extra={"x-component": "ResponseModelSelect"})
    concurrency: int = Field(30, description=schema_field_description("concurrency"), ge=1)
    max_retries: int = Field(3, description=schema_field_description("max_retries"))
    temperature: float = Field(0.7, description=schema_field_description("temperature"))
    max_tokens: Optional[int] = Field(None, description=schema_field_description("max_tokens"))
    timeout: Optional[float] = Field(150, description=schema_field_description("timeout"))
    fail_soft: bool = Field(False, description=schema_field_description("fail_soft"))
    use_instruction_flow: bool = Field(
        False,
        description=schema_field_description("use_instruction_flow"),
    )
    cache_key: Optional[str] = Field(None, description=schema_field_description("cache_key"))


class BatchStructuredOutput(BaseModel):
    results: List[Dict[str, Any]] = Field(..., description=schema_field_description("results"))
    errors: List[Dict[str, Any]] = Field(..., description=schema_field_description("errors"))


@register_node
class BatchStructuredNode(BaseNode[BatchStructuredInput, BatchStructuredOutput]):
    node_type = "AI.BatchStructured"
    category = "ai"
    label = "Batch Structured Generation"
    description = "Generate structured data for items in batches"

    input_model = BatchStructuredInput
    output_model = BatchStructuredOutput

    async def execute(self, inputs: BatchStructuredInput) -> AsyncIterator[Union['ProgressEvent', BatchStructuredOutput]]:
        from ...engine.async_executor import ProgressEvent

        items = inputs.items
        if not isinstance(items, list):
            raise ValueError("Invalid batch structured input")

        if not items:
            yield BatchStructuredOutput(results=[], errors=[])
            return

        prompt_template = inputs.prompt_template
        if not prompt_template:
            raise ValueError("Invalid batch structured input")

        checkpoint = getattr(self.context, 'checkpoint', None)
        processed_indices = set(checkpoint.get('processed_indices', [])) if checkpoint else set()
        saved_results = checkpoint.get('partial_results', []) if checkpoint else []

        if processed_indices:
            logger.info(
                f"[BatchStructured] \u4ece\u68c0\u67e5\u70b9\u6062\u590d: "
                f"\u5df2\u5904\u7406 {len(processed_indices)}/{len(items)}"
            )

        results = [None] * len(items)
        errors = []
        total = len(items)

        for saved_result in saved_results:
            if isinstance(saved_result, dict) and 'meta' in saved_result:
                for i, item in enumerate(items):
                    if item == saved_result['meta']:
                        results[i] = saved_result
                        break

        pending_indices = [i for i in range(len(items)) if i not in processed_indices]

        if not pending_indices:
            yield BatchStructuredOutput(
                results=[r for r in results if r is not None],
                errors=errors
            )
            return

        logger.info(
            f"[BatchStructured] \u5f85\u5904\u7406 {len(pending_indices)} \u4e2a\u9879\u76ee "
            f"(\u5df2\u5b8c\u6210 {len(processed_indices)} \u4e2a, \u5e76\u53d1\u9650\u5236: {inputs.concurrency})"
        )

        schema = self._get_schema(self.context.session, inputs)
        if not schema:
            raise ValueError(f"\u65e0\u6cd5\u52a0\u8f7d\u6a21\u578b Schema: {inputs.response_model_id}")
        dynamic_output = build_model_from_json_schema(
            f"BatchStructured_{inputs.response_model_id}",
            schema,
        )

        progress_queue = asyncio.Queue()

        async def process_item(index):
            item = items[index]

            try:
                content = ""
                path = item.get("path")

                if path and os.path.exists(path):
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            content = f.read()
                    except Exception as e:
                        content = f"[\u8bfb\u53d6\u5931\u8d25: {e}]"

                if not content and "content" in item:
                    content = item["content"]

                current_prompt = prompt_template.replace("{{content}}", str(content))
                for k, v in item.items():
                    if k != "content":
                        current_prompt = current_prompt.replace(f"{{{{item.{k}}}}}", str(v))


                generated = await generate_structured(
                    session=self.context.session,
                    llm_config_id=inputs.llm_config_id,
                    user_prompt=current_prompt,
                    output_type=dynamic_output,
                    system_prompt=None,
                    deps="",
                    temperature=inputs.temperature,
                    max_tokens=inputs.max_tokens,
                    timeout=inputs.timeout or 150,
                    max_retries=inputs.max_retries,
                    use_instruction_flow=inputs.use_instruction_flow,
                    track_stats=True,
                    return_logs=True,
                )


                results[index] = {
                    "ai_result": generated["result"].model_dump(mode="json"),
                    "logs": generated["logs"],
                    "meta": item
                }

            except asyncio.CancelledError:
                raise
            except Exception as e:
                errors.append({"index": index, "item": item, "error": str(e)})
                results[index] = {"error": str(e), "meta": item}

            finally:
                processed_indices.add(index)
                await progress_queue.put(index)

        async def process_all_batches():
            batch_size = inputs.concurrency

            for batch_start in range(0, len(pending_indices), batch_size):
                batch_indices = pending_indices[batch_start:batch_start + batch_size]

                logger.info(
                    f"[BatchStructured] \u5904\u7406\u6279\u6b21 {batch_start//batch_size + 1}: "
                    f"\u7d22\u5f15 {batch_indices}"
                )

                await asyncio.gather(
                    *[process_item(i) for i in batch_indices],
                    return_exceptions=True
                )

                logger.info(
                    f"[BatchStructured] \u6279\u6b21 {batch_start//batch_size + 1} \u5b8c\u6210"
                )

        main_task = asyncio.create_task(process_all_batches())
        self.register_task(main_task)

        while not main_task.done():
            try:
                await asyncio.wait_for(progress_queue.get(), timeout=0.5)

                percent = (len(processed_indices) / total) * 100
                current_results = [r for r in results if r is not None]

                yield ProgressEvent(
                    percent=percent,
                    message=f"\u5df2\u5904\u7406 {len(processed_indices)}/{total} \u4e2a\u9879\u76ee",
                    data={
                        'processed_indices': list(processed_indices),
                        'partial_results': current_results
                    }
                )
            except asyncio.TimeoutError:
                continue

        await main_task

        logger.info(
            f"[BatchStructured] \u6279\u91cf\u5904\u7406\u5b8c\u6210: "
            f"{len([r for r in results if r is not None])} \u4e2a\u6210\u529f, {len(errors)} \u4e2a\u5931\u8d25"
        )

        yield BatchStructuredOutput(
            results=[r for r in results if r is not None],
            errors=errors
        )

    def _get_schema(self, session, inputs: BatchStructuredInput) -> Optional[Dict[str, Any]]:


        ct = get_card_type_by_identifier(session, inputs.response_model_id)
        if ct and ct.json_schema:
            return ct.json_schema

        builtin_model = RESPONSE_MODEL_MAP.get(inputs.response_model_id)
        if builtin_model is not None:
            return builtin_model.model_json_schema(ref_template="#/$defs/{model}")

        return None
