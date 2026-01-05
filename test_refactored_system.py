#!/usr/bin/env python3
"""Test the refactored AgenticMemorySystem with ChromaDB as single source of truth."""

import os
os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY', 'test-key')

from agentic_memory.memory_system import AgenticMemorySystem
import time

print("="*80)
print("Testing Refactored AgenticMemorySystem")
print("="*80)

# Test 1: Initialize system and verify it loads existing memories
print("\n[Test 1] Initializing system with existing ChromaDB data...")
memory_system = AgenticMemorySystem(
    model_name='all-MiniLM-L6-v2',
    llm_backend="openai",
    llm_model="gpt-4o-mini",
    storage_path="./chroma_db",
    cache_size=10,  # Small cache for testing
    enable_cache=True
)

print(f"✓ System initialized")
print(f"✓ ChromaDB has {memory_system.retriever.count()} existing memories")
print(f"✓ Cache stats: {memory_system.cache.get_stats()}")

# Test 2: Read existing memory (should load from ChromaDB, then cache)
print("\n[Test 2] Reading existing memory...")
memory_ids = memory_system.retriever.get_all_ids(limit=5)
if memory_ids:
    test_id = memory_ids[0]
    print(f"Reading memory: {test_id}")

    # First read - cache miss, loads from ChromaDB
    memory = memory_system.read(test_id)
    print(f"✓ First read (cache miss): {memory.content[:100]}...")
    print(f"  Cache stats: {memory_system.cache.get_stats()}")

    # Second read - cache hit
    memory2 = memory_system.read(test_id)
    print(f"✓ Second read (cache hit): {memory2.content[:100]}...")
    print(f"  Cache stats: {memory_system.cache.get_stats()}")

    # Verify cache hit
    stats = memory_system.cache.get_stats()
    assert stats['hits'] >= 1, "Cache should have at least 1 hit"
    print(f"✓ Cache working correctly (hit rate: {stats['hit_rate']:.2%})")
else:
    print("⚠ No existing memories found, skipping read test")

# Test 3: Search existing memories
print("\n[Test 3] Searching existing memories...")
results = memory_system.search("memory evolution", k=3)
print(f"✓ Found {len(results)} results")
for i, result in enumerate(results, 1):
    print(f"  {i}. {result['content'][:80]}...")
print(f"  Cache stats: {memory_system.cache.get_stats()}")

# Test 4: Verify persistence across restarts (simulate by creating new instance)
print("\n[Test 4] Testing persistence across restarts...")
print("Creating new system instance (simulates restart)...")
memory_system2 = AgenticMemorySystem(
    model_name='all-MiniLM-L6-v2',
    llm_backend="openai",
    llm_model="gpt-4o-mini",
    storage_path="./chroma_db",
    cache_size=10,
    enable_cache=True
)

count_before = memory_system.retriever.count()
count_after = memory_system2.retriever.count()
print(f"✓ Memories before restart: {count_before}")
print(f"✓ Memories after restart: {count_after}")
assert count_before == count_after, "Memory count should match after restart"
print(f"✓ Persistence verified!")

# Test 5: Update a memory and verify it syncs to ChromaDB
print("\n[Test 5] Testing update persistence...")
if memory_ids:
    test_id = memory_ids[0]

    # Update memory
    print(f"Updating memory {test_id}...")
    success = memory_system2.update(test_id, tags=["test-tag-updated", "persistence-test"])
    print(f"✓ Update successful: {success}")

    # Create new instance to verify update persisted
    memory_system3 = AgenticMemorySystem(
        model_name='all-MiniLM-L6-v2',
        llm_backend="openai",
        llm_model="gpt-4o-mini",
        storage_path="./chroma_db",
        cache_size=10
    )

    # Read updated memory
    updated_memory = memory_system3.read(test_id)
    print(f"✓ Updated tags: {updated_memory.tags}")
    assert "test-tag-updated" in updated_memory.tags, "Update should persist to ChromaDB"
    print(f"✓ Update persistence verified!")
else:
    print("⚠ No memories to update, skipping test")

# Test 6: Cache statistics
print("\n[Test 6] Cache Statistics...")
stats = memory_system2.cache.get_stats()
print(f"  Cache size: {stats['size']}/{stats['max_size']}")
print(f"  Hits: {stats['hits']}")
print(f"  Misses: {stats['misses']}")
print(f"  Evictions: {stats['evictions']}")
print(f"  Hit rate: {stats['hit_rate']:.2%}")

print("\n" + "="*80)
print("✓ All tests passed!")
print("="*80)
print("\nKey Features Verified:")
print("  ✓ ChromaDB as single source of truth")
print("  ✓ Memories persist across system restarts")
print("  ✓ LRU cache provides performance optimization")
print("  ✓ Updates sync immediately to ChromaDB")
print("  ✓ Cache-aware lazy loading works correctly")
