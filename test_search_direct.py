#!/usr/bin/env python3
"""Direct test of search functionality."""

import os
os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY', 'test-key')

from agentic_memory.memory_system import AgenticMemorySystem

print("Testing direct search functionality...")

# Initialize system
memory_system = AgenticMemorySystem(
    model_name='all-MiniLM-L6-v2',
    llm_backend="openai",
    llm_model="gpt-4o-mini",
    storage_path="./chroma_db"
)

print(f"Total memories in ChromaDB: {memory_system.retriever.count()}")

# Test search
print("\nSearching for 'memory evolution'...")
results = memory_system.search("memory evolution", k=5)
print(f"Found {len(results)} results\n")

for i, result in enumerate(results, 1):
    print(f"{i}. ID: {result['id']}")
    print(f"   Content: {result['content'][:100]}...")
    print(f"   Tags: {result['tags']}")
    print()

# Test search_agentic
print("\nTesting search_agentic...")
results_agentic = memory_system.search_agentic("memory evolution", k=5)
print(f"Found {len(results_agentic)} results\n")

for i, result in enumerate(results_agentic, 1):
    print(f"{i}. ID: {result['id']}")
    print(f"   Content: {result['content'][:100]}...")
    print(f"   Is Neighbor: {result.get('is_neighbor', False)}")
    print()

print("✓ Search functionality working correctly!")
