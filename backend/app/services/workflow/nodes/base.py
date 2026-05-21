
from typing import Any, Dict, Optional, List, Type, Union, AsyncIterator, Generic, TypeVar, TYPE_CHECKING
from sqlmodel import Session, select
from pydantic import BaseModel, Field
from typing_extensions import ClassVar
from abc import ABC, abstractmethod
import inspect
import asyncio

if TYPE_CHECKING:
    from ..engine.async_executor import ProgressEvent

from app.db.models import Card, CardType
from app.services.card_type_service_utils import get_card_type_by_identifier
from ..types import ExecutionContext, NodeMetadata


TInput = TypeVar('TInput', bound=BaseModel)
TOutput = TypeVar('TOutput', bound=BaseModel)


def get_card_by_id(session: Session, card_id: int) -> Optional[Card]:
    return session.get(Card, card_id)


def get_card_type_by_name(session: Session, type_name: str) -> Optional[CardType]:
    return get_card_type_by_identifier(session, type_name)


def resolve_card_reference(
    session: Session,
    reference: Any,
    context_card_id: Optional[int] = None
) -> Optional[Card]:
    if isinstance(reference, int):
        return get_card_by_id(session, reference)

    if isinstance(reference, str):
        if reference == "$self" and context_card_id:
            return get_card_by_id(session, context_card_id)
        elif reference == "$parent" and context_card_id:
            card = get_card_by_id(session, context_card_id)
            if card and card.parent_id:
                return get_card_by_id(session, card.parent_id)

    if isinstance(reference, dict):
        card_id = reference.get("id")
        if card_id:
            return get_card_by_id(session, card_id)

    return None


class BaseNode(ABC, Generic[TInput, TOutput]):




    node_type: ClassVar[str]
    category: ClassVar[str]
    label: ClassVar[str]
    description: ClassVar[str] = ""

    input_model: ClassVar[Type[TInput]]
    output_model: ClassVar[Type[TOutput]]

    @classmethod
    def get_output_schema_contract(
        cls,
        config: Dict[str, Any],
        session: Optional[Session] = None,
    ) -> Optional[Dict[str, Any]]:
        return None

    def __init__(self, context: ExecutionContext):
        self.context = context
        self._cleanup_tasks: List[Any] = []

    async def cleanup(self):
        if self._cleanup_tasks:
            from loguru import logger

            for task in self._cleanup_tasks:
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                    except Exception as e:


                        pass
            pass
            self._cleanup_tasks.clear()

    def register_task(self, task):
        self._cleanup_tasks.append(task)

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        input_schema = {}
        if hasattr(cls, 'input_model') and cls.input_model:
            input_schema = cls.input_model.model_json_schema()

        output_schema = {}
        if hasattr(cls, 'output_model') and cls.output_model:
            output_schema = cls.output_model.model_json_schema()

        return NodeMetadata(
            type=cls.node_type,
            category=cls.category,
            label=cls.label,
            description=cls.description,
            documentation=inspect.getdoc(cls) or "",
            input_schema=input_schema,
            output_schema=output_schema,
            executor=cls
        )

    @abstractmethod
    async def execute(self, inputs: TInput) -> AsyncIterator[Union['ProgressEvent', TOutput]]:
        raise NotImplementedError



class NoInputNode(BaseNode[BaseModel, TOutput]):




    class EmptyInput(BaseModel):
        pass

    input_model = EmptyInput

    async def execute(self, inputs: BaseModel) -> AsyncIterator[Union['ProgressEvent', TOutput]]:
        result = await self.execute_no_input()
        yield result

    @abstractmethod
    async def execute_no_input(self) -> TOutput:
        raise NotImplementedError


class NoOutputNode(BaseNode[TInput, BaseModel]):




    class EmptyOutput(BaseModel):
        pass

    output_model = EmptyOutput

    async def execute(self, inputs: TInput) -> AsyncIterator[Union['ProgressEvent', BaseModel]]:
        await self.execute_no_output(inputs)
        yield self.EmptyOutput()

    @abstractmethod
    async def execute_no_output(self, inputs: TInput) -> None:
        raise NotImplementedError
