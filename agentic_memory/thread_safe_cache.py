"""Thread-safe wrapper for MemoryCache.

This module provides a thread-safe wrapper around the MemoryCache class
to support concurrent access from multiple threads during async operations.
"""

import threading
from typing import Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .memory_system import MemoryNote


class ThreadSafeMemoryCache:
    """Thread-safe wrapper around MemoryCache using threading.Lock.

    This wrapper ensures that all cache operations are atomic and safe
    for concurrent access from multiple threads. Each method acquires
    a lock before delegating to the underlying MemoryCache.
    """

    def __init__(self, max_size: int = 1000):
        """Initialize thread-safe cache wrapper.

        Args:
            max_size: Maximum number of memories to keep in cache
        """
        # Import here to avoid circular dependency
        from .memory_system import MemoryCache

        self._cache = MemoryCache(max_size=max_size)
        self._lock = threading.Lock()

    def get(self, memory_id: str) -> Optional["MemoryNote"]:
        """Thread-safe get operation.

        Args:
            memory_id: ID of memory to retrieve

        Returns:
            MemoryNote if found in cache, None otherwise
        """
        with self._lock:
            return self._cache.get(memory_id)

    def put(self, memory_id: str, note: "MemoryNote"):
        """Thread-safe put operation.

        Args:
            memory_id: ID of memory
            note: MemoryNote object to cache
        """
        with self._lock:
            self._cache.put(memory_id, note)

    def remove(self, memory_id: str):
        """Thread-safe remove operation.

        Args:
            memory_id: ID of memory to remove
        """
        with self._lock:
            self._cache.remove(memory_id)

    def clear(self):
        """Thread-safe clear operation."""
        with self._lock:
            self._cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Thread-safe stats retrieval.

        Returns:
            Dict with cache metrics (size, hits, misses, evictions, hit_rate)
        """
        with self._lock:
            return self._cache.get_stats()
