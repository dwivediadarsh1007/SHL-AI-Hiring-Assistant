"""
Tests for embedding and retrieval services.
"""

import numpy as np
import pytest

from app.services.embedding_service import EmbeddingService, EmbeddingCache
from app.models.catalog import CatalogEntry


class TestEmbeddingService:
    """Tests for embedding service."""
    
    @pytest.fixture
    def service(self):
        """Create embedding service."""
        return EmbeddingService()
    
    def test_initialization(self, service):
        """Test service initialization."""
        assert service.settings is not None
        assert service.settings.embedding_dimension > 0
    
    def test_cosine_similarity(self):
        """Test cosine similarity computation."""
        v1 = np.array([1, 0, 0])
        v2 = np.array([1, 0, 0])
        v3 = np.array([0, 1, 0])
        
        # Same vectors
        sim_same = EmbeddingService.cosine_similarity(v1, v2)
        assert abs(sim_same - 1.0) < 0.01
        
        # Orthogonal vectors
        sim_ortho = EmbeddingService.cosine_similarity(v1, v3)
        assert abs(sim_ortho) < 0.01
    
    def test_euclidean_distance(self):
        """Test Euclidean distance computation."""
        v1 = np.array([0, 0, 0])
        v2 = np.array([1, 1, 1])
        
        dist = EmbeddingService.euclidean_distance(v1, v2)
        expected = np.sqrt(3)
        assert abs(dist - expected) < 0.01
    
    def test_top_k_similar(self):
        """Test top-k similarity search."""
        query = np.array([1, 0, 0])
        embeddings = np.array([
            [1, 0, 0],    # Very similar
            [0.8, 0.2, 0],  # Similar
            [0, 1, 0],     # Orthogonal
            [0, 0, 1]      # Orthogonal
        ])
        
        results = EmbeddingService.top_k_similar(query, embeddings, k=2)
        
        assert len(results) == 2
        assert results[0][0] == 0  # Most similar should be index 0
        assert results[0][1] > results[1][1]  # First should have higher similarity


class TestEmbeddingCache:
    """Tests for embedding cache."""
    
    def test_cache_operations(self, tmp_path):
        """Test cache get/set operations."""
        cache_file = tmp_path / "cache.json"
        cache = EmbeddingCache(str(cache_file))
        
        # Test set
        embedding = np.array([0.1, 0.2, 0.3])
        cache.set("test_key", embedding)
        
        assert cache.contains("test_key")
        
        # Test get
        retrieved = cache.get("test_key")
        assert retrieved is not None
        assert len(retrieved) == 3
    
    def test_cache_persistence(self, tmp_path):
        """Test cache persistence to disk."""
        cache_file = tmp_path / "cache.json"
        
        # Create and save cache
        cache1 = EmbeddingCache(str(cache_file))
        cache1.set("key1", np.array([0.1, 0.2]))
        cache1.save_cache()
        
        # Load in new instance
        cache2 = EmbeddingCache(str(cache_file))
        assert cache2.contains("key1")
        retrieved = cache2.get("key1")
        assert retrieved is not None


class TestCatalogEntry:
    """Tests for catalog entry compatibility with embeddings."""
    
    def test_entry_to_text(self):
        """Test converting entry to text for embedding."""
        entry = CatalogEntry(
            name="Test Assessment",
            url="https://www.shl.com/test/",
            description="Test description",
            test_type="cognitive",
            skills="reasoning, problem-solving",
            keywords=["test", "reasoning"]
        )
        
        # Should be convertible to string
        text = f"{entry.name} {entry.description} {entry.skills}"
        assert len(text) > 0
        assert "Test Assessment" in text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
