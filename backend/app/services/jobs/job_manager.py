"""Asynchronous background job manager with cancellation and concurrency control."""

import asyncio
import logging
from typing import Dict, Optional
from app.services.pipeline.pipeline import pipeline_runner

logger = logging.getLogger(__name__)


class JobManager:
    """Manages asynchronous pipeline job execution and life-cycle."""

    def __init__(self):
        self._running_tasks: Dict[str, asyncio.Task] = {}

    def start_job(self, job_id: str) -> None:
        """Launch job pipeline as a monitored background task."""
        if job_id in self._running_tasks and not self._running_tasks[job_id].done():
            logger.warning(f"Job {job_id} is already running.")
            return

        task = asyncio.create_task(self._execute_job(job_id))
        self._running_tasks[job_id] = task

    async def _execute_job(self, job_id: str) -> None:
        try:
            logger.info(f"Starting background worker task for job {job_id}")
            await pipeline_runner.run_pipeline(job_id)
        except asyncio.CancelledError:
            logger.warning(f"Job {job_id} task was cancelled.")
        except Exception as e:
            logger.error(f"Unhandled exception in background worker for job {job_id}: {e}")
        finally:
            self._running_tasks.pop(job_id, None)

    def cancel_job(self, job_id: str) -> bool:
        """Cancel an in-progress job."""
        if job_id in self._running_tasks:
            task = self._running_tasks[job_id]
            if not task.done():
                task.cancel()
                logger.info(f"Cancelled task for job {job_id}")
                return True
        return False

    def is_job_active(self, job_id: str) -> bool:
        """Check if job is currently running in background."""
        return job_id in self._running_tasks and not self._running_tasks[job_id].done()


job_manager = JobManager()
