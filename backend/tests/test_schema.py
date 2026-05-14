"""
Tests for API schema validation.
"""

import pytest

from app.models.api import (
    Message, ChatRequest, ChatResponse,
    AssessmentRecommendation, HealthResponse
)


class TestMessageModel:
    """Tests for Message model."""
    
    def test_valid_user_message(self):
        """Test valid user message."""
        msg = Message(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
    
    def test_valid_assistant_message(self):
        """Test valid assistant message."""
        msg = Message(role="assistant", content="Hi there")
        assert msg.role == "assistant"
    
    def test_invalid_role(self):
        """Test invalid role."""
        with pytest.raises(ValueError):
            Message(role="invalid", content="test")
    
    def test_empty_content_invalid(self):
        """Test empty content fails."""
        with pytest.raises(ValueError):
            Message(role="user", content="")


class TestChatRequest:
    """Tests for ChatRequest model."""
    
    def test_valid_request(self):
        """Test valid request."""
        req = ChatRequest(messages=[
            Message(role="user", content="Hello")
        ])
        assert len(req.messages) == 1
    
    def test_max_messages(self):
        """Test maximum messages limit."""
        messages = [
            Message(role="user" if i % 2 == 0 else "assistant", content="msg")
            for i in range(16)
        ]
        req = ChatRequest(messages=messages)
        assert len(req.messages) == 16
    
    def test_exceed_max_messages(self):
        """Test exceeding message limit."""
        messages = [
            Message(role="user" if i % 2 == 0 else "assistant", content="msg")
            for i in range(17)  # More than max
        ]
        with pytest.raises(ValueError):
            ChatRequest(messages=messages)
    
    def test_empty_request(self):
        """Test empty request fails."""
        with pytest.raises(ValueError):
            ChatRequest(messages=[])


class TestAssessmentRecommendation:
    """Tests for AssessmentRecommendation model."""
    
    def test_valid_recommendation(self):
        """Test valid recommendation."""
        rec = AssessmentRecommendation(
            name="Numerical Test",
            url="https://www.shl.com/test/",
            test_type="cognitive"
        )
        assert rec.name == "Numerical Test"
        assert rec.url == "https://www.shl.com/test/"
    
    def test_missing_name(self):
        """Test missing name."""
        with pytest.raises(ValueError):
            AssessmentRecommendation(
                name="",
                url="https://www.shl.com/",
                test_type="cognitive"
            )
    
    def test_missing_url(self):
        """Test missing URL."""
        with pytest.raises(ValueError):
            AssessmentRecommendation(
                name="Test",
                url="",
                test_type="cognitive"
            )


class TestChatResponse:
    """Tests for ChatResponse model."""
    
    def test_valid_response(self):
        """Test valid response."""
        resp = ChatResponse(
            reply="Here are recommendations",
            recommendations=[],
            end_of_conversation=False
        )
        assert resp.reply == "Here are recommendations"
        assert len(resp.recommendations) == 0
    
    def test_with_recommendations(self):
        """Test response with recommendations."""
        resp = ChatResponse(
            reply="Recommendations:",
            recommendations=[
                AssessmentRecommendation(
                    name="Test 1",
                    url="https://www.shl.com/1/",
                    test_type="cognitive"
                )
            ],
            end_of_conversation=False
        )
        assert len(resp.recommendations) == 1
    
    def test_max_recommendations(self):
        """Test maximum recommendations."""
        recommendations = [
            AssessmentRecommendation(
                name=f"Test {i}",
                url=f"https://www.shl.com/{i}/",
                test_type="cognitive"
            )
            for i in range(10)
        ]
        resp = ChatResponse(
            reply="Test",
            recommendations=recommendations,
            end_of_conversation=False
        )
        assert len(resp.recommendations) == 10
    
    def test_exceed_max_recommendations(self):
        """Test exceeding max recommendations."""
        recommendations = [
            AssessmentRecommendation(
                name=f"Test {i}",
                url=f"https://www.shl.com/{i}/",
                test_type="cognitive"
            )
            for i in range(11)
        ]
        with pytest.raises(ValueError):
            ChatResponse(
                reply="Test",
                recommendations=recommendations,
                end_of_conversation=False
            )


class TestHealthResponse:
    """Tests for HealthResponse model."""
    
    def test_valid_health_response(self):
        """Test valid health response."""
        resp = HealthResponse(status="ok")
        assert resp.status == "ok"
    
    def test_invalid_status(self):
        """Test invalid status."""
        with pytest.raises(ValueError):
            HealthResponse(status="error")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
