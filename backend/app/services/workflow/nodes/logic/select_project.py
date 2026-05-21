from app.locales import schema_field_description
from typing import Any, AsyncIterator, Dict

from loguru import logger
from pydantic import BaseModel, Field
from sqlmodel import select

from app.db.models import Project
from ...registry import register_node
from ..base import BaseNode


class SelectProjectInput(BaseModel):


    project_id: int | None = Field(
        default=None,
        description=schema_field_description("project_id"),
        json_schema_extra={"x-component": "ProjectSelect"},
    )
    project_name: str | None = Field(
        default=None,
        description=schema_field_description("project_name"),
        json_schema_extra={"x-component": "ProjectSelect"},
    )


class SelectProjectOutput(BaseModel):


    project_id: int = Field(..., description=schema_field_description("project_id"))
    project: Dict[str, Any] = Field(..., description=schema_field_description("project"))


@register_node
class SelectProjectNode(BaseNode[SelectProjectInput, SelectProjectOutput]):
    node_type = "Logic.SelectProject"
    category = "logic"
    label = "Select Project"
    description = "Select a project for downstream workflow nodes"

    input_model = SelectProjectInput
    output_model = SelectProjectOutput

    async def execute(self, inputs: SelectProjectInput) -> AsyncIterator[SelectProjectOutput]:
        session = self.context.session

        project = None
        if inputs.project_id is not None:
            project = session.get(Project, inputs.project_id)

        if project is None and inputs.project_name:
            project = session.exec(
                select(Project).where(Project.name == inputs.project_name)
            ).first()
            if project is None:
                candidates = session.exec(select(Project)).all()
                lowered = inputs.project_name.lower()
                matches = [
                    item
                    for item in candidates
                    if lowered in (item.name or "").lower()
                ]
                if len(matches) == 1:
                    project = matches[0]
                elif len(matches) > 1:
                    raise ValueError(
                        f"\u9879\u76ee\u540d\u5339\u914d\u5230\u591a\u4e2a\u5019\u9009: {inputs.project_name}"
                    )

        if not project:
            raise ValueError(
                f"\u9879\u76ee\u4e0d\u5b58\u5728: id={inputs.project_id}, name={inputs.project_name}"
            )


        yield SelectProjectOutput(
            project_id=project.id,
            project={
                "id": project.id,
                "name": project.name,
                "description": project.description,
            },
        )
