"""
Catalog data models representing SHL assessments.
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class CatalogEntry(BaseModel):
    """A single SHL assessment in the catalog."""
    name: str = Field(
        ..., 
        description="Official name of the assessment"
    )
    url: str = Field(
        ..., 
        description="URL to the assessment on SHL website"
    )
    description: str = Field(
        ..., 
        description="Detailed description of what the assessment measures"
    )
    test_type: str = Field(
        ..., 
        description="Type of assessment (e.g., cognitive, personality, situational, ability, language)"
    )
    skills: str = Field(
        default="",
        description="Comma-separated list of skills or competencies measured"
    )
    duration: str = Field(
        default="",
        description="Typical duration to complete the assessment"
    )
    keywords: List[str] = Field(
        default_factory=list,
        description="Additional keywords for semantic search"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Situational Judgment Test (SJT)",
                "url": "https://www.shl.com/en/solutions/assessments/situational-judgment-test/",
                "description": "Measures behavioral competencies and decision-making ability in realistic workplace scenarios.",
                "test_type": "situational",
                "skills": "decision-making, leadership, teamwork, communication",
                "duration": "20-30 minutes",
                "keywords": ["behavioral", "judgment", "scenarios"]
            }
        }


class CatalogMetadata(BaseModel):
    """Metadata about the catalog."""
    total_entries: int = Field(..., description="Total number of assessments in the catalog")
    last_updated: str = Field(..., description="ISO 8601 timestamp of last update")
    version: str = Field(..., description="Catalog version")

    class Config:
        json_schema_extra = {
            "example": {
                "total_entries": 45,
                "last_updated": "2026-05-14T10:00:00Z",
                "version": "1.0.0"
            }
        }
