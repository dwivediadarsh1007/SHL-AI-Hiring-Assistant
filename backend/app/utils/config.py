"""
Configuration management for the SHL Assessment Recommender.
"""

import os
from functools import lru_cache
from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings from environment variables."""
    
    # API Configuration
    api_title: str = "SHL Assessment Recommender"
    api_version: str = "1.0.0"
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    
    # LLM Configuration
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    
    # Embedding Configuration
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384  # Dimension of all-MiniLM-L6-v2
    
    # Retrieval Configuration
    faiss_index_path: str = "vectorstore/shl_index.faiss"
    faiss_metadata_path: str = "vectorstore/metadata.json"
    catalog_path: str = "data/shl_catalog.json"
    
    # Retrieval Parameters
    retrieval_top_k: int = 10
    retrieval_rerank_top_k: int = 5
    
    # Conversation Parameters
    max_conversation_turns: int = 8  # Maximum turns (8 user + 8 assistant messages)
    response_timeout_seconds: int = 10
    
    # Feature Flags
    enable_hybrid_retrieval: bool = True
    enable_reranking: bool = True
    enable_hallucination_guards: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
