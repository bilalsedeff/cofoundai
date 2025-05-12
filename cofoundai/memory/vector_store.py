"""
CoFound.ai Vector Store Memory Implementation

This module implements vector-based memory storage for long-term context
retention in the agent-based system.
"""

from typing import Dict, List, Optional, Any
import uuid
import json
import os
from pathlib import Path

from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStore
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import FastEmbedEmbeddings

from cofoundai.utils.logger import get_logger

logger = get_logger(__name__)

class VectorMemory:
    """Vector-based memory implementation using FAISS for storing and retrieving embeddings."""
    
    def __init__(
            self, 
            collection_name: str,
            embeddings: Optional[Embeddings] = None,
            persist_directory: Optional[str] = None
        ):
        """
        Initialize the vector memory.
        
        Args:
            collection_name: Name of the memory collection
            embeddings: Embedding model to use (defaults to FastEmbedEmbeddings)
            persist_directory: Directory to persist vector store (defaults to ./data/vector_store)
        """
        self.collection_name = collection_name
        self.embeddings = embeddings or FastEmbedEmbeddings()
        self.persist_directory = persist_directory or os.path.join("data", "vector_store")
        self.collection_path = os.path.join(self.persist_directory, self.collection_name)
        self.vector_store = self._initialize_vector_store()
        
        logger.info(f"Initialized vector memory for collection: {collection_name}")
    
    def _initialize_vector_store(self) -> VectorStore:
        """Initialize or load the vector store from disk."""
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
        
        if os.path.exists(self.collection_path):
            try:
                logger.info(f"Loading existing vector store from {self.collection_path}")
                return FAISS.load_local(self.collection_path, self.embeddings)
            except Exception as e:
                logger.error(f"Error loading vector store: {e}")
                logger.info("Creating new vector store")
                return FAISS.from_texts(["_initialization_document_"], self.embeddings)
        else:
            logger.info(f"Creating new vector store at {self.collection_path}")
            return FAISS.from_texts(["_initialization_document_"], self.embeddings)
    
    def add_texts(self, texts: List[str], metadatas: Optional[List[Dict[str, Any]]] = None) -> List[str]:
        """
        Add texts to the vector store with optional metadata.
        
        Args:
            texts: List of text strings to add
            metadatas: List of metadata dictionaries, one for each text
            
        Returns:
            List of document IDs
        """
        if not metadatas:
            metadatas = [{} for _ in texts]
            
        # Add timestamps and IDs if not present
        for metadata in metadatas:
            if "id" not in metadata:
                metadata["id"] = str(uuid.uuid4())
            if "timestamp" not in metadata:
                metadata["timestamp"] = str(uuid.now().isoformat())
        
        try:
            ids = self.vector_store.add_texts(texts, metadatas)
            self._persist()
            logger.info(f"Added {len(texts)} documents to vector store")
            return ids
        except Exception as e:
            logger.error(f"Error adding texts to vector store: {e}")
            return []
    
    def similarity_search(
            self, 
            query: str, 
            k: int = 5, 
            filter: Optional[Dict[str, Any]] = None
        ) -> List[Dict[str, Any]]:
        """
        Search for similar texts in the vector store.
        
        Args:
            query: Query text
            k: Number of results to return
            filter: Optional metadata filter
            
        Returns:
            List of dictionaries containing document text and metadata
        """
        try:
            docs = self.vector_store.similarity_search(query, k=k, filter=filter)
            results = []
            
            for doc in docs:
                results.append({
                    "text": doc.page_content,
                    "metadata": doc.metadata
                })
            
            logger.info(f"Found {len(results)} similar documents for query: {query[:50]}...")
            return results
        except Exception as e:
            logger.error(f"Error searching vector store: {e}")
            return []
    
    def _persist(self) -> None:
        """Persist the vector store to disk."""
        try:
            self.vector_store.save_local(self.collection_path)
            logger.info(f"Persisted vector store to {self.collection_path}")
        except Exception as e:
            logger.error(f"Error persisting vector store: {e}")
    
    def clear(self) -> None:
        """Clear all documents from the vector store."""
        try:
            # Re-initialize with empty store
            self.vector_store = FAISS.from_texts(["_initialization_document_"], self.embeddings)
            self._persist()
            logger.info(f"Cleared vector store for collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error clearing vector store: {e}") 