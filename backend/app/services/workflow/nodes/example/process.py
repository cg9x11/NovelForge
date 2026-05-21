
from app.locales import schema_field_description
from typing import List, Dict, Any, AsyncIterator, Union, TYPE_CHECKING
from pydantic import BaseModel, Field
from loguru import logger
import asyncio

if TYPE_CHECKING:
    from ...engine.async_executor import ProgressEvent

from ..base import BaseNode
from ...registry import register_node



class ExampleProcessInput(BaseModel):
    items: List[str] = Field(..., description=schema_field_description("items"))
    delay: float = Field(0.5, description=schema_field_description("delay"), ge=0.0, le=10.0)
    enable_progress: bool = Field(True, description=schema_field_description("enable_progress"))


class ExampleProcessOutput(BaseModel):
    results: List[Dict[str, Any]] = Field(..., description=schema_field_description("results"))
    summary: Dict[str, Any] = Field(..., description=schema_field_description("summary"))


@register_node
class ExampleProcessNode(BaseNode[ExampleProcessInput, ExampleProcessOutput]):




    node_type = "Example.Process"
    category = "example"
    label = "Example Process"
    description = "Process example items and report progress"

    input_model = ExampleProcessInput
    output_model = ExampleProcessOutput

    async def execute(self, inputs: ExampleProcessInput) -> AsyncIterator[Union['ProgressEvent', ExampleProcessOutput]]:
        from ...engine.async_executor import ProgressEvent


        checkpoint = getattr(self.context, 'checkpoint', None)
        start_index = checkpoint.get('processed_count', 0) if checkpoint else 0

        if start_index > 0:


            pass
        pass
        results = []
        total = len(inputs.items)

        for i in range(start_index, total):
            item = inputs.items[i]

            await asyncio.sleep(inputs.delay)
            result = {"item": item, "processed": True, "index": i}
            results.append(result)

            if inputs.enable_progress:
                percent = ((i + 1) / total) * 100
                yield ProgressEvent(
                    percent=percent,
                    message=f"\u6b63\u5728\u5904\u7406: {item} ({i+1}/{total})",
                    data={
                        'processed_count': i + 1,
                        'last_item': item
                    }
                )

        summary = {
            "total": len(inputs.items),
            "processed": len(results),
            "success_rate": 1.0
        }


        yield ExampleProcessOutput(
            results=results,
            summary=summary
        )

class BatchProcessInput(BaseModel):
    data: List[Any] = Field(..., description=schema_field_description("data"))
    batch_size: int = Field(10, description=schema_field_description("batch_size"), ge=1, le=100)
    parallel: bool = Field(False, description=schema_field_description("parallel"))


class BatchProcessOutput(BaseModel):
    results: List[Dict[str, Any]] = Field(..., description=schema_field_description("results"))
    total_processed: int = Field(..., description=schema_field_description("total_processed"))


@register_node
class BatchProcessNode(BaseNode[BatchProcessInput, BatchProcessOutput]):




    node_type = "Example.BatchProcess"
    category = "example"
    label = "Batch Process"
    description = "Process data in batches with optional parallelism"

    input_model = BatchProcessInput
    output_model = BatchProcessOutput

    async def execute(self, inputs: BatchProcessInput) -> AsyncIterator[BatchProcessOutput]:

        results = []

        for i in range(0, len(inputs.data), inputs.batch_size):
            batch = inputs.data[i:i + inputs.batch_size]

            if inputs.parallel:
                tasks = [self._process_item(item) for item in batch]
                batch_results = await asyncio.gather(*tasks)
            else:
                batch_results = []
                for item in batch:
                    result = await self._process_item(item)
                    batch_results.append(result)

            results.extend(batch_results)


        yield BatchProcessOutput(
            results=results,
            total_processed=len(results)
        )

    async def _process_item(self, item: Any) -> Dict[str, Any]:
        await asyncio.sleep(0.1)
        return {"item": item, "processed": True}
