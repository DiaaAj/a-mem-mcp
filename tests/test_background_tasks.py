"""Tests for background task infrastructure."""

import asyncio
import pytest
from datetime import datetime, timedelta, UTC
from agentic_memory_mcp.background import TaskTracker, process_memory_task, MemoryTask
from agentic_memory.memory_system import AgenticMemorySystem


@pytest.mark.asyncio
async def test_task_creation():
    """Test creating a task returns task_id and sets status to queued."""
    tracker = TaskTracker()

    task_id = await tracker.create_task("test content", keywords=["test"])
    assert task_id is not None
    assert isinstance(task_id, str)

    task = await tracker.get_task(task_id)
    assert task is not None
    assert task.status == "queued"
    assert task.content == "test content"
    assert task.kwargs["keywords"] == ["test"]


@pytest.mark.asyncio
async def test_task_status_update():
    """Test updating task status works correctly."""
    tracker = TaskTracker()

    task_id = await tracker.create_task("test content")

    # Update to processing
    await tracker.update_status(task_id, "processing")
    task = await tracker.get_task(task_id)
    assert task.status == "processing"

    # Update to completed with memory_id
    await tracker.update_status(task_id, "completed", memory_id="mem-123")
    task = await tracker.get_task(task_id)
    assert task.status == "completed"
    assert task.memory_id == "mem-123"

    # Update to failed with error
    task_id2 = await tracker.create_task("test 2")
    await tracker.update_status(task_id2, "failed", error="Test error")
    task2 = await tracker.get_task(task_id2)
    assert task2.status == "failed"
    assert task2.error == "Test error"


@pytest.mark.asyncio
async def test_task_not_found():
    """Test getting nonexistent task returns None."""
    tracker = TaskTracker()

    task = await tracker.get_task("nonexistent-id")
    assert task is None


@pytest.mark.asyncio
async def test_lru_eviction():
    """Test LRU eviction when max_tasks is reached."""
    tracker = TaskTracker(max_tasks=3)

    # Create 3 tasks (at capacity)
    ids = []
    for i in range(3):
        task_id = await tracker.create_task(f"content {i}")
        ids.append(task_id)

    # All should exist
    for task_id in ids:
        assert await tracker.get_task(task_id) is not None

    # Create 4th task - should evict oldest
    task_id4 = await tracker.create_task("content 4")

    # First task should be evicted
    assert await tracker.get_task(ids[0]) is None
    # Others should exist
    assert await tracker.get_task(ids[1]) is not None
    assert await tracker.get_task(ids[2]) is not None
    assert await tracker.get_task(task_id4) is not None


@pytest.mark.asyncio
async def test_process_memory_task_success():
    """Test successful memory task processing."""
    # Initialize memory system
    memory_system = AgenticMemorySystem(
        model_name='all-MiniLM-L6-v2',
        llm_backend="openai",
        llm_model="gpt-4o-mini",
        storage_path="./test_chroma_db"
    )

    # Use the global task_tracker from background module
    from agentic_memory_mcp.background import task_tracker
    task_id = await task_tracker.create_task("Important test memory", keywords=["test", "async"])

    # Process task
    await process_memory_task(
        memory_system,
        task_id,
        "Important test memory",
        keywords=["test", "async"]
    )

    # Verify task completed
    task = await task_tracker.get_task(task_id)
    assert task.status == "completed"
    assert task.memory_id is not None

    # Verify memory was actually stored
    memory_id = task.memory_id
    note = memory_system.read(memory_id)
    assert note is not None
    assert note.content == "Important test memory"
    assert "test" in note.keywords
    assert "async" in note.keywords

    # Cleanup
    memory_system.delete(memory_id)


@pytest.mark.asyncio
async def test_process_memory_task_graceful_degradation():
    """Test task processing handles LLM errors gracefully with defaults."""
    # Create memory system with invalid model (will use defaults on error)
    memory_system = AgenticMemorySystem(
        model_name='all-MiniLM-L6-v2',
        llm_backend="openai",
        llm_model="invalid-model-name",
        storage_path="./test_chroma_db"
    )

    # Use the global task_tracker from background module
    from agentic_memory_mcp.background import task_tracker
    task_id = await task_tracker.create_task("Test content")

    # Process task (LLM will fail but system should gracefully degrade)
    await process_memory_task(
        memory_system,
        task_id,
        "Test content"
    )

    # Verify task completed with graceful degradation
    task = await task_tracker.get_task(task_id)
    assert task.status == "completed"  # System handles errors gracefully
    assert task.memory_id is not None  # Memory still gets stored

    # Verify memory was stored with default values
    memory_id = task.memory_id
    note = memory_system.read(memory_id)
    assert note is not None
    assert note.content == "Test content"

    # Cleanup
    memory_system.delete(memory_id)


@pytest.mark.asyncio
async def test_cleanup_old_tasks():
    """Test automatic cleanup of old completed/failed tasks."""
    # Use very short retention for testing
    tracker = TaskTracker(retention_seconds=1)

    # Create completed task
    task_id1 = await tracker.create_task("content 1")
    await tracker.update_status(task_id1, "completed", memory_id="mem-1")

    # Create failed task
    task_id2 = await tracker.create_task("content 2")
    await tracker.update_status(task_id2, "failed", error="test error")

    # Create queued task
    task_id3 = await tracker.create_task("content 3")

    # All should exist initially
    assert await tracker.get_task(task_id1) is not None
    assert await tracker.get_task(task_id2) is not None
    assert await tracker.get_task(task_id3) is not None

    # Wait for retention period to expire
    await asyncio.sleep(1.5)

    # Manually trigger cleanup (since background task runs every 5 min)
    now = datetime.now(UTC)
    async with tracker._lock:
        expired = [
            tid for tid, task in tracker._tasks.items()
            if task.status in ("completed", "failed") and
            (now - task.updated_at).total_seconds() > tracker._retention_seconds
        ]
        for tid in expired:
            del tracker._tasks[tid]

    # Completed and failed tasks should be cleaned up
    assert await tracker.get_task(task_id1) is None
    assert await tracker.get_task(task_id2) is None

    # Queued task should remain
    assert await tracker.get_task(task_id3) is not None


@pytest.mark.asyncio
async def test_concurrent_task_operations():
    """Test concurrent task creation and updates."""
    tracker = TaskTracker(max_tasks=100)

    async def worker(worker_id):
        """Create and process tasks."""
        for i in range(5):
            task_id = await tracker.create_task(f"Worker {worker_id} task {i}")
            await tracker.update_status(task_id, "processing")
            await asyncio.sleep(0.01)  # Simulate work
            await tracker.update_status(task_id, "completed", memory_id=f"mem-{worker_id}-{i}")

    # Run 10 workers concurrently
    await asyncio.gather(*[worker(i) for i in range(10)])

    # Should have 50 completed tasks
    stats_size = len(tracker._tasks)
    assert stats_size == 50


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
