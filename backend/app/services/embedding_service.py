"""
Embedding service for generating and managing embeddings.

Uses sentence-transformers to encode assessment descriptions and metadata
into dense vectors for semantic similarity search.
"""

import json
import logging
import numpy as np
from typing import List, Tuple, Optional
from pathlib import Path

from app.models.catalog import CatalogEntry
from app.utils.config import get_settings


logger = logging.getLogger(__name__)

# Global embedding model instance (lazy loaded)
_embedding_model = None


def get_embedding_model():
    """
    Lazy load embedding model.
    
    Returns:
        sentence-transformers model instance
    """
    global _embedding_model
    
    if _embedding_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            
            settings = get_settings()
            model_name = settings.embedding_model
            
            logger.info(f"Loading embedding model: {model_name}")
            _embedding_model = SentenceTransformer(model_name)
            logger.info(f"✓ Model loaded successfully (dim={_embedding_model.get_sentence_embedding_dimension()})")
            
        except ImportError:
            logger.error("sentence-transformers not installed")
            raise
    
    return _embedding_model


class EmbeddingService:
    """
    Service for generating and managing embeddings.
    
    Responsibilities:
    - Encode text to embeddings
    - Batch processing for efficiency
    - Caching embeddings to disk
    - Memory-efficient storage
    """
    
    def __init__(self):
        """Initialize embedding service."""
        self.settings = get_settings()
        self.model = None
        self.embedding_cache = {}
    
    def encode_text(self, text: str) -> np.ndarray:
        """
        Encode a single text string to embedding vector.
        
        Args:
            text: Text to encode
            
        Returns:
            Embedding vector as numpy array (1D)
        """
        if not text or not text.strip():
            logger.warning("Empty text provided to encode_text")
            return np.zeros(self.settings.embedding_dimension)
        
        try:
            model = get_embedding_model()
            
            # Normalize text
            text = text.strip()[:512]  # Limit to 512 chars
            
            # Single encoding
            embedding = model.encode([text], convert_to_numpy=True)
            
            return embedding[0]
            
        except Exception as e:
            logger.error(f"Failed to encode text: {e}")
            # Return zero vector as fallback
            return np.zeros(self.settings.embedding_dimension)
    
    def encode_batch(self, texts: List[str], show_progress: bool = True) -> np.ndarray:
        """
        Encode multiple texts to embeddings (batch processing for efficiency).
        
        Args:
            texts: List of texts to encode
            show_progress: Show progress bar
            
        Returns:
            Matrix of embeddings (N x D)
        """
        if not texts:
            logger.warning("Empty text list provided to encode_batch")
            return np.zeros((0, self.settings.embedding_dimension))
        
        try:
            model = get_embedding_model()
            
            # Normalize texts
            normalized_texts = [
                text.strip()[:512] if text else ""
                for text in texts
            ]
            
            # Batch encoding
            embeddings = model.encode(
                normalized_texts,
                convert_to_numpy=True,
                show_progress_bar=show_progress,
                batch_size=32
            )
            
            logger.info(f"Encoded {len(texts)} texts to embeddings (shape: {embeddings.shape})")
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to encode batch: {e}")
            return np.zeros((len(texts), self.settings.embedding_dimension))
    
    def encode_assessments(
        self, 
        assessments: List[CatalogEntry],
        show_progress: bool = True
    ) -> Tuple[np.ndarray, List[str]]:
        """
        Encode all assessments by creating rich text representations.
        
        Args:
            assessments: List of catalog entries
            show_progress: Show progress bar
            
        Returns:
            Tuple of (embeddings matrix, assessment identifiers)
        """
        if not assessments:
            logger.warning("Empty assessment list provided")
            return np.zeros((0, self.settings.embedding_dimension)), []
        
        try:
            # Create rich text representation for each assessment
            assessment_texts = []
            assessment_ids = []
            
            for assessment in assessments:
                # Combine multiple fields for richer context
                rich_text = f"""
                {assessment.name}
                {assessment.test_type}
                {assessment.description}
                {assessment.skills}
                {' '.join(assessment.keywords)}
                """.strip()
                
                assessment_texts.append(rich_text)
                assessment_ids.append(assessment.url)
            
            # Encode all texts
            embeddings = self.encode_batch(assessment_texts, show_progress=show_progress)
            
            logger.info(f"Encoded {len(assessments)} assessments")
            return embeddings, assessment_ids
            
        except Exception as e:
            logger.error(f"Failed to encode assessments: {e}")
            return np.zeros((len(assessments), self.settings.embedding_dimension)), []
    
    def encode_query(self, query: str) -> np.ndarray:
        """
        Encode a user query to embedding.
        
        Args:
            query: User query text
            
        Returns:
            Query embedding vector
        """
        if not query or not query.strip():
            logger.warning("Empty query provided")
            return np.zeros(self.settings.embedding_dimension)
        
        return self.encode_text(query)
    
    @staticmethod
    def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """
        Compute cosine similarity between two vectors.
        
        Args:
            a: First vector
            b: Second vector
            
        Returns:
            Cosine similarity score (-1 to 1)
        """
        a_norm = a / (np.linalg.norm(a) + 1e-8)
        b_norm = b / (np.linalg.norm(b) + 1e-8)
        return float(np.dot(a_norm, b_norm))
    
    @staticmethod
    def euclidean_distance(a: np.ndarray, b: np.ndarray) -> float:
        """
        Compute Euclidean distance between two vectors.
        
        Args:
            a: First vector
            b: Second vector
            
        Returns:
            Euclidean distance
        """
        return float(np.linalg.norm(a - b))
    
    @staticmethod
    def top_k_similar(
        query_embedding: np.ndarray,
        embeddings: np.ndarray,
        k: int = 10
    ) -> List[Tuple[int, float]]:
        """
        Find top-k most similar embeddings to query.
        
        Args:
            query_embedding: Query vector
            embeddings: Embeddings matrix (N x D)
            k: Number of top results
            
        Returns:
            List of (index, similarity_score) tuples sorted by similarity
        """
        if len(embeddings) == 0:
            return []
        
        # Compute cosine similarities
        similarities = []
        for i, embedding in enumerate(embeddings):
            sim = EmbeddingService.cosine_similarity(query_embedding, embedding)
            similarities.append((i, sim))
        
        # Sort by similarity (descending) and return top-k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:k]


class EmbeddingCache:
    """
    Persistent cache for embeddings to avoid recomputation.
    """
    
    def __init__(self, cache_path: str = "vectorstore/embeddings_cache.json"):
        """
        Initialize cache.
        
        Args:
            cache_path: Path to cache file
        """
        self.cache_path = Path(cache_path)
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.data = self._load_cache()
    
    def _load_cache(self) -> dict:
        """Load cache from disk."""
        try:
            if self.cache_path.exists():
                with open(self.cache_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load embedding cache: {e}")
        
        return {}
    
    def save_cache(self) -> bool:
        """
        Save cache to disk.
        
        Returns:
            True if successful
        """
        try:
            with open(self.cache_path, 'w') as f:
                json.dump(self.data, f)
            logger.info(f"Saved embedding cache with {len(self.data)} entries")
            return True
        except Exception as e:
            logger.error(f"Failed to save embedding cache: {e}")
            return False
    
    def get(self, key: str) -> Optional[List[float]]:
        """
        Get embedding from cache.
        
        Args:
            key: Cache key (usually URL)
            
        Returns:
            Embedding as list of floats or None
        """
        return self.data.get(key)
    
    def set(self, key: str, embedding: np.ndarray) -> None:
        """
        Store embedding in cache.
        
        Args:
            key: Cache key
            embedding: Embedding vector
        """
        # Convert numpy array to list for JSON serialization
        self.data[key] = embedding.tolist() if isinstance(embedding, np.ndarray) else embedding
    
    def contains(self, key: str) -> bool:
        """Check if key exists in cache."""
        return key in self.data
