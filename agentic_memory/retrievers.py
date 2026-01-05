from typing import List, Dict, Any, Optional, Union
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
import nltk
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import chromadb
from chromadb.config import Settings
import pickle
from nltk.tokenize import word_tokenize
import os
import json
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

def simple_tokenize(text):
    return word_tokenize(text)

class ChromaRetriever:
    """Vector database retrieval using ChromaDB"""
    def __init__(self, collection_name: str = "memories", model_name: str = "all-MiniLM-L6-v2", persist_directory: str = "./chroma_db"):
        """Initialize ChromaDB retriever.

        Args:
            collection_name: Name of the ChromaDB collection
            model_name: Name of the sentence transformer model
            persist_directory: Directory path for persistent storage
        """
        self.persist_directory = persist_directory
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.embedding_function = SentenceTransformerEmbeddingFunction(model_name=model_name)
        self.collection = self.client.get_or_create_collection(name=collection_name, embedding_function=self.embedding_function)
        
    def add_document(self, document: str, metadata: Dict, doc_id: str):
        """Add a document to ChromaDB with enhanced embedding using metadata.
        
        Args:
            document: Text content to add
            metadata: Dictionary of metadata including keywords, tags, context
            doc_id: Unique identifier for the document
        """
        # Build enhanced document content including semantic metadata
        enhanced_document = document
        
        # Add context information
        if 'context' in metadata and metadata['context'] != "General":
            enhanced_document += f" context: {metadata['context']}"
        
        # Add keywords information    
        if 'keywords' in metadata and metadata['keywords']:
            keywords = metadata['keywords'] if isinstance(metadata['keywords'], list) else json.loads(metadata['keywords'])
            if keywords:
                enhanced_document += f" keywords: {', '.join(keywords)}"
        
        # Add tags information
        if 'tags' in metadata and metadata['tags']:
            tags = metadata['tags'] if isinstance(metadata['tags'], list) else json.loads(metadata['tags'])
            if tags:
                enhanced_document += f" tags: {', '.join(tags)}"
        
        # Convert MemoryNote object to serializable format
        processed_metadata = {}
        for key, value in metadata.items():
            if isinstance(value, list):
                processed_metadata[key] = json.dumps(value)
            elif isinstance(value, dict):
                processed_metadata[key] = json.dumps(value)
            else:
                processed_metadata[key] = str(value)
        
        # Store enhanced document content for better embedding
        processed_metadata['enhanced_content'] = enhanced_document
                
        # Use enhanced document content for embedding generation
        self.collection.add(
            documents=[enhanced_document],
            metadatas=[processed_metadata],
            ids=[doc_id]
        )
        
    def delete_document(self, doc_id: str):
        """Delete a document from ChromaDB.
        
        Args:
            doc_id: ID of document to delete
        """
        self.collection.delete(ids=[doc_id])
        
    def search(self, query: str, k: int = 5):
        """Search for similar documents.
        
        Args:
            query: Query text
            k: Number of results to return
            
        Returns:
            Dict with documents, metadatas, ids, and distances
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=k
        )
        
        # Convert string metadata back to original types
        if 'metadatas' in results and results['metadatas'] and len(results['metadatas']) > 0:
            # First level is a list with one item per query
            for i in range(len(results['metadatas'])):
                # Second level is a list of metadata dicts for each result
                if isinstance(results['metadatas'][i], list):
                    for j in range(len(results['metadatas'][i])):
                        # Process each metadata dict
                        if isinstance(results['metadatas'][i][j], dict):
                            metadata = results['metadatas'][i][j]
                            for key, value in metadata.items():
                                try:
                                    # Try to parse JSON for lists and dicts
                                    if isinstance(value, str) and (value.startswith('[') or value.startswith('{')):
                                        metadata[key] = json.loads(value)
                                    # Convert numeric strings back to numbers
                                    elif isinstance(value, str) and value.replace('.', '', 1).isdigit():
                                        if '.' in value:
                                            metadata[key] = float(value)
                                        else:
                                            metadata[key] = int(value)
                                except (json.JSONDecodeError, ValueError):
                                    # If parsing fails, keep the original string
                                    pass

        return results

    def _deserialize_metadata(self, metadata: Dict) -> Dict:
        """Deserialize ChromaDB metadata (convert JSON strings back to native types).

        Args:
            metadata: Raw metadata dict from ChromaDB

        Returns:
            Dict with deserialized values
        """
        deserialized = {}
        for key, value in metadata.items():
            try:
                # Try to parse JSON for lists and dicts
                if isinstance(value, str) and (value.startswith('[') or value.startswith('{')):
                    deserialized[key] = json.loads(value)
                # Convert numeric strings back to numbers
                elif isinstance(value, str) and value.replace('.', '', 1).isdigit():
                    if '.' in value:
                        deserialized[key] = float(value)
                    else:
                        deserialized[key] = int(value)
                else:
                    deserialized[key] = value
            except (json.JSONDecodeError, ValueError):
                # If parsing fails, keep the original string
                deserialized[key] = value
        return deserialized

    def get_by_id(self, doc_id: str) -> Optional[Dict]:
        """Retrieve a single document by ID with deserialized metadata.

        Args:
            doc_id: Document ID to retrieve

        Returns:
            Dict with deserialized metadata if found, None otherwise
        """
        try:
            results = self.collection.get(ids=[doc_id])
            if results['ids'] and len(results['ids']) > 0:
                metadata = results['metadatas'][0]
                return self._deserialize_metadata(metadata)
        except Exception as e:
            print(f"Error retrieving document {doc_id}: {e}")
        return None

    def get_by_ids(self, doc_ids: List[str]) -> Dict[str, Dict]:
        """Batch retrieve multiple documents by IDs.

        Args:
            doc_ids: List of document IDs to retrieve

        Returns:
            Dict mapping doc_id to deserialized metadata
        """
        try:
            results = self.collection.get(ids=doc_ids)
            metadata_map = {}
            for i, doc_id in enumerate(results['ids']):
                metadata_map[doc_id] = self._deserialize_metadata(results['metadatas'][i])
            return metadata_map
        except Exception as e:
            print(f"Error batch retrieving documents: {e}")
            return {}

    def update_document(self, doc_id: str, metadata: Dict, content: str = None):
        """Update document metadata (and optionally content) in-place.

        Args:
            doc_id: Document ID to update
            metadata: New metadata dict
            content: New content (optional, if None will keep existing)
        """
        try:
            # Get current document if content not provided
            if content is None:
                current = self.collection.get(ids=[doc_id])
                if not current['ids']:
                    print(f"Document {doc_id} not found for update")
                    return
                content = current['documents'][0]

            # Process metadata (serialize lists/dicts to JSON)
            processed_metadata = {}
            for key, value in metadata.items():
                if isinstance(value, (list, dict)):
                    processed_metadata[key] = json.dumps(value)
                else:
                    processed_metadata[key] = str(value)

            # Build enhanced document for embedding
            enhanced_document = content
            if 'context' in metadata and metadata['context'] != "General":
                enhanced_document += f" context: {metadata['context']}"
            if 'keywords' in metadata and metadata['keywords']:
                keywords = metadata['keywords'] if isinstance(metadata['keywords'], list) else json.loads(metadata['keywords'])
                if keywords:
                    enhanced_document += f" keywords: {', '.join(keywords)}"
            if 'tags' in metadata and metadata['tags']:
                tags = metadata['tags'] if isinstance(metadata['tags'], list) else json.loads(metadata['tags'])
                if tags:
                    enhanced_document += f" tags: {', '.join(tags)}"

            processed_metadata['enhanced_content'] = enhanced_document

            # ChromaDB doesn't have native update, use delete+add
            self.collection.delete(ids=[doc_id])
            self.collection.add(
                documents=[enhanced_document],
                metadatas=[processed_metadata],
                ids=[doc_id]
            )
        except Exception as e:
            print(f"Error updating document {doc_id}: {e}")

    def count(self) -> int:
        """Get total number of documents in collection.

        Returns:
            Number of documents
        """
        return self.collection.count()

    def get_all_ids(self, limit: int = None, offset: int = 0) -> List[str]:
        """Get all document IDs with optional pagination.

        Args:
            limit: Maximum number of IDs to return (None for all)
            offset: Number of IDs to skip

        Returns:
            List of document IDs
        """
        try:
            results = self.collection.get(limit=limit, offset=offset)
            return results['ids']
        except Exception as e:
            print(f"Error getting document IDs: {e}")
            return []
