#!/usr/bin/env python3
"""Script to inspect stored memories in the ChromaDB database."""

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
import json

def inspect_memories():
    # Connect to existing ChromaDB
    client = chromadb.PersistentClient(path="./chroma_db")
    embedding_function = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

    try:
        collection = client.get_collection(name="memories", embedding_function=embedding_function)

        # Get all documents
        results = collection.get()

        print(f"{'='*80}")
        print(f"TOTAL MEMORIES: {len(results['ids'])}")
        print(f"{'='*80}\n")

        # Display each memory
        for i, doc_id in enumerate(results['ids'], 1):
            metadata = results['metadatas'][i-1]

            print(f"Memory #{i}")
            print(f"ID: {doc_id}")
            print(f"Content: {metadata.get('content', 'N/A')[:200]}...")

            # Parse JSON fields
            keywords = metadata.get('keywords', '[]')
            if isinstance(keywords, str):
                keywords = json.loads(keywords) if keywords.startswith('[') else []
            print(f"Keywords: {keywords}")

            tags = metadata.get('tags', '[]')
            if isinstance(tags, str):
                tags = json.loads(tags) if tags.startswith('[') else []
            print(f"Tags: {tags}")

            print(f"Context: {metadata.get('context', 'N/A')[:150]}")

            links = metadata.get('links', '[]')
            if isinstance(links, str):
                links = json.loads(links) if links.startswith('[') else []
            print(f"Links: {len(links)} connections")

            print(f"Timestamp: {metadata.get('timestamp', 'N/A')}")
            print(f"Retrieval Count: {metadata.get('retrieval_count', 'N/A')}")
            print(f"{'-'*80}\n")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_memories()
