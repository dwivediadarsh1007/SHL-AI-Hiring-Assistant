"""
Script to validate and inspect the SHL catalog.

Usage:
    python scripts/validate_catalog.py
"""

import sys
import json
from pathlib import Path

# Add parent directory to path (project root)
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.catalog_service import CatalogService


def main():
    """Validate and display catalog information."""
    print("=" * 60)
    print("SHL Assessment Catalog Validator")
    print("=" * 60)
    
    service = CatalogService("data/shl_catalog.json")
    
    # Load catalog
    print("\n[1] Loading catalog...")
    if not service.load():
        print("✗ Failed to load catalog")
        return 1
    
    print(f"✓ Loaded {len(service.catalog)} assessments")
    
    # Validate catalog
    print("\n[2] Validating catalog...")
    if not service.validate_all():
        print("✗ Validation failed")
        return 1
    
    print("✓ All entries are valid")
    
    # Display metadata
    metadata = service.get_metadata()
    print("\n[3] Catalog Metadata:")
    print(f"   Total entries: {metadata.total_entries}")
    print(f"   Last updated: {metadata.last_updated}")
    print(f"   Version: {metadata.version}")
    
    # Display entries
    print("\n[4] Assessment Catalog:")
    print("-" * 60)
    
    for i, entry in enumerate(service.get_all(), 1):
        print(f"\n{i}. {entry.name}")
        print(f"   Type: {entry.test_type}")
        print(f"   Duration: {entry.duration}")
        print(f"   Skills: {entry.skills}")
        print(f"   URL: {entry.url}")
    
    # Test search
    print("\n[5] Testing Search Functions:")
    print("-" * 60)
    
    # Search by type
    cognitive = service.get_by_type("cognitive")
    print(f"\nCognitive assessments: {len(cognitive)}")
    for entry in cognitive:
        print(f"  - {entry.name}")
    
    # Search by skill
    decision_making = service.search_by_skill("decision")
    print(f"\nAssessments with 'decision' skill: {len(decision_making)}")
    for entry in decision_making:
        print(f"  - {entry.name}")
    
    # Search by keyword
    personality_tests = service.search_by_keyword("personality")
    print(f"\nAssessments with 'personality' keyword: {len(personality_tests)}")
    for entry in personality_tests:
        print(f"  - {entry.name}")
    
    print("\n" + "=" * 60)
    print("✓ Catalog validation complete")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
