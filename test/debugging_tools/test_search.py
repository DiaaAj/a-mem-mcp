#!/usr/bin/env python3
"""Test memory search functionality."""

from agentic_memory.memory_system import AgenticMemorySystem

# Initialize the memory system (read-only mode for testing)
memory_system = AgenticMemorySystem(
    model_name='all-MiniLM-L6-v2',
    llm_backend="openai",
    llm_model="gpt-4o-mini",
    storage_path="./chroma_db"
)

print("Testing memory search for 'memory evolution'...")
print("="*80)

# Test 1: Basic search
results = memory_system.search("memory evolution process strengthen update_neighbor", k=5)
print(f"\n1. Basic search() returned {len(results)} results:\n")
for i, result in enumerate(results, 1):
    print(f"Result #{i}")
    print(f"ID: {result['id']}")
    print(f"Content: {result['content'][:150]}...")
    print(f"Keywords: {result['keywords']}")
    print(f"Tags: {result['tags']}")
    print(f"Score: {result.get('score', 'N/A')}")
    print("-"*80)

# Test 2: Agentic search (with linked neighbors)
print("\n2. Agentic search_agentic() with linked neighbors:\n")
results_agentic = memory_system.search_agentic("memory evolution", k=5)
print(f"Returned {len(results_agentic)} results:\n")
for i, result in enumerate(results_agentic, 1):
    print(f"Result #{i}")
    print(f"ID: {result['id']}")
    print(f"Content: {result['content'][:150]}...")
    print(f"Is Neighbor: {result.get('is_neighbor', False)}")
    print(f"Tags: {result['tags']}")
    print("-"*80)

# Test 3: Check in-memory storage
print(f"\n3. In-memory storage check:")
print(f"Total memories in system: {len(memory_system.memories)}")
print(f"Memory IDs: {list(memory_system.memories.keys())[:5]}...")
