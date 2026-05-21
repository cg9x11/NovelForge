
import asyncio
from typing import Dict, Optional
from loguru import logger

from app.db.models import WorkflowRun


class WorkflowScheduler:


    def __init__(self, max_concurrent_runs: int = 5):
        self.max_concurrent_runs = max_concurrent_runs
        self.running_runs: Dict[int, asyncio.Task] = {}  # run_id -> task
        self.pending_queue: asyncio.Queue = asyncio.Queue()  # (priority, run_id)

    async def schedule_run(
        self,
        run_id: int,
        executor_coro,
        priority: int = 0
    ) -> None:
        if len(self.running_runs) < self.max_concurrent_runs:
            await self._start_run(run_id, executor_coro)
        else:
            logger.info(
                f"[Scheduler] \u8fd0\u884c\u52a0\u5165\u7b49\u5f85\u961f\u5217: run_id={run_id}, "
                f"priority={priority}"
            )
            await self.pending_queue.put((priority, run_id, executor_coro))

    async def _start_run(self, run_id: int, executor_coro) -> None:

        task = asyncio.create_task(self._run_with_cleanup(run_id, executor_coro))
        self.running_runs[run_id] = task

    async def _run_with_cleanup(self, run_id: int, executor_coro) -> None:
        try:
            await executor_coro
        finally:
            if run_id in self.running_runs:
                del self.running_runs[run_id]

            logger.info(
                f"[Scheduler] \u8fd0\u884c\u5b8c\u6210: run_id={run_id}, "
                f"\u5f53\u524d\u8fd0\u884c\u6570={len(self.running_runs)}"
            )

            await self._start_next_from_queue()

    async def _start_next_from_queue(self) -> None:
        if self.pending_queue.empty():
            return

        if len(self.running_runs) >= self.max_concurrent_runs:
            return

        priority, run_id, executor_coro = await self.pending_queue.get()
        logger.info(
            f"[Scheduler] \u4ece\u961f\u5217\u542f\u52a8\u8fd0\u884c: run_id={run_id}, priority={priority}"
        )
        await self._start_run(run_id, executor_coro)

    def cancel_run(self, run_id: int) -> bool:
        if run_id in self.running_runs:
            task = self.running_runs[run_id]
            task.cancel()
            return True
        return False

    def get_running_count(self) -> int:
        return len(self.running_runs)

    def get_pending_count(self) -> int:
        return self.pending_queue.qsize()

    def is_running(self, run_id: int) -> bool:
        return run_id in self.running_runs
