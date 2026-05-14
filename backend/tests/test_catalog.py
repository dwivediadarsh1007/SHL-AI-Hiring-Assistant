"""
Unit tests for scraper and catalog loading.
"""

import json
import tempfile
from pathlib import Path

import pytest

from app.services.scraper import SHLScraper, create_sample_catalog
from app.services.catalog_service import CatalogService
from app.models.catalog import CatalogEntry


class TestScraper:
    """Tests for SHL scraper."""
    
    def test_scraper_initialization(self):
        """Test scraper can be initialized."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "catalog.json"
            scraper = SHLScraper(output_path=str(output_path))
            assert scraper.output_path == output_path
            assert scraper.catalog == []
            assert scraper.seen_urls == set()
    
    def test_url_validation(self):
        """Test URL validation."""
        scraper = SHLScraper()
        
        # Valid URLs
        assert scraper._is_valid_url("https://www.shl.com/assessments/")
        assert scraper._is_valid_url("https://shl.com/solutions/")
        
        # Invalid URLs
        assert not scraper._is_valid_url("https://example.com/shl")
        assert not scraper._is_valid_url("invalid_url")
        assert not scraper._is_valid_url("ftp://shl.com/")
    
    def test_create_sample_catalog(self):
        """Test sample catalog creation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "catalog.json"
            success = create_sample_catalog(str(output_path))
            
            assert success
            assert output_path.exists()
            
            # Verify file structure
            with open(output_path) as f:
                data = json.load(f)
            
            assert "metadata" in data
            assert "assessments" in data
            assert len(data["assessments"]) > 0


class TestCatalogService:
    """Tests for catalog service."""
    
    def test_catalog_loading(self):
        """Test catalog loads from JSON."""
        service = CatalogService("data/shl_catalog.json")
        assert service.load()
        assert len(service.catalog) > 0
        assert service.loaded
    
    def test_get_all(self):
        """Test getting all catalog entries."""
        service = CatalogService("data/shl_catalog.json")
        catalog = service.get_all()
        assert len(catalog) > 0
        assert all(isinstance(entry, CatalogEntry) for entry in catalog)
    
    def test_get_by_name(self):
        """Test getting assessment by name."""
        service = CatalogService("data/shl_catalog.json")
        entry = service.get_by_name("Numerical Reasoning Test")
        
        assert entry is not None
        assert entry.name == "Numerical Reasoning Test"
        assert entry.test_type == "cognitive"
    
    def test_get_by_type(self):
        """Test filtering by assessment type."""
        service = CatalogService("data/shl_catalog.json")
        
        cognitive = service.get_by_type("cognitive")
        assert len(cognitive) > 0
        assert all(e.test_type == "cognitive" for e in cognitive)
        
        personality = service.get_by_type("personality")
        assert len(personality) > 0
    
    def test_search_by_skill(self):
        """Test searching by skill."""
        service = CatalogService("data/shl_catalog.json")
        
        results = service.search_by_skill("reasoning")
        assert len(results) > 0
    
    def test_search_by_keyword(self):
        """Test searching by keyword."""
        service = CatalogService("data/shl_catalog.json")
        
        results = service.search_by_keyword("reasoning")
        assert len(results) > 0
    
    def test_validate_all(self):
        """Test catalog validation."""
        service = CatalogService("data/shl_catalog.json")
        assert service.validate_all()


class TestCatalogEntry:
    """Tests for catalog entry model."""
    
    def test_entry_creation(self):
        """Test creating a valid catalog entry."""
        entry = CatalogEntry(
            name="Test Assessment",
            url="https://www.shl.com/test/",
            description="Test description",
            test_type="cognitive",
            skills="reasoning, problem-solving",
            duration="20 minutes",
            keywords=["test", "reasoning"]
        )
        
        assert entry.name == "Test Assessment"
        assert entry.test_type == "cognitive"
        assert "reasoning" in entry.skills
    
    def test_entry_with_defaults(self):
        """Test entry with default values."""
        entry = CatalogEntry(
            name="Minimal Assessment",
            url="https://www.shl.com/minimal/",
            description="Minimal entry"
        )
        
        assert entry.name == "Minimal Assessment"
        assert entry.test_type == ""
        assert entry.skills == ""
        assert entry.keywords == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
