"""Tests for thread-safe cache wrapper."""

import threading
import pytest
from agentic_memory.thread_safe_cache import ThreadSafeMemoryCache
from agentic_memory.memory_system import MemoryNote


def test_basic_operations():
    """Test basic cache operations work correctly."""
    cache = ThreadSafeMemoryCache(max_size=10)

    # Create and add a note
    note = MemoryNote(content="Test memory")
    cache.put(note.id, note)

    # Retrieve note
    retrieved = cache.get(note.id)
    assert retrieved is not None
    assert retrieved.content == "Test memory"
    assert retrieved.id == note.id

    # Remove note
    cache.remove(note.id)
    assert cache.get(note.id) is None


def test_lru_eviction():
    """Test LRU eviction works with small cache."""
    cache = ThreadSafeMemoryCache(max_size=3)

    # Add 3 notes (at capacity)
    notes = [MemoryNote(content=f"Memory {i}") for i in range(3)]
    for note in notes:
        cache.put(note.id, note)

    stats = cache.get_stats()
    assert stats['size'] == 3

    # Add 4th note - should evict oldest
    note4 = MemoryNote(content="Memory 4")
    cache.put(note4.id, note4)

    stats = cache.get_stats()
    assert stats['size'] == 3
    assert stats['evictions'] == 1

    # First note should be evicted
    assert cache.get(notes[0].id) is None
    # Others should still exist
    assert cache.get(notes[1].id) is not None
    assert cache.get(notes[2].id) is not None
    assert cache.get(note4.id) is not None


def test_concurrent_cache_access():
    """Test thread-safe cache with 10 concurrent workers."""
    cache = ThreadSafeMemoryCache(max_size=100)
    errors = []

    def worker(thread_id):
        """Worker thread that performs cache operations."""
        try:
            for i in range(10):
                # Create and store note
                note = MemoryNote(content=f"Thread {thread_id} note {i}")
                cache.put(note.id, note)

                # Retrieve note
                retrieved = cache.get(note.id)
                assert retrieved is not None
                assert retrieved.content == note.content

                # Update note (put with same id)
                note.content = f"Updated thread {thread_id} note {i}"
                cache.put(note.id, note)

                # Verify update
                retrieved = cache.get(note.id)
                assert retrieved.content == note.content
        except Exception as e:
            errors.append(f"Thread {thread_id}: {e}")

    # Launch 10 threads
    threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Check no errors occurred
    assert len(errors) == 0, f"Errors: {errors}"

    # Verify cache stats
    stats = cache.get_stats()
    assert stats['size'] <= 100  # LRU eviction worked
    assert stats['hits'] > 0
    assert stats['misses'] == 0  # All gets should hit


def test_cache_stats():
    """Test cache statistics tracking."""
    cache = ThreadSafeMemoryCache(max_size=10)

    note = MemoryNote(content="Test")
    cache.put(note.id, note)

    # Hit
    cache.get(note.id)
    stats = cache.get_stats()
    assert stats['hits'] == 1
    assert stats['misses'] == 0

    # Miss
    cache.get("nonexistent-id")
    stats = cache.get_stats()
    assert stats['hits'] == 1
    assert stats['misses'] == 1
    assert stats['hit_rate'] == 0.5


def test_clear_cache():
    """Test clearing cache resets everything."""
    cache = ThreadSafeMemoryCache(max_size=10)

    # Add notes
    for i in range(5):
        note = MemoryNote(content=f"Memory {i}")
        cache.put(note.id, note)

    # Generate some stats
    cache.get("nonexistent")

    stats = cache.get_stats()
    assert stats['size'] == 5
    assert stats['misses'] == 1

    # Clear
    cache.clear()

    stats = cache.get_stats()
    assert stats['size'] == 0
    assert stats['hits'] == 0
    assert stats['misses'] == 0
    assert stats['evictions'] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
