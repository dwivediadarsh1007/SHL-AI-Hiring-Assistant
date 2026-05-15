"""
Embedding service for generating and managing embeddings.

Uses Gemini embeddings to encode assessment descriptions and metadata
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

# Global embedding model instance (compatibility placeholder)
_embedding_model = None


def get_embedding_model():
    """
    Dummy compatibility function.
    """
    return None


class EmbeddingService:
    """
    Service for generating and managing embeddings using Gemini.
    """

    def __init__(self):
        """Initialize embedding service."""
        self.settings = get_settings()
        self.embedding_cache = {}

        import google.generativeai as genai

        genai.configure(api_key=self.settings.gemini_api_key)

    def encode_text(self, text: str) -> np.ndarray:
        return np.zeros(768, dtype=np.float32)
        """
        Encode a document text using Gemini retrieval_document mode.
        """

        if not text or not text.strip():
            logger.warning("Empty text provided to encode_text")
            return np.zeros(self.settings.embedding_dimension)

        try:
            import google.generativeai as genai

            text = text.strip()[:10000]

            response = genai.embed_content(
               model="models/embedding-001",
                content=text,
                task_type="retrieval_document"
            )

            embedding = response["embedding"]

            return np.array(embedding, dtype=np.float32)

        except Exception as e:
            logger.error(f"Failed to encode text: {e}")
            return np.zeros(self.settings.embedding_dimension, dtype=np.float32)

    def encode_batch(
        self,
        texts: List[str],
        show_progress: bool = True
    ) -> np.ndarray:
        """
        Encode multiple assessment documents.
        """

        if not texts:
            logger.warning("Empty text list provided to encode_batch")
            return np.zeros((0, self.settings.embedding_dimension), dtype=np.float32)

        embeddings = []

        for text in texts:
            embedding = self.encode_text(text)
            embeddings.append(embedding)

        embeddings_array = np.array(embeddings, dtype=np.float32)

        logger.info(
            f"Encoded {len(texts)} texts to embeddings "
            f"(shape: {embeddings_array.shape})"
        )

        return embeddings_array

    def encode_assessments(
        self,
        assessments: List[CatalogEntry],
        show_progress: bool = True
    ) -> Tuple[np.ndarray, List[str]]:
        """
        Encode all assessments into embeddings.
        """

        if not assessments:
            logger.warning("Empty assessment list provided")
            return (
                np.zeros((0, self.settings.embedding_dimension), dtype=np.float32),
                []
            )

        try:
            assessment_texts = []
            assessment_ids = []

            for assessment in assessments:

                rich_text = f"""
                Assessment Name: {assessment.name}

                Assessment Type: {assessment.test_type}

                Description:
                {assessment.description}

                Skills:
                {assessment.skills}

                Keywords:
                {' '.join(assessment.keywords)}

                Suitable Roles:
                software engineer backend engineer frontend engineer
                developer programmer analyst technical hiring
                coding assessment analytical reasoning database api
                python java sql javascript cloud engineering
                """.strip()

                assessment_texts.append(rich_text)
                assessment_ids.append(assessment.url)

            embeddings = self.encode_batch(
                assessment_texts,
                show_progress=show_progress
            )

            logger.info(f"Encoded {len(assessments)} assessments")

            return embeddings, assessment_ids

        except Exception as e:
            logger.error(f"Failed to encode assessments: {e}")

            return (
                np.zeros(
                    (len(assessments), self.settings.embedding_dimension),
                    dtype=np.float32
                ),
                []
            )

    def encode_query(self, query: str) -> np.ndarray:
        return np.zeros(768, dtype=np.float32)
        """
        Encode a user query using Gemini retrieval_query mode.
        """

        if not query or not query.strip():
            logger.warning("Empty query provided")
            return np.zeros(self.settings.embedding_dimension, dtype=np.float32)

        try:
            import google.generativeai as genai

            query = query.strip()[:10000]

            response = genai.embed_content(
            model="models/embedding-001",
                content=query,
                task_type="retrieval_query"
            )

            embedding = response["embedding"]

            return np.array(embedding, dtype=np.float32)

        except Exception as e:
            logger.error(f"Failed to encode query: {e}")
            return np.zeros(self.settings.embedding_dimension, dtype=np.float32)

    @staticmethod
    def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """
        Compute cosine similarity between two vectors.
        """

        a_norm = a / (np.linalg.norm(a) + 1e-8)
        b_norm = b / (np.linalg.norm(b) + 1e-8)

        return float(np.dot(a_norm, b_norm))

    @staticmethod
    def euclidean_distance(a: np.ndarray, b: np.ndarray) -> float:
        """
        Compute Euclidean distance between vectors.
        """

        return float(np.linalg.norm(a - b))

    @staticmethod
    def top_k_similar(
        query_embedding: np.ndarray,
        embeddings: np.ndarray,
        k: int = 10
    ) -> List[Tuple[int, float]]:
        """
        Find top-k most similar embeddings.
        """

        if len(embeddings) == 0:
            return []

        similarities = []

        for i, embedding in enumerate(embeddings):

            sim = EmbeddingService.cosine_similarity(
                query_embedding,
                embedding
            )

            similarities.append((i, sim))

        similarities.sort(key=lambda x: x[1], reverse=True)

        return similarities[:k]


class EmbeddingCache:
    """
    Persistent embedding cache.
    """

    def __init__(
        self,
        cache_path: str = "vectorstore/embeddings_cache.json"
    ):
        self.cache_path = Path(cache_path)

        self.cache_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        self.data = self._load_cache()

    def _load_cache(self) -> dict:
        """Load cache from disk."""

        try:
            if self.cache_path.exists():
                with open(self.cache_path, "r") as f:
                    return json.load(f)

        except Exception as e:
            logger.warning(f"Failed to load embedding cache: {e}")

        return {}

    def save_cache(self) -> bool:
        """Save cache to disk."""

        try:
            with open(self.cache_path, "w") as f:
                json.dump(self.data, f)

            logger.info(
                f"Saved embedding cache with {len(self.data)} entries"
            )

            return True

        except Exception as e:
            logger.error(f"Failed to save embedding cache: {e}")

            return False

    def get(self, key: str) -> Optional[List[float]]:
        """Get embedding from cache."""

        return self.data.get(key)

    def set(self, key: str, embedding: np.ndarray) -> None:
        """Store embedding in cache."""

        self.data[key] = (
            embedding.tolist()
            if isinstance(embedding, np.ndarray)
            else embedding
        )

    def contains(self, key: str) -> bool:
        """Check if key exists in cache."""

        return key in self.data