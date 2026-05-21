
from app.locales import schema_field_description
from typing import Any, Dict, List, Optional, AsyncIterator
from pydantic import BaseModel, Field
from loguru import logger

from ...registry import register_node
from ..base import BaseNode
from app.services.context_service import assemble_context, ContextAssembleParams


class ContextAssembleInput(BaseModel):


    project_id: int = Field(..., description=schema_field_description("project_id"))
    participants: List[str] = Field(
        default_factory=list,
        description=schema_field_description("participants")
    )


class ContextAssembleOutput(BaseModel):


    context_text: str = Field(..., description=schema_field_description("context_text"))
    context_data: Dict[str, Any] = Field(default_factory=dict, description=schema_field_description("context_data"))


# @register_node
class ContextAssembleNode(BaseNode):


    node_type = "Context.Assemble"
    category = "context"
    label = "Assemble Context"
    description = "Assemble context for AI prompts"
    input_model = ContextAssembleInput
    output_model = ContextAssembleOutput

    async def execute(self, input_data: ContextAssembleInput) -> AsyncIterator[ContextAssembleOutput]:

        project_id = input_data.project_id

        params = ContextAssembleParams(
            project_id=project_id,
            participants=input_data.participants,
            volume_number=None,
            chapter_number=None,
            current_draft_tail=None,
        )

        result = assemble_context(self.context.session, params)

        logger.info(
            f"[Context.Assemble] \u7ec4\u88c5\u4e0a\u4e0b\u6587\u6210\u529f: project_id={project_id}, "
            f"participants={input_data.participants}"
        )

        yield ContextAssembleOutput(
            context_text=result.facts_subgraph,
            context_data=result.facts_structured or {},
        )
