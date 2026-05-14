"""
API request and response schemas for the SHL Assessment Recommender.
"""

from typing import List, Literal
from pydantic import BaseModel, Field


class Message(BaseModel):
    """A single message in the conversation history."""
    role: Literal["user", "assistant"] = Field(
        ..., description="Role of the message sender: 'user' or 'assistant'"
    )
    content: str = Field(
        ..., description="Content of the message", min_length=1, max_length=2000
    )


class ChatRequest(BaseModel):
    """Request payload for the /chat endpoint."""
    messages: List[Message] = Field(
        ..., 
        description="Conversation history in chronological order",
        min_items=1,
        max_items=16  # Max 8 turns = 16 messages (user + assistant pairs)
    )

    class Config:
        json_schema_extra = {
            "example": {
                "messages": [
                    {
                        "role": "user",
                        "content": "Hiring a Java developer"
                    }
                ]
            }
        }


class AssessmentRecommendation(BaseModel):
    """A recommended SHL assessment."""
    name: str = Field(
        ..., description="Official name of the SHL assessment"
    )
    url: str = Field(
        ..., description="Valid SHL catalog URL"
    )
    test_type: str = Field(
        ..., description="Type of assessment (e.g., 'cognitive', 'personality', 'situational')"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Situational Judgment Test (SJT)",
                "url": "https://www.shl.com/en/solutions/assessments/situational-judgment-test/",
                "test_type": "situational"
            }
        }


class ChatResponse(BaseModel):
    """Response payload for the /chat endpoint."""
    reply: str = Field(
        ..., 
        description="Conversational response from the agent",
        min_length=1,
        max_length=2000
    )
    recommendations: List[AssessmentRecommendation] = Field(
        default_factory=list,
        description="List of recommended SHL assessments (max 10)",
        max_items=10
    )
    end_of_conversation: bool = Field(
        default=False,
        description="Flag indicating if the conversation should end"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "reply": "Based on your needs, I recommend these assessments for backend developers.",
                "recommendations": [
                    {
                        "name": "Situational Judgment Test (SJT)",
                        "url": "https://www.shl.com/en/solutions/assessments/situational-judgment-test/",
                        "test_type": "situational"
                    }
                ],
                "end_of_conversation": False
            }
        }


class HealthResponse(BaseModel):
    """Response payload for the /health endpoint."""
    status: Literal["ok"] = Field(..., description="Health status")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "ok"
            }
        }
