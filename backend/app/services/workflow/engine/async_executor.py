
import asyncio
from typing import Dict, Any, List, Optional, AsyncIterator, TYPE_CHECKING
from dataclasses import dataclass
from datetime import datetime
from loguru import logger
from sqlmodel import Session

from .execution_plan import ExecutionPlan, Statement
from .execution_state import ExecutionState, CheckpointData
from .error_handler import ErrorHandler
from ..registry import get_registered_nodes
from ..expressions.evaluator import evaluate_expression

if TYPE_CHECKING:
    from .state_manager import StateManager


@dataclass
class ProgressEvent:
    percent: float = 0.0  # 0-100
    message: str = ""
    data: Optional[Dict[str, Any]] = None

    statement: Optional[Statement] = None
    type: Optional[str] = None  # 'start', 'progress', 'complete', 'error', 'workflow_complete'
    result: Optional[Any] = None
    error: Optional[str] = None


class AsyncExecutor:




    def __init__(self, session: Session, state_manager: Optional['StateManager'] = None, run_id: int = 0):
        self.session = session
        self.state_manager = state_manager
        self.run_id = run_id
        self.execution_state = ExecutionState(run_id)
        self.node_registry = get_registered_nodes()
        self.async_tasks: Dict[str, asyncio.Task] = {}
        self.node_instances: Dict[str, Any] = {}
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.pending_async_tasks: int = 0
        self.pause_event = asyncio.Event()
        self.pause_event.set()
        self.is_paused = False

    @property
    def context(self) -> Dict[str, Any]:
        return self.execution_state.context

    @property
    def completed_statements(self) -> set:
        return self.execution_state.completed_nodes

    async def execute_stream(
        self,
        plan: ExecutionPlan,
        initial_context: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[ProgressEvent]:
        is_resuming = False
        if self.run_id:
            self.execution_state = ExecutionState.load(self.run_id, self.session)

            if self.execution_state.completed_nodes:
                is_resuming = True
                logger.info(
                    f"[AsyncExecutor] \u68c0\u6d4b\u5230\u6062\u590d\u6267\u884c: run_id={self.run_id}, "
                    f"\u5df2\u5b8c\u6210={len(self.execution_state.completed_nodes)}\u4e2a\u8282\u70b9"
                )
            else:
                self.execution_state.context = initial_context or {}
        else:
            self.execution_state.context = initial_context or {}

        if is_resuming:
            for node_id in self.execution_state.completed_nodes:
                node_state = self.execution_state.get_node_state(node_id)
                if node_state and node_state.status == "success":
                    stmt = next((s for s in plan.statements if s.variable == node_id), None)
                    if stmt:
                        await self.event_queue.put(ProgressEvent(
                            statement=stmt,
                            type='complete',
                            result=node_state.outputs,
                            message=f"[\u5df2\u6062\u590d] {node_id}"
                        ))


        consumer_task = asyncio.create_task(self._process_statements(plan))

        try:
            while True:
                event = await self.event_queue.get()

                if event is None:
                    break

                yield event

        finally:
            try:
                await consumer_task
            except Exception as e:
                raise

    async def _process_statements(self, plan: ExecutionPlan):
        try:
            for stmt in plan.statements:
                if self.execution_state.is_completed(stmt.variable):
                    continue

                if self.is_paused:
                    break

                await self.pause_event.wait()


                if stmt.disabled:




                    await self.event_queue.put(ProgressEvent(
                        statement=stmt,
                        type='skipped',
                        message=f"\u8282\u70b9\u5df2\u7981\u7528，\u8df3\u8fc7\u6267\u884c: {stmt.variable}"
                    ))

                    self.execution_state.context[stmt.variable] = None
                    self.execution_state.completed_nodes.add(stmt.variable)
                    continue

                await self.event_queue.put(ProgressEvent(
                    statement=stmt,
                    type='start',
                    message=f"\u5f00\u59cb\u6267\u884c: {stmt.variable}"
                ))

                try:
                    if stmt.is_async:
                        self.pending_async_tasks += 1

                        task = asyncio.create_task(
                            self._execute_async_node_to_queue(stmt),
                            name=f"async_node_{stmt.variable}"
                        )
                        self.async_tasks[stmt.variable] = task

                    elif stmt.node_type == "Logic.Wait" or stmt.node_type == "_wait":
                        wait_for = stmt.config.get("tasks") or stmt.config.get("wait_for", [])

                        if isinstance(wait_for, str):
                            wait_for = [v.strip() for v in wait_for.split(",") if v.strip()]
                        elif not isinstance(wait_for, list):
                            wait_for = [wait_for] if wait_for else []

                        wait_for = [v.lstrip('$') if isinstance(v, str) else v for v in wait_for]


                        for var in wait_for:
                            if var in self.async_tasks:
                                await self.async_tasks[var]
                                del self.async_tasks[var]
                            elif var in self.execution_state.context:
                                pass
                            else:
                                raise ValueError(f"\u7b49\u5f85\u7684\u53d8\u91cf\u4e0d\u5b58\u5728: {var}")

                        self.execution_state.context[stmt.variable] = {
                            'waited_tasks': wait_for,
                            'count': len(wait_for)
                        }

                        await self.event_queue.put(ProgressEvent(
                            statement=stmt,
                            type='complete',
                            result=self.execution_state.context[stmt.variable]
                        ))

                        self.execution_state.completed_nodes.add(stmt.variable)

                    elif stmt.node_type is None:
                        result = self._execute_expression(stmt)
                        self.execution_state.context[stmt.variable] = result

                        self.execution_state.update_node_state(
                            node_id=stmt.variable,
                            node_type="expression",
                            status="success",
                            progress=100.0,
                            outputs=result
                        )
                        self.execution_state.save(self.session)

                        await self.event_queue.put(ProgressEvent(
                            statement=stmt,
                            type='complete',
                            result=result
                        ))

                    else:
                        async for event in self._execute_node_stream(stmt):
                            await self.event_queue.put(event)

                    self.execution_state.completed_nodes.add(stmt.variable)

                except Exception as e:
                    error_event = await ErrorHandler.handle_node_error(
                        e, stmt, self.execution_state, self.session
                    )
                    await self.event_queue.put(error_event)
                    raise

            if self.async_tasks:
                for var, task in list(self.async_tasks.items()):
                    await task
                    del self.async_tasks[var]


            await self.event_queue.put(ProgressEvent(
                statement=plan.statements[-1] if plan.statements else Statement(line_number=0, variable="", node_type=None, config={}, depends_on=[]),
                type='workflow_complete',
                message="Completed"
            ))

        finally:
            await self.event_queue.put(None)

    async def _execute_async_node_to_queue(self, stmt: Statement):
        try:
            async for event in self._execute_node_stream(stmt):
                await self.event_queue.put(event)
        except asyncio.CancelledError:
            await ErrorHandler.handle_cancellation(
                stmt, self.execution_state, self.session
            )
            raise
        except Exception as e:
            error_event = await ErrorHandler.handle_node_error(
                e, stmt, self.execution_state, self.session
            )
            await self.event_queue.put(error_event)
            raise
        finally:
            self.pending_async_tasks -= 1

    async def _execute_node_stream(self, stmt: Statement) -> AsyncIterator[ProgressEvent]:
        node_type = stmt.node_type

        executor_fn = self.node_registry.get(node_type)
        if not executor_fn:
            raise ValueError(f"\u672a\u6ce8\u518c\u7684\u8282\u70b9\u7c7b\u578b: {node_type}")

        config = self._resolve_config(stmt.config)

        inputs = self._resolve_inputs(config)

        self.execution_state.update_node_state(
            node_id=stmt.variable,
            node_type=node_type,
            status="running",
            progress=0.0
        )

        checkpoint_data = self.execution_state.get_checkpoint(stmt.variable)
        checkpoint = checkpoint_data.data if checkpoint_data else None

        if checkpoint:
            logger.info(
                f"[Checkpoint] \u6062\u590d\u8282\u70b9 {stmt.variable}: "
                f"\u8fdb\u5ea6={checkpoint_data.percent}%, "
                f"\u6570\u636e={checkpoint}"
            )

        import inspect
        if inspect.isclass(executor_fn):
            from ..types import ExecutionContext, WorkflowSettings

            context = ExecutionContext(
                run_id=self.run_id or 0,
                node_id=stmt.variable,
                node_type=node_type,
                config=config,
                inputs=inputs,
                variables=self.execution_state.context,
                node_outputs={},
                settings=WorkflowSettings(),
                session=self.session,
                checkpoint=checkpoint
            )

            node = executor_fn(context)

            self.node_instances[stmt.variable] = node

            if hasattr(executor_fn, 'input_model') and executor_fn.input_model:
                input_data = {**config, **inputs}
                input_instance = executor_fn.input_model(**input_data)
            else:
                raise ValueError(f"\u8282\u70b9 {node_type} \u7f3a\u5c11 input_model \u5b9a\u4e49")

            result = None
            async for event in node.execute(input_instance):
                if isinstance(event, ProgressEvent):
                    checkpoint_data = CheckpointData(
                        percent=event.percent,
                        message=event.message,
                        data=event.data,
                        timestamp=datetime.utcnow()
                    )

                    self.execution_state.update_node_state(
                        node_id=stmt.variable,
                        node_type=node_type,
                        status="running",
                        progress=event.percent,
                        checkpoint=checkpoint_data
                    )
                    self.execution_state.save(self.session)

                    yield ProgressEvent(
                        statement=stmt,
                        type='progress',
                        percent=event.percent,
                        message=event.message
                    )
                else:
                    result = event

            if result is None:
                raise ValueError(f"\u8282\u70b9 {node_type} \u6ca1\u6709\u8fd4\u56de\u7ed3\u679c")

            if hasattr(result, 'model_dump'):
                final_result = result.model_dump()
            elif hasattr(result, 'dict'):
                final_result = result.dict()
            else:
                final_result = result

            self.execution_state.context[stmt.variable] = final_result

            self.execution_state.update_node_state(
                node_id=stmt.variable,
                node_type=node_type,
                status="success",
                progress=100.0,
                outputs=final_result,
                checkpoint=CheckpointData(
                    percent=100.0,
                    message="Completed",
                    data={'completed': True},
                    timestamp=datetime.utcnow()
                )
            )
            self.execution_state.save(self.session)

            yield ProgressEvent(
                statement=stmt,
                type='complete',
                result=final_result
            )

        elif inspect.iscoroutinefunction(executor_fn):
            result = await executor_fn(**inputs)
            self.execution_state.context[stmt.variable] = result

            self.execution_state.update_node_state(
                node_id=stmt.variable,
                node_type=node_type or "async_function",
                status="success",
                progress=100.0,
                outputs=result
            )
            self.execution_state.save(self.session)

            yield ProgressEvent(
                statement=stmt,
                type='complete',
                result=result
            )
        else:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, lambda: executor_fn(**inputs))
            self.execution_state.context[stmt.variable] = result

            self.execution_state.update_node_state(
                node_id=stmt.variable,
                node_type=node_type or "sync_function",
                status="success",
                progress=100.0,
                outputs=result
            )
            self.execution_state.save(self.session)

            yield ProgressEvent(
                statement=stmt,
                type='complete',
                result=result
            )

    def _execute_expression(self, stmt: Statement) -> Any:
        expression = stmt.config.get("expression", "")

        context = self._resolve_context(stmt.depends_on)
        return evaluate_expression(expression, context)

    def _resolve_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        resolved = {}
        for key, value in config.items():
            resolved[key] = self._resolve_value(value)
        return resolved

    def _resolve_value(self, value: Any) -> Any:
        if isinstance(value, str):
            if value.startswith("${") and value.endswith("}"):
                expression = value[2:-1]
                return evaluate_expression(expression, self.execution_state.context)
            elif value.startswith("$"):
                ref = value[1:]
                return self._resolve_variable_reference(ref)
            else:
                return value
        elif isinstance(value, list):
            return [self._resolve_value(item) for item in value]
        elif isinstance(value, dict):
            return {k: self._resolve_value(v) for k, v in value.items()}
        else:
            return value

    def _resolve_variable_reference(self, ref: str) -> Any:
        parts = ref.split(".")
        value = self.execution_state.context.get(parts[0])

        if value is None:
            raise ValueError(f"\u53d8\u91cf\u4e0d\u5b58\u5728: {parts[0]}")

        for part in parts[1:]:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                value = getattr(value, part, None)

            if value is None:
                raise ValueError(f"\u5c5e\u6027\u4e0d\u5b58\u5728: {ref}")

        return value

    def _resolve_inputs(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return config

    def _resolve_context(self, depends_on: List[str]) -> Dict[str, Any]:
        context = {}
        for var in depends_on:
            if var in self.execution_state.context:
                context[var] = self.execution_state.context[var]
        return context

    def pause(self):
        self.is_paused = True
        self.pause_event.clear()

        if self.node_instances:
            for var, node in list(self.node_instances.items()):
                try:
                    asyncio.create_task(node.cleanup())
                except Exception as e:


                    pass
        if self.async_tasks:
            for var, task in list(self.async_tasks.items()):
                if not task.done():
                    task.cancel()


    def resume(self):
        self.is_paused = False
        self.pause_event.set()

    def is_paused(self) -> bool:
        return not self.pause_event.is_set()
