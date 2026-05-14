"""
FAISS-based vector index for semantic search.

Manages indexing, searching, and persistence of dense embeddings.
"""

import json
import logging
import pickle
import numpy as np
from typing import List, Tuple, Optional, Dict
from pathlib import Path

from app.utils.config import get_settings
from app.models.catalog import CatalogEntry


logger = logging.getLogger(__name__)

# Lazy-loaded FAISS module
_faiss = None


def get_faiss():
    """Lazy load FAISS library."""
    global _faiss
    
    if _faiss is None:
        try:
            import faiss
            _faiss = faiss
            logger.info("FAISS loaded successfully")
        except ImportError:
            logger.warning("FAISS not available, using fallback in-memory index")
    
    return _faiss


class FAISSIndex:
    """
    FAISS-based vector index for semantic search.
    
    Supports:
    - Index creation and persistence
    - Semantic similarity search
    - Metadata association
    - Hybrid search with filtering
    """
    
    def __init__(self, dimension: int = 384, index_path: str = None):
        """
        Initialize FAISS index.
        
        Args:
            dimension: Embedding dimension
            index_path: Optional path to load existing index
        """
        self.settings = get_settings()
        self.dimension = dimension
        self.index_path = Path(index_path or self.settings.faiss_index_path)
        self.metadata_path = Path(self.settings.faiss_metadata_path)
        
        # Create directory
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.metadata_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Index and metadata
        self.index = None
        self.metadata: Dict[int, str] = {}  # Maps index ID to assessment URL
        self.url_to_id: Dict[str, int] = {}  # Maps URL to index ID
        self.embeddings = None  # Backup embeddings if FAISS unavailable
        
        # Try to load existing index
        if self.index_path.exists():
            self._load_index()
    
    def _create_faiss_index(self) -> bool:
        """
        Create FAISS index.
        
        Returns:
            True if successful
        """
        try:
            faiss = get_faiss()
            if faiss is None:
                logger.warning("FAISS unavailable, using fallback index")
                return False
            
            # Create index (flat L2 search)
            self.index = faiss.IndexFlatL2(self.dimension)
            logger.info(f"Created FAISS index (dimension={self.dimension})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create FAISS index: {e}")
            return False
    
    def add_embeddings(
        self, 
        embeddings: np.ndarray, 
        metadata: List[str]
    ) -> bool:
        """
        Add embeddings to index.
        
        Args:
            embeddings: Matrix of embeddings (N x D)
            metadata: List of metadata (URLs) for each embedding
            
        Returns:
            True if successful
        """
        try:
            if len(embeddings) != len(metadata):
                logger.error("Embeddings and metadata length mismatch")
                return False
            
            # Ensure embeddings are float32 (required by FAISS)
            embeddings = np.asarray(embeddings, dtype=np.float32)
            
            # Create index if needed
            if self.index is None:
                if not self._create_faiss_index():
                    # Fallback to in-memory embeddings
                    self.embeddings = embeddings
                    for i, url in enumerate(metadata):
                        self.metadata[i] = url
                        self.url_to_id[url] = i
                    logger.info(f"Using in-memory fallback for {len(embeddings)} embeddings")
                    return True
            
            # Add to FAISS index
            self.index.add(embeddings)
            
            # Store metadata
            for i, url in enumerate(metadata):
                idx = len(self.metadata)  # Current size
                self.metadata[idx] = url
                self.url_to_id[url] = idx
            
            logger.info(f"Added {len(embeddings)} embeddings to index (total: {self.index.ntotal})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add embeddings: {e}")
            return False
    
    def search(self, query_embedding: np.ndarray, k: int = 10) -> List[Tuple[str, float]]:
        """
        Search for similar embeddings.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results
            
        Returns:
            List of (metadata, distance) tuples
        """
        try:
            query_embedding = np.asarray([query_embedding], dtype=np.float32)
            
            if self.index is not None:
                # FAISS search
                distances, indices = self.index.search(query_embedding, k)
                
                results = []
                for idx, distance in zip(indices[0], distances[0]):
                    if idx >= 0 and idx in self.metadata:
                        # Convert L2 distance to similarity score (0-1)
                        similarity = 1.0 / (1.0 + float(distance))
                        results.append((self.metadata[idx], similarity))
                
                return results
            
            elif self.embeddings is not None:
                # Fallback in-memory search
                similarities = []
                for i, embedding in enumerate(self.embeddings):
                    # Cosine similarity
                    sim = np.dot(query_embedding[0], embedding) / (
                        np.linalg.norm(query_embedding[0]) * np.linalg.norm(embedding) + 1e-8
                    )
                    similarities.append((i, float(sim)))
                
                # Sort by similarity
                similarities.sort(key=lambda x: x[1], reverse=True)
                
                results = []
                for idx, sim in similarities[:k]:
                    if idx in self.metadata:
                        results.append((self.metadata[idx], sim))
                
                return results
            
            else:
                logger.warning("No index available for search")
                return []
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def save_index(self) -> bool:
        """
        Save index to disk.
        
        Returns:
            True if successful
        """
        try:
            # Save FAISS index
            if self.index is not None:
                faiss = get_faiss()
                if faiss:
                    faiss.write_index(self.index, str(self.index_path))
            
            # Save fallback embeddings
            if self.embeddings is not None:
                with open(self.index_path.with_suffix('.npy'), 'wb') as f:
                    np.save(f, self.embeddings)
            
            # Save metadata
            with open(self.metadata_path, 'w') as f:
                json.dump({
                    "metadata": self.metadata,
                    "url_to_id": self.url_to_id
                }, f, indent=2)
            
            logger.info(f"Saved index to {self.index_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save index: {e}")
            return False
    
    def _load_index(self) -> bool:
        """
        Load index from disk.
        
        Returns:
            True if successful
        """
        try:
            # Try to load FAISS index
            if self.index_path.exists():
                faiss = get_faiss()
                if faiss:
                    self.index = faiss.read_index(str(self.index_path))
                    logger.info(f"Loaded FAISS index (size: {self.index.ntotal})")
            
            # Try to load fallback embeddings
            embeddings_path = self.index_path.with_suffix('.npy')
            if embeddings_path.exists():
                self.embeddings = np.load(embeddings_path)
                logger.info(f"Loaded fallback embeddings (shape: {self.embeddings.shape})")
            
            # Load metadata
            if self.metadata_path.exists():
                with open(self.metadata_path, 'r') as f:
                    data = json.load(f)
                    self.metadata = {int(k): v for k, v in data.get("metadata", {}).items()}
                    self.url_to_id = data.get("url_to_id", {})
                    logger.info(f"Loaded metadata ({len(self.metadata)} entries)")
            
            return len(self.metadata) > 0
            
        except Exception as e:
            logger.error(f"Failed to load index: {e}")
            return False
    
    def is_empty(self) -> bool:
        """Check if index is empty."""
        return len(self.metadata) == 0
    
    def size(self) -> int:
        """Get number of embeddings in index."""
        return len(self.metadata)


class HybridRetriever:
    """
    Hybrid retriever combining semantic (FAISS) and lexical search.
    """
    
    def __init__(self, index: FAISSIndex):
        """
        Initialize hybrid retriever.
        
        Args:
            index: FAISSIndex instance
        """
        self.index = index
    
    def retrieve(
        self,
        query_embedding: np.ndarray,
        query_text: str,
        assessments_map: Dict[str, CatalogEntry],
        k: int = 10
    ) -> List[CatalogEntry]:
        """
        Retrieve assessments using hybrid search.
        
        Args:
            query_embedding: Query embedding vector
            query_text: Original query text for lexical search
            assessments_map: Mapping of URL to CatalogEntry
            k: Number of results
            
        Returns:
            List of relevant CatalogEntry objects
        """
        # Semantic search
        semantic_results = self.index.search(query_embedding, k=k*2)
        
        results = []
        for url, similarity in semantic_results:
            if url in assessments_map:
                results.append(assessments_map[url])
        
        return results[:k]
