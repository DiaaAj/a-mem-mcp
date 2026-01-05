#!/usr/bin/env python3
"""Test direct ChromaDB access without AgenticMemorySystem."""

from agentic_memory.retrievers import ChromaRetriever

# Connect directly to existing ChromaDB
retriever = ChromaRetriever(collection_name="memories", model_name="all-MiniLM-L6-v2", persist_directory="./chroma_db")

print("Testing direct ChromaDB search...")
print("="*80)

# Test search
results = retriever.search("memory evolution process strengthen update_neighbor", k=5)

print(f"\nChromaDB search results:")
print(f"IDs found: {len(results.get('ids', [[]])[0])}")
print()

if results and 'ids' in results and results['ids'] and len(results['ids'][0]) > 0:
    for i, doc_id in enumerate(results['ids'][0], 1):
        print(f"Result #{i}")
        print(f"ID: {doc_id}")

        if i-1 < len(results['metadatas'][0]):
            metadata = results['metadatas'][0][i-1]
            print(f"Content: {metadata.get('content', '')[:150]}...")
            print(f"Keywords: {metadata.get('keywords', [])}")
            print(f"Tags: {metadata.get('tags', [])}")
            print(f"Context: {metadata.get('context', '')[:100]}")

        if 'distances' in results and i-1 < len(results['distances'][0]):
            print(f"Distance: {results['distances'][0][i-1]}")

        print("-"*80)
else:
    print("No results found!")

# Check collection stats
print(f"\nCollection stats:")
print(f"Total documents in collection: {retriever.collection.count()}")
