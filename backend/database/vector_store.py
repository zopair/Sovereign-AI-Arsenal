import chromadb
import numpy as np
from typing import List, Dict, Optional, Any
import logging
from sentence_transformers import SentenceTransformer
import json
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.client = None
        self.collection = None
        self.embedding_model = None
        self._initialize()
    
    def _initialize(self):
        """Initialize ChromaDB client and embedding model"""
        try:
            # Initialize ChromaDB
            persist_directory = self.config.get('persist_directory', 'data/vectors')
            os.makedirs(persist_directory, exist_ok=True)
            
            self.client = chromadb.PersistentClient(path=persist_directory)
            collection_name = self.config.get('collection_name', 'ai_repositories')
            
            # Get or create collection
            try:
                self.collection = self.client.get_collection(name=collection_name)
                logger.info(f"Connected to existing collection: {collection_name}")
            except chromadb.exceptions.CollectionNotFound:
                self.collection = self.client.create_collection(
                    name=collection_name,
                    metadata={"description": "AI repository embeddings"}
                )
                logger.info(f"Created new collection: {collection_name}")
            
            # Initialize embedding model
            model_name = self.config.get('embedding_model', 'all-MiniLM-L6-v2')
            self.embedding_model = SentenceTransformer(model_name)
            logger.info(f"Initialized embedding model: {model_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            raise
    
    def add_repository_embedding(self, 
                               repo_id: str, 
                               content: str, 
                               metadata: Dict[str, Any] = None) -> str:
        """Add repository content embedding to vector store"""
        try:
            # Generate embedding
            embedding = self.embedding_model.encode(content)
            
            # Prepare metadata
            repo_metadata = {
                'repo_id': repo_id,
                'content_length': len(content),
                'created_at': datetime.utcnow().isoformat(),
                **(metadata or {})
            }
            
            # Add to collection
            self.collection.add(
                embeddings=[embedding.tolist()],
                documents=[content],
                metadatas=[repo_metadata],
                ids=[repo_id]
            )
            
            logger.info(f"Added embedding for repository: {repo_id}")
            return repo_id
            
        except Exception as e:
            logger.error(f"Failed to add repository embedding: {e}")
            raise
    
    def search_similar_repositories(self, 
                                  query: str, 
                                  top_k: int = 10,
                                  where: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Search for similar repositories using vector similarity"""
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode(query)
            
            # Search in collection
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=top_k,
                where=where,
                include=['documents', 'metadatas', 'distances']
            )
            
            # Format results
            formatted_results = []
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    'id': results['ids'][0][i],
                    'document': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'similarity_score': 1 - results['distances'][0][i]  # Convert distance to similarity
                })
            
            logger.info(f"Found {len(formatted_results)} similar repositories")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Failed to search similar repositories: {e}")
            raise
    
    def get_repository_embedding(self, repo_id: str) -> Optional[Dict[str, Any]]:
        """Get repository embedding by ID"""
        try:
            results = self.collection.get(
                ids=[repo_id],
                include=['documents', 'metadatas']
            )
            
            if results['ids']:
                return {
                    'id': results['ids'][0],
                    'document': results['documents'][0],
                    'metadata': results['metadatas'][0]
                }
            return None
            
        except Exception as e:
            logger.error(f"Failed to get repository embedding: {e}")
            raise
    
    def update_repository_embedding(self, 
                                 repo_id: str, 
                                 content: str, 
                                 metadata: Dict[str, Any] = None):
        """Update repository embedding"""
        try:
            # Remove existing embedding
            self.collection.delete(ids=[repo_id])
            
            # Add new embedding
            self.add_repository_embedding(repo_id, content, metadata)
            
            logger.info(f"Updated embedding for repository: {repo_id}")
            
        except Exception as e:
            logger.error(f"Failed to update repository embedding: {e}")
            raise
    
    def delete_repository_embedding(self, repo_id: str):
        """Delete repository embedding"""
        try:
            self.collection.delete(ids=[repo_id])
            logger.info(f"Deleted embedding for repository: {repo_id}")
            
        except Exception as e:
            logger.error(f"Failed to delete repository embedding: {e}")
            raise
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        try:
            count = self.collection.count()
            return {
                'total_embeddings': count,
                'collection_name': self.collection.name,
                'last_updated': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            raise
    
    def batch_add_embeddings(self, 
                           embeddings_data: List[Dict[str, Any]]) -> List[str]:
        """Add multiple embeddings in batch"""
        try:
            ids = []
            documents = []
            metadatas = []
            embeddings = []
            
            for data in embeddings_data:
                repo_id = data['repo_id']
                content = data['content']
                metadata = data.get('metadata', {})
                
                # Generate embedding
                embedding = self.embedding_model.encode(content)
                
                ids.append(repo_id)
                documents.append(content)
                metadatas.append(metadata)
                embeddings.append(embedding.tolist())
            
            # Add to collection
            self.collection.add(
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Added {len(ids)} embeddings in batch")
            return ids
            
        except Exception as e:
            logger.error(f"Failed to batch add embeddings: {e}")
            raise

# Global vector store instance
vector_store = None

def init_vector_store(config: Dict[str, Any] = None) -> VectorStore:
    """Initialize global vector store instance"""
    global vector_store
    vector_store = VectorStore(config)
    return vector_store

def get_vector_store() -> VectorStore:
    """Get global vector store instance"""
    if vector_store is None:
        raise RuntimeError("Vector store not initialized. Call init_vector_store() first.")
    return vector_store