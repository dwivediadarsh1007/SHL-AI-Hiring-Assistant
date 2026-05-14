"""
Intent types and classification for the dialog manager.
"""

from enum import Enum
from typing import List
from pydantic import BaseModel, Field


class IntentType(str, Enum):
    """Supported conversation intents."""
    CLARIFY = "clarify"
    RECOMMEND = "recommend"
    REFINE = "refine"
    COMPARE = "compare"
    REFUSE = "refuse"


class IntentDetection(BaseModel):
    """Result of intent detection from conversation history."""
    intent: IntentType = Field(
        ..., 
        description="Detected intent of the current user message"
    )
    confidence: float = Field(
        ...,
        description="Confidence score between 0 and 1",
        ge=0.0,
        le=1.0
    )
    clarification_needed: List[str] = Field(
        default_factory=list,
        description="List of clarification questions if intent is CLARIFY"
    )
    hiring_constraints: dict = Field(
        default_factory=dict,
        description="Extracted hiring constraints from conversation history"
    )
    comparison_items: List[str] = Field(
        default_factory=list,
        description="Assessment names to compare if intent is COMPARE"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "intent": "recommend",
                "confidence": 0.95,
                "clarification_needed": [],
                "hiring_constraints": {
                    "role": "backend developer",
                    "level": "mid-level",
                    "tech_stack": ["Java"]
                },
                "comparison_items": []
            }
        }
