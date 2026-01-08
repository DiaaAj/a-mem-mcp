"""Background task processing for async memory operations.

This module provides infrastructure for processing memory operations
asynchronously using asyncio, allowing the MCP server to return immediately
while memory processing (LLM calls, evolution, storage) happens in background.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime, UTC
import asyncio
import uuid
import logging
from collections import OrderedDict

logger = logging.getLogger(__name__)


@dataclass
class MemoryTask:
    """Represents a background memory operation.

    Attributes:
        task_id: Unique identifier for this task
        status: Current status (queued, processing, completed, failed)
        created_at: When task was created
        updated_at: When task was last updated
        content: Memory content to store
        kwargs: Additional arguments for add_note
        memory_id: ID of stored memory (available when completed)
        error: Error message (available when failed)
    """
    task_id: str
    status: str  # "queued" | "processing" | "completed" | "failed"
    created_at: datetime
    updated_at: datetime
    content: str
    kwargs: Dict[str, Any]
    memory_id: Optional[str] = None
    error: Optional[str] = None


class TaskTracker:
    """In-memory task tracking with automatic expiration.

    Manages background memory tasks with LRU eviction and automatic cleanup
    of old completed/failed tasks.
    """

    def __init__(self, max_tasks: int = 1000, retention_seconds: int = 3600):
        """Initialize task tracker.

        Args:
            max_tasks: Maximum tasks to keep (LRU eviction)
            retention_seconds: How long to keep completed tasks (1 hour default)
        """
        self._tasks: OrderedDict[str, MemoryTask] = OrderedDict()
        self._max_tasks = max_tasks
        self._retention_seconds = retention_seconds
        self._lock = asyncio.Lock()

    async def create_task(self, content: str, **kwargs) -> str:
        """Create new task and return task_id.

        Args:
            content: Memory content
            **kwargs: Additional arguments for add_note

        Returns:
            Unique task ID
        """
        task_id = str(uuid.uuid4())
        now = datetime.now(UTC)

        task = MemoryTask(
            task_id=task_id,
            status="queued",
            created_at=now,
            updated_at=now,
            content=content,
            kwargs=kwargs
        )

        async with self._lock:
            # LRU eviction
            if len(self._tasks) >= self._max_tasks:
                evicted_id, _ = self._tasks.popitem(last=False)
                logger.debug(f"Evicted task {evicted_id} due to max_tasks limit")
            self._tasks[task_id] = task

        logger.debug(f"Created task {task_id}")
        return task_id

    async def update_status(
        self,
        task_id: str,
        status: str,
        memory_id: Optional[str] = None,
        error: Optional[str] = None
    ):
        """Update task status atomically.

        Args:
            task_id: Task to update
            status: New status
            memory_id: Memory ID (for completed tasks)
            error: Error message (for failed tasks)
        """
        async with self._lock:
            if task_id in self._tasks:
                task = self._tasks[task_id]
                task.status = status
                task.updated_at = datetime.now(UTC)
                if memory_id:
                    task.memory_id = memory_id
                if error:
                    task.error = error
                # Move to end (most recent)
                self._tasks.move_to_end(task_id)
                logger.debug(f"Updated task {task_id} to status={status}")

    async def get_task(self, task_id: str) -> Optional[MemoryTask]:
        """Retrieve task status.

        Args:
            task_id: Task to retrieve

        Returns:
            MemoryTask if found, None otherwise
        """
        async with self._lock:
            return self._tasks.get(task_id)

    async def cleanup_old_tasks(self):
        """Background task to remove expired completed/failed tasks.

        Runs continuously every 5 minutes, removing tasks that have been
        completed/failed for longer than retention_seconds.
        """
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                async with self._lock:
                    now = datetime.now(UTC)
                    expired = [
                        tid for tid, task in self._tasks.items()
                        if task.status in ("completed", "failed") and
                        (now - task.updated_at).total_seconds() > self._retention_seconds
                    ]
                    for tid in expired:
                        del self._tasks[tid]
                    if expired:
                        logger.info(f"Cleaned up {len(expired)} expired tasks")
            except asyncio.CancelledError:
                logger.info("Task cleanup cancelled, shutting down")
                break
            except Exception as e:
                logger.error(f"Error in cleanup_old_tasks: {e}", exc_info=True)


# Global task tracker instance
task_tracker = TaskTracker()


async def process_memory_task(memory_system, task_id: str, content: str, **kwargs):
    """Background worker that processes a memory task.

    Args:
        memory_system: AgenticMemorySystem instance
        task_id: Task ID to update
        content: Memory content
        **kwargs: Additional arguments for add_note
    """
    try:
        # Update status to processing
        await task_tracker.update_status(task_id, "processing")
        logger.info(f"Processing task {task_id}")

        # Execute synchronous memory operation in thread pool
        memory_id = await asyncio.to_thread(
            memory_system.add_note,
            content,
            **kwargs
        )

        # Update status to completed
        await task_tracker.update_status(
            task_id,
            "completed",
            memory_id=memory_id
        )

        logger.info(f"Task {task_id} completed successfully, memory_id={memory_id}")

    except Exception as e:
        # Update status to failed with error message
        error_msg = str(e)
        await task_tracker.update_status(
            task_id,
            "failed",
            error=error_msg
        )
        logger.error(f"Task {task_id} failed: {error_msg}", exc_info=True)
