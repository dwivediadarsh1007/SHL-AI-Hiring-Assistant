"""
Script to build FAISS index from catalog.

Usage:
    python scripts/build_faiss_index.py
"""

import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.catalog_service import CatalogService
from app.services.retrieval_service import RetrievalService


def main():
    """Build FAISS index from catalog."""
    print("=" * 60)
    print("SHL Assessment FAISS Index Builder")
    print("=" * 60)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Load catalog
    print("\n[1] Loading catalog...")
    catalog_service = CatalogService("data/shl_catalog.json")
    
    if not catalog_service.load():
        print("✗ Failed to load catalog")
        return 1
    
    assessments = catalog_service.get_all()
    print(f"✓ Loaded {len(assessments)} assessments")
    
    # Build index
    print("\n[2] Building FAISS index...")
    retrieval_service = RetrievalService()
    
    if not retrieval_service.build_index(assessments):
        print("✗ Failed to build index")
        return 1
    
    print(f"✓ Index built successfully")
    
    # Test retrieval
    print("\n[3] Testing retrieval...")
    test_queries = [
        "cognitive reasoning test",
        "personality assessment",
        "situational judgment",
        "Java developer skills"
    ]
    
    for query in test_queries:
        results = retrieval_service.retrieve(query, top_k=3)
        print(f"\n  Query: '{query}'")
        for i, result in enumerate(results, 1):
            print(f"    {i}. {result.name} ({result.test_type})")
    
    print("\n" + "=" * 60)
    print("✓ Index build complete")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
