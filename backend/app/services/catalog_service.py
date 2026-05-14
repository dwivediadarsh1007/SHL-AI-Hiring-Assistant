"""
Service for loading and managing the SHL assessment catalog.

Provides read-only access to the catalog with caching and validation.
"""

import json
import logging
from typing import List, Optional
from pathlib import Path

from app.models.catalog import CatalogEntry, CatalogMetadata


logger = logging.getLogger(__name__)


class CatalogService:
    """
    Manages loading, caching, and accessing the SHL catalog.
    
    Ensures that:
    - Catalog is loaded once and cached in memory
    - All entries are valid CatalogEntry instances
    - Metadata is tracked and accessible
    """
    
    def __init__(self, catalog_path: str = "data/shl_catalog.json"):
        """
        Initialize catalog service.
        
        Args:
            catalog_path: Path to catalog JSON file
        """
        self.catalog_path = Path(catalog_path)
        self.catalog: List[CatalogEntry] = []
        self.metadata: Optional[CatalogMetadata] = None
        self.loaded = False
    
    def load(self) -> bool:
        """
        Load catalog from JSON file.
        
        Returns:
            True if loading was successful
        """
        if self.loaded:
            logger.debug("Catalog already loaded, skipping reload")
            return True
        
        try:
            if not self.catalog_path.exists():
                logger.error(f"Catalog file not found: {self.catalog_path}")
                return False
            
            with open(self.catalog_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Load metadata
            metadata_dict = data.get("metadata", {})
            self.metadata = CatalogMetadata(**metadata_dict) if metadata_dict else None
            
            # Load assessments
            assessments_list = data.get("assessments", [])
            self.catalog = []
            
            for assessment_dict in assessments_list:
                try:
                    entry = CatalogEntry(**assessment_dict)
                    self.catalog.append(entry)
                except Exception as e:
                    logger.warning(f"Skipped invalid catalog entry: {e}")
            
            self.loaded = True
            logger.info(f"Loaded {len(self.catalog)} assessments from {self.catalog_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load catalog: {e}")
            return False
    
    def get_all(self) -> List[CatalogEntry]:
        """
        Get all catalog entries.
        
        Returns:
            List of all assessments
        """
        if not self.loaded:
            self.load()
        
        return self.catalog
    
    def get_by_name(self, name: str) -> Optional[CatalogEntry]:
        """
        Get assessment by exact name.
        
        Args:
            name: Assessment name
            
        Returns:
            CatalogEntry or None if not found
        """
        if not self.loaded:
            self.load()
        
        for entry in self.catalog:
            if entry.name.lower() == name.lower():
                return entry
        
        return None
    
    def get_by_url(self, url: str) -> Optional[CatalogEntry]:
        """
        Get assessment by URL.
        
        Args:
            url: Assessment URL
            
        Returns:
            CatalogEntry or None if not found
        """
        if not self.loaded:
            self.load()
        
        url_normalized = url.lower().strip()
        for entry in self.catalog:
            if entry.url.lower() == url_normalized:
                return entry
        
        return None
    
    def get_by_type(self, test_type: str) -> List[CatalogEntry]:
        """
        Get all assessments of a specific type.
        
        Args:
            test_type: Type of assessment
            
        Returns:
            List of matching assessments
        """
        if not self.loaded:
            self.load()
        
        return [
            entry for entry in self.catalog
            if entry.test_type.lower() == test_type.lower()
        ]
    
    def search_by_skill(self, skill: str) -> List[CatalogEntry]:
        """
        Search assessments by skill keyword.
        
        Args:
            skill: Skill to search for
            
        Returns:
            List of matching assessments
        """
        if not self.loaded:
            self.load()
        
        skill_lower = skill.lower()
        results = []
        
        for entry in self.catalog:
            if skill_lower in entry.skills.lower():
                results.append(entry)
        
        return results
    
    def search_by_keyword(self, keyword: str) -> List[CatalogEntry]:
        """
        Search assessments by keyword.
        
        Args:
            keyword: Keyword to search for
            
        Returns:
            List of matching assessments
        """
        if not self.loaded:
            self.load()
        
        keyword_lower = keyword.lower()
        results = []
        
        for entry in self.catalog:
            # Search in name, description, skills, keywords
            if (keyword_lower in entry.name.lower() or
                keyword_lower in entry.description.lower() or
                keyword_lower in entry.skills.lower() or
                any(keyword_lower in k.lower() for k in entry.keywords)):
                results.append(entry)
        
        return results
    
    def validate_all(self) -> bool:
        """
        Validate all catalog entries have required fields.
        
        Returns:
            True if all entries are valid
        """
        if not self.loaded:
            self.load()
        
        for i, entry in enumerate(self.catalog):
            try:
                # Validation happens during instantiation
                # Just check that required fields are non-empty
                assert entry.name, f"Entry {i}: missing name"
                assert entry.url, f"Entry {i}: missing url"
                assert entry.description, f"Entry {i}: missing description"
                assert entry.test_type, f"Entry {i}: missing test_type"
            except AssertionError as e:
                logger.error(f"Validation failed: {e}")
                return False
        
        logger.info(f"✓ All {len(self.catalog)} entries validated successfully")
        return True
    
    def get_metadata(self) -> Optional[CatalogMetadata]:
        """
        Get catalog metadata.
        
        Returns:
            CatalogMetadata or None
        """
        if not self.loaded:
            self.load()
        
        return self.metadata
