"""Integration tests for async memory operations."""

import asyncio
import pytest
import time
from agentic_memory.memory_system import AgenticMemorySystem
from agentic_memory_mcp.background import task_tracker, process_memory_task


@pytest.mark.asyncio
async def test_async_response_time():
    """Test that async add returns immediately (<10ms)."""
    memory_system = AgenticMemorySystem(
        model_name='all-MiniLM-L6-v2',
        llm_backend="openai",
        llm_model="gpt-4o-mini",
        storage_path="./test_chroma_db"
    )

    # Measure response time
    start = time.perf_counter()

    # Create task (should return immediately)
    task_id = await task_tracker.create_task(
        "Async response time test",
        keywords=["performance", "test"]
    )

    # Schedule background processing (fire-and-forget)
    asyncio.create_task(
        process_memory_task(
            memory_system,
            task_id,
            "Async response time test",
            keywords=["performance", "test"]
        )
    )

    elapsed_ms = (time.perf_counter() - start) * 1000

    print(f"Async response time: {elapsed_ms:.2f}ms")
    assert elapsed_ms < 10, f"Response time {elapsed_ms}ms exceeds 10ms threshold"

    # Wait for background processing to complete
    await asyncio.sleep(2)

    # Verify task completed
    task = await task_tracker.get_task(task_id)
    assert task.status == "completed"
    assert task.memory_id is not None

    # Cleanup
    memory_system.delete(task.memory_id)


@pytest.mark.asyncio
async def test_concurrent_memory_additions():
    """Test adding 50 memories concurrently."""
    memory_system = AgenticMemorySystem(
        model_name='all-MiniLM-L6-v2',
        llm_backend="openai",
        llm_model="gpt-4o-mini",
        storage_path="./test_chroma_db"
    )

    async def add_memory(i):
        """Add a single memory and return task_id."""
        task_id = await task_tracker.create_task(
            f"Concurrent test memory {i}",
            keywords=[f"test{i}", "concurrent"]
        )

        # Schedule background processing
        asyncio.create_task(
            process_memory_task(
                memory_system,
                task_id,
                f"Concurrent test memory {i}",
                keywords=[f"test{i}", "concurrent"]
            )
        )

        return task_id

    # Execute 50 concurrent additions
    print("Adding 50 memories concurrently...")
    start = time.perf_counter()
    task_ids = await asyncio.gather(*[add_memory(i) for i in range(50)])
    response_time = time.perf_counter() - start

    print(f"Total response time for 50 additions: {response_time*1000:.2f}ms")
    print(f"Average per addition: {response_time*1000/50:.2f}ms")

    # Response should be fast (all should queue in < 1 second)
    assert response_time < 1.0, "Queueing 50 tasks took too long"

    # Wait for all background processing to complete
    print("Waiting for background processing...")
    await asyncio.sleep(10)  # Give enough time for LLM calls

    # Verify all tasks completed
    completed = 0
    failed = 0
    memory_ids = []

    for task_id in task_ids:
        task = await task_tracker.get_task(task_id)
        if task.status == "completed":
            completed += 1
            memory_ids.append(task.memory_id)
        elif task.status == "failed":
            failed += 1
            print(f"Task {task_id} failed: {task.error}")

    print(f"Results: {completed} completed, {failed} failed")
    assert completed >= 45, f"Too many failures: only {completed}/50 completed"

    # Cleanup
    for memory_id in memory_ids:
        memory_system.delete(memory_id)


@pytest.mark.asyncio
async def test_status_polling():
    """Test polling task status until completion."""
    memory_system = AgenticMemorySystem(
        model_name='all-MiniLM-L6-v2',
        llm_backend="openai",
        llm_model="gpt-4o-mini",
        storage_path="./test_chroma_db"
    )

    # Create and schedule task
    task_id = await task_tracker.create_task(
        "Status polling test",
        keywords=["polling", "test"]
    )

    asyncio.create_task(
        process_memory_task(
            memory_system,
            task_id,
            "Status polling test",
            keywords=["polling", "test"]
        )
    )

    # Poll status until completed
    poll_count = 0
    max_polls = 100  # Max 10 seconds (100 * 0.1s)

    while poll_count < max_polls:
        task = await task_tracker.get_task(task_id)
        print(f"Poll {poll_count}: status={task.status}")

        if task.status == "completed":
            assert task.memory_id is not None
            print(f"Completed after {poll_count} polls, memory_id={task.memory_id}")

            # Cleanup
            memory_system.delete(task.memory_id)
            return

        elif task.status == "failed":
            pytest.fail(f"Task failed: {task.error}")

        await asyncio.sleep(0.1)
        poll_count += 1

    pytest.fail(f"Task did not complete within {max_polls * 0.1}s")


@pytest.mark.asyncio
async def test_fire_and_forget_pattern():
    """Test typical fire-and-forget usage pattern."""
    memory_system = AgenticMemorySystem(
        model_name='all-MiniLM-L6-v2',
        llm_backend="openai",
        llm_model="gpt-4o-mini",
        storage_path="./test_chroma_db"
    )

    task_ids = []

    # Add 10 memories without waiting
    for i in range(10):
        task_id = await task_tracker.create_task(
            f"Fire and forget memory {i}",
            keywords=["fire-forget", f"num{i}"]
        )

        asyncio.create_task(
            process_memory_task(
                memory_system,
                task_id,
                f"Fire and forget memory {i}",
                keywords=["fire-forget", f"num{i}"]
            )
        )

        task_ids.append(task_id)

    # Immediately proceed without waiting
    print("All tasks queued, continuing without waiting...")

    # Do other work (simulate)
    await asyncio.sleep(0.5)

    # Later, we can check if they completed
    await asyncio.sleep(5)

    completed = sum(
        1 for tid in task_ids
        if (task := await task_tracker.get_task(tid)) and task.status == "completed"
    )

    print(f"{completed}/10 tasks completed")
    assert completed >= 8, "Most tasks should complete"

    # Cleanup
    for tid in task_ids:
        task = await task_tracker.get_task(tid)
        if task and task.memory_id:
            memory_system.delete(task.memory_id)


@pytest.mark.asyncio
async def test_performance_comparison():
    """Compare sync vs async performance."""
    memory_system = AgenticMemorySystem(
        model_name='all-MiniLM-L6-v2',
        llm_backend="openai",
        llm_model="gpt-4o-mini",
        storage_path="./test_chroma_db"
    )

    # Measure synchronous (old way)
    print("\n=== Synchronous (old way) ===")
    start = time.perf_counter()
    sync_ids = []
    for i in range(3):
        memory_id = memory_system.add_note(
            f"Sync memory {i}",
            keywords=["sync", f"num{i}"]
        )
        sync_ids.append(memory_id)
    sync_time = time.perf_counter() - start
    print(f"3 synchronous adds: {sync_time:.2f}s ({sync_time/3:.2f}s avg)")

    # Measure asynchronous (new way)
    print("\n=== Asynchronous (new way) ===")
    start = time.perf_counter()
    async_task_ids = []
    for i in range(3):
        task_id = await task_tracker.create_task(
            f"Async memory {i}",
            keywords=["async", f"num{i}"]
        )
        asyncio.create_task(
            process_memory_task(
                memory_system,
                task_id,
                f"Async memory {i}",
                keywords=["async", f"num{i}"]
            )
        )
        async_task_ids.append(task_id)
    async_queue_time = time.perf_counter() - start
    print(f"3 asynchronous queues: {async_queue_time:.2f}s ({async_queue_time/3:.2f}s avg)")

    # Wait for async to complete
    await asyncio.sleep(10)

    print(f"\nSpeedup: {sync_time/async_queue_time:.1f}x faster queueing")
    assert async_queue_time < sync_time / 10, "Async should be much faster"

    # Cleanup
    for memory_id in sync_ids:
        memory_system.delete(memory_id)

    for task_id in async_task_ids:
        task = await task_tracker.get_task(task_id)
        if task and task.memory_id:
            memory_system.delete(task.memory_id)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
