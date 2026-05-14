"""
Retrieval service orchestrating FAISS search and ranking.
"""

import logging
from typing import List, Dict, Optional, Tuple

from app.models.catalog import CatalogEntry
from app.services.embedding_service import EmbeddingService
from app.retrieval.faiss_index import FAISSIndex, HybridRetriever
from app.utils.config import get_settings


logger = logging.getLogger(__name__)


class RetrievalService:
    """
    High-level retrieval service combining embeddings and FAISS search.
    
    Handles:
    - Query encoding
    - Semantic search via FAISS
    - Result ranking and filtering
    - Metadata association
    """
    
    def __init__(self):
        """Initialize retrieval service."""
        self.settings = get_settings()
        self.embedding_service = EmbeddingService()
        self.faiss_index = FAISSIndex(dimension=self.settings.embedding_dimension)
        self.hybrid_retriever = HybridRetriever(self.faiss_index)
        self.assessments_map: Dict[str, CatalogEntry] = {}
    
    def build_index(self, assessments: List[CatalogEntry]) -> bool:
        """
        Build FAISS index from assessments.
        
        Args:
            assessments: List of CatalogEntry objects
            
        Returns:
            True if successful
        """
        try:
            logger.info(f"Building retrieval index for {len(assessments)} assessments...")
            
            # Encode assessments
            embeddings, assessment_urls = self.embedding_service.encode_assessments(
                assessments,
                show_progress=True
            )
            
            if len(embeddings) == 0:
                logger.error("Failed to encode assessments")
                return False
            
            # Add to FAISS index
            if not self.faiss_index.add_embeddings(embeddings, assessment_urls):
                logger.error("Failed to add embeddings to index")
                return False
            
            # Store assessment map
            for assessment in assessments:
                self.assessments_map[assessment.url] = assessment
            
            # Save index
            if not self.faiss_index.save_index():
                logger.warning("Failed to save index (continuing anyway)")
            
            logger.info(f"✓ Index built successfully ({len(assessments)} assessments)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to build index: {e}")
            return False
    
    def load_index(self) -> bool:
        """
        Load existing FAISS index from disk.
        
        Returns:
            True if successful
        """
        try:
            if self.faiss_index.is_empty():
                logger.warning("No existing index found")
                return False
            
            logger.info(f"Loaded index with {self.faiss_index.size()} assessments")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load index: {e}")
            return False
    
    def retrieve(
        self,
        query: str,
        top_k: int = 10
    ) -> List[CatalogEntry]:
        """
        Retrieve relevant assessments for a query.
        
        Args:
            query: User query text
            top_k: Number of results to return
            
        Returns:
            List of relevant CatalogEntry objects
        """
        try:
            # Validate inputs
            if not query or not query.strip():
                logger.warning("Empty query provided")
                return []
            
            if top_k < 1 or top_k > 100:
                logger.warning(f"Invalid top_k={top_k}, clamping to [1, 100]")
                top_k = max(1, min(100, top_k))
            
            # Encode query
            query_embedding = self.embedding_service.encode_query(query)
            
            # Retrieve using hybrid search
            results = self.hybrid_retriever.retrieve(
                query_embedding=query_embedding,
                query_text=query,
                assessments_map=self.assessments_map,
                k=top_k
            )
            
            logger.info(f"Retrieved {len(results)} assessments for query: '{query[:50]}'")
            return results
            
        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            return []
    
    def retrieve_by_type(
        self,
        assessment_type: str,
        limit: int = 10
    ) -> List[CatalogEntry]:
        """
        Retrieve all assessments of a specific type.
        
        Args:
            assessment_type: Type filter (e.g., 'cognitive', 'personality')
            limit: Maximum results
            
        Returns:
            List of matching assessments
        """
        results = [
            assessment for assessment in self.assessments_map.values()
            if assessment.test_type.lower() == assessment_type.lower()
        ]
        
        return results[:limit]
    
    def rerank_results(
        self,
        query: str,
        candidates: List[CatalogEntry],
        top_k: int = 5
    ) -> List[CatalogEntry]:
        """
        Rerank candidate assessments for better relevance.
        
        Args:
            query: User query
            candidates: Initial candidate assessments
            top_k: Number to return
            
        Returns:
            Reranked assessments
        """
        if not candidates:
            return []
        
        try:
            # Encode query and candidates
            query_embedding = self.embedding_service.encode_query(query)
            
            # Score each candidate
            scores = []
            for candidate in candidates:
                # Combine text for embedding
                text = f"{candidate.name} {candidate.description} {candidate.skills}"
                candidate_embedding = self.embedding_service.encode_text(text)
                
                # Compute similarity
                similarity = EmbeddingService.cosine_similarity(
                    query_embedding,
                    candidate_embedding
                )
                
                scores.append((candidate, similarity))
            
            # Sort by score
            scores.sort(key=lambda x: x[1], reverse=True)
            
            # Return top-k
            return [candidate for candidate, _ in scores[:top_k]]
            
        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            return candidates[:top_k]
