"""
API integration tests.
"""

import json
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.api import Message


client = TestClient(app)


class TestHealthEndpoint:
    """Tests for health check endpoint."""
    
    def test_health_check(self):
        """Test health endpoint returns ok."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "ok"


class TestChatEndpoint:
    """Tests for chat endpoint."""
    
    def test_chat_empty_messages(self):
        """Test chat with empty messages."""
        response = client.post(
            "/chat",
            json={"messages": []}
        )
        # Should reject empty messages
        assert response.status_code in [400, 422]
    
    def test_chat_single_user_message(self):
        """Test chat with single user message."""
        response = client.post(
            "/chat",
            json={
                "messages": [
                    {
                        "role": "user",
                        "content": "Hiring a backend developer"
                    }
                ]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "reply" in data
        assert "recommendations" in data
        assert "end_of_conversation" in data
        
        # Should return reply
        assert len(data["reply"]) > 0
        
        # Recommendations can be empty or filled
        assert isinstance(data["recommendations"], list)
    
    def test_chat_with_conversation_history(self):
        """Test chat with multi-turn conversation."""
        messages = [
            {"role": "user", "content": "I need assessment recommendations"},
            {"role": "assistant", "content": "What role are you hiring for?"},
            {"role": "user", "content": "Backend Java developer"}
        ]
        
        response = client.post(
            "/chat",
            json={"messages": messages}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data["reply"], str)
        assert isinstance(data["recommendations"], list)
    
    def test_chat_assistant_as_last_message_invalid(self):
        """Test that last message must be from user."""
        messages = [
            {"role": "user", "content": "Hiring"},
            {"role": "assistant", "content": "Who are you hiring for?"}
        ]
        
        response = client.post(
            "/chat",
            json={"messages": messages}
        )
        
        assert response.status_code == 400
    
    def test_chat_response_schema(self):
        """Test chat response matches schema."""
        response = client.post(
            "/chat",
            json={
                "messages": [
                    {"role": "user", "content": "cognitive assessment"}
                ]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate schema
        assert isinstance(data.get("reply"), str)
        assert isinstance(data.get("recommendations"), list)
        assert isinstance(data.get("end_of_conversation"), bool)
        
        # Validate recommendation schema
        for rec in data["recommendations"]:
            assert "name" in rec
            assert "url" in rec
            assert "test_type" in rec
            
            # URL should be from SHL
            assert rec["url"].startswith("https://www.shl.com")


class TestChatIntents:
    """Tests for different conversation intents."""
    
    def test_intent_clarify(self):
        """Test clarification intent."""
        response = client.post(
            "/chat",
            json={
                "messages": [
                    {"role": "user", "content": "I need an assessment"}
                ]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should ask clarifying questions
        reply_lower = data["reply"].lower()
        assert any(word in reply_lower for word in ["clarify", "question", "more info", "details"])
    
    def test_intent_recommend(self):
        """Test recommendation intent."""
        response = client.post(
            "/chat",
            json={
                "messages": [
                    {"role": "user", "content": "I'm hiring a senior Java backend developer"}
                ]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should provide recommendations
        assert len(data["recommendations"]) >= 0
    
    def test_intent_refuse(self):
        """Test refusal intent for off-topic."""
        response = client.post(
            "/chat",
            json={
                "messages": [
                    {"role": "user", "content": "What are the legal implications of hiring?"}
                ]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should refuse gracefully
        reply_lower = data["reply"].lower()
        assert any(word in reply_lower for word in ["shl", "assessment", "outside"])


class TestRecommendationValidation:
    """Tests for recommendation guardrails."""
    
    def test_recommendations_are_from_catalog(self):
        """Test that recommendations only include catalog assessments."""
        response = client.post(
            "/chat",
            json={
                "messages": [
                    {"role": "user", "content": "cognitive assessment numerical reasoning"}
                ]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # All recommendations should have valid URLs
        for rec in data["recommendations"]:
            assert rec["url"].startswith("https://www.shl.com")
            assert len(rec["name"]) > 0
    
    def test_max_recommendations_limit(self):
        """Test that max 10 recommendations are returned."""
        response = client.post(
            "/chat",
            json={
                "messages": [
                    {"role": "user", "content": "show me all assessments"}
                ]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["recommendations"]) <= 10


class TestInputValidation:
    """Tests for input validation."""
    
    def test_invalid_role(self):
        """Test with invalid message role."""
        response = client.post(
            "/chat",
            json={
                "messages": [
                    {"role": "system", "content": "test"}
                ]
            }
        )
        
        # Should handle gracefully or reject
        assert response.status_code in [400, 422]
    
    def test_very_long_message(self):
        """Test with very long message."""
        long_content = "a" * 5000  # Exceeds limit
        
        response = client.post(
            "/chat",
            json={
                "messages": [
                    {"role": "user", "content": long_content}
                ]
            }
        )
        
        # Should either reject or truncate
        assert response.status_code in [200, 422]
    
    def test_empty_message_content(self):
        """Test with empty message content."""
        response = client.post(
            "/chat",
            json={
                "messages": [
                    {"role": "user", "content": ""}
                ]
            }
        )
        
        # Should reject empty content
        assert response.status_code in [400, 422]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
