"""
Guardrails to prevent hallucination, prompt injection, and invalid outputs.

Validates all agent outputs against the SHL catalog before responding.
"""

import json
import logging
import re
from typing import List, Dict, Optional, Tuple

from app.models.catalog import CatalogEntry
from app.models.api import AssessmentRecommendation, ChatResponse
from app.utils.validation import validate_shl_url, is_prompt_injection_attempt


logger = logging.getLogger(__name__)


class HallucinationGuard:
    """
    Prevents recommending non-existent assessments.
    
    Validates that all recommendations exist in the SHL catalog.
    """
    
    def __init__(self, catalog_entries: List[CatalogEntry]):
        """
        Initialize guard with catalog.
        
        Args:
            catalog_entries: List of valid SHL assessments
        """
        self.valid_names = {entry.name.lower(): entry for entry in catalog_entries}
        self.valid_urls = {entry.url.lower(): entry for entry in catalog_entries}
        self.catalog_entries = catalog_entries
    
    def validate_recommendation(self, name: str, url: str) -> Tuple[bool, Optional[CatalogEntry]]:
        """
        Validate that a recommendation exists in catalog.
        
        Args:
            name: Assessment name
            url: Assessment URL
            
        Returns:
            Tuple of (is_valid, catalog_entry or None)
        """
        # Check URL first (most reliable)
        if url.lower() in self.valid_urls:
            entry = self.valid_urls[url.lower()]
            
            # Verify name matches
            if entry.name.lower() == name.lower():
                return True, entry
            else:
                logger.warning(f"Name mismatch for URL {url}: got '{name}', expected '{entry.name}'")
                return False, None
        
        # Fallback: check by name
        if name.lower() in self.valid_names:
            entry = self.valid_names[name.lower()]
            logger.warning(f"Resolved by name only (URL mismatch): {name}")
            return True, entry
        
        # Not in catalog
        logger.error(f"Hallucination detected: {name} ({url}) not in catalog")
        return False, None
    
    def validate_recommendations(
        self, 
        recommendations: List[Dict[str, str]]
    ) -> Tuple[List[AssessmentRecommendation], List[str]]:
        """
        Validate a list of recommendations.
        
        Args:
            recommendations: List of recommendation dicts
            
        Returns:
            Tuple of (valid_recommendations, error_messages)
        """
        valid = []
        errors = []
        
        for rec in recommendations:
            try:
                name = rec.get("name", "").strip()
                url = rec.get("url", "").strip()
                test_type = rec.get("test_type", "").strip()
                
                # Validate fields exist
                if not name:
                    errors.append("Missing assessment name")
                    continue
                
                if not url:
                    errors.append(f"Missing URL for {name}")
                    continue
                
                # Check against catalog
                is_valid, entry = self.validate_recommendation(name, url)
                
                if not is_valid:
                    errors.append(f"Assessment not in SHL catalog: {name}")
                    continue
                
                # Use catalog data for consistency
                valid.append(AssessmentRecommendation(
                    name=entry.name,
                    url=entry.url,
                    test_type=entry.test_type or test_type
                ))
                
            except Exception as e:
                errors.append(f"Invalid recommendation format: {e}")
        
        return valid, errors


class PromptInjectionGuard:
    """
    Detects and prevents prompt injection attacks in user input.
    """
    
    # Patterns that indicate injection attempts
    INJECTION_PATTERNS = [
        r"ignore.*prompt",
        r"system.*message",
        r"act as.*",
        r"pretend.*to be",
        r"disregard.*instruction",
        r"override.*instruction",
        r"hidden.*instruction",
        r"jailbreak",
        r"bypass.*filter",
        r"forget.*context",
        r"new.*prompt",
        r"switch.*mode"
    ]
    
    @staticmethod
    def detect_injection(text: str) -> Tuple[bool, Optional[str]]:
        """
        Detect prompt injection attempt.
        
        Args:
            text: User input to check
            
        Returns:
            Tuple of (is_injection, reason)
        """
        if is_prompt_injection_attempt(text):
            return True, "Potential prompt injection detected"
        
        # Check for suspicious patterns
        text_lower = text.lower()
        for pattern in PromptInjectionGuard.INJECTION_PATTERNS:
            if re.search(pattern, text_lower):
                return True, f"Suspicious pattern detected: {pattern}"
        
        return False, None
    
    @staticmethod
    def sanitize_context(text: str) -> str:
        """
        Sanitize context to prevent injection.
        
        Args:
            text: Text to sanitize
            
        Returns:
            Sanitized text
        """
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # Limit length
        text = text[:2000]
        
        # Normalize whitespace
        text = ' '.join(text.split())
        
        return text


class SchemaGuard:
    """
    Validates response schemas before returning to client.
    """
    
    @staticmethod
    def validate_chat_response(response: Dict) -> Tuple[bool, ChatResponse, List[str]]:
        """
        Validate chat response format.
        
        Args:
            response: Response dict to validate
            
        Returns:
            Tuple of (is_valid, validated_response, errors)
        """
        errors = []
        
        try:
            # Extract fields
            reply = response.get("reply", "").strip()
            recommendations = response.get("recommendations", [])
            end_of_conversation = response.get("end_of_conversation", False)
            
            # Validate reply
            if not reply:
                errors.append("Reply is empty")
                reply = "I couldn't generate a response. Please try again."
            
            if len(reply) > 2000:
                errors.append("Reply exceeds 2000 characters")
                reply = reply[:2000]
            
            # Validate recommendations
            if not isinstance(recommendations, list):
                errors.append("Recommendations must be a list")
                recommendations = []
            
            if len(recommendations) > 10:
                errors.append(f"Too many recommendations ({len(recommendations)}, max 10)")
                recommendations = recommendations[:10]
            
            # Validate end_of_conversation flag
            if not isinstance(end_of_conversation, bool):
                errors.append("end_of_conversation must be boolean")
                end_of_conversation = False
            
            # Build validated response
            validated = ChatResponse(
                reply=reply,
                recommendations=recommendations,
                end_of_conversation=end_of_conversation
            )
            
            is_valid = len(errors) == 0
            return is_valid, validated, errors
            
        except Exception as e:
            return False, None, [f"Schema validation failed: {e}"]
    
    @staticmethod
    def validate_json_format(text: str) -> Tuple[bool, Optional[Dict]]:
        """
        Validate that response is valid JSON.
        
        Args:
            text: Text to validate as JSON
            
        Returns:
            Tuple of (is_valid_json, parsed_dict)
        """
        try:
            # Try to parse as JSON
            data = json.loads(text)
            
            # Validate structure
            if not isinstance(data, dict):
                return False, None
            
            if "reply" not in data or "recommendations" not in data:
                return False, None
            
            return True, data
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON: {e}")
            return False, None


class URLGuard:
    """
    Validates all URLs in recommendations.
    """
    
    @staticmethod
    def validate_url_format(url: str) -> bool:
        """
        Validate URL format and domain.
        
        Args:
            url: URL to validate
            
        Returns:
            True if valid SHL URL
        """
        if not url or not isinstance(url, str):
            return False
        
        # Must start with https
        if not url.startswith("https://"):
            logger.warning(f"URL does not use HTTPS: {url}")
            return False
        
        # Must be SHL domain
        if not validate_shl_url(url):
            logger.warning(f"URL not from SHL domain: {url}")
            return False
        
        return True
    
    @staticmethod
    def sanitize_urls(recommendations: List[AssessmentRecommendation]) -> List[AssessmentRecommendation]:
        """
        Sanitize and validate URLs in recommendations.
        
        Args:
            recommendations: Recommendations to sanitize
            
        Returns:
            List with validated URLs
        """
        sanitized = []
        
        for rec in recommendations:
            if URLGuard.validate_url_format(rec.url):
                sanitized.append(rec)
            else:
                logger.error(f"Invalid URL in recommendation: {rec.url}")
        
        return sanitized


class GuardrailManager:
    """
    Orchestrates all guardrails for comprehensive validation.
    """
    
    def __init__(self, catalog_entries: List[CatalogEntry]):
        """
        Initialize all guardrails.
        
        Args:
            catalog_entries: Catalog for hallucination detection
        """
        self.hallucination_guard = HallucinationGuard(catalog_entries)
        self.injection_guard = PromptInjectionGuard()
        self.schema_guard = SchemaGuard()
        self.url_guard = URLGuard()
        self.catalog_entries = catalog_entries
    
    def validate_user_input(self, user_input: str) -> Tuple[bool, Optional[str]]:
        """
        Validate user input for injections and safety.
        
        Args:
            user_input: User message
            
        Returns:
            Tuple of (is_safe, error_message)
        """
        # Check for injection
        is_injection, reason = self.injection_guard.detect_injection(user_input)
        if is_injection:
            logger.warning(f"Injection attempt detected: {reason}")
            return False, "Your message appears to contain suspicious content."
        
        return True, None
    
    def validate_agent_response(self, response_dict: Dict) -> Tuple[bool, Optional[ChatResponse], List[str]]:
        """
        Comprehensively validate agent response.
        
        Args:
            response_dict: Response from LLM
            
        Returns:
            Tuple of (is_valid, validated_response, error_list)
        """
        errors = []
        
        try:
            # Validate JSON format
            is_json_valid, parsed = self.schema_guard.validate_json_format(json.dumps(response_dict) if isinstance(response_dict, dict) else response_dict)
            if not is_json_valid:
                errors.append("Invalid JSON structure")
                return False, None, errors
            
            # Validate schema
            is_schema_valid, chat_response, schema_errors = self.schema_guard.validate_chat_response(parsed)
            errors.extend(schema_errors)
            
            # Validate hallucination
            validated_recs = []
            for rec in (chat_response.recommendations if chat_response else []):
                is_real, catalog_entry = self.hallucination_guard.validate_recommendation(rec.name, rec.url)
                
                if not is_real:
                    errors.append(f"Hallucinated assessment: {rec.name}")
                else:
                    validated_recs.append(rec)
            
            # Validate URLs
            validated_recs = self.url_guard.sanitize_urls(validated_recs)
            
            # Rebuild response with valid recommendations
            if chat_response:
                chat_response.recommendations = validated_recs
            
            # Overall validation result
            is_valid = len(errors) == 0
            
            if not is_valid:
                logger.warning(f"Response validation errors: {errors}")
            
            return is_valid, chat_response, errors
            
        except Exception as e:
            logger.error(f"Response validation exception: {e}")
            return False, None, [f"Validation error: {e}"]
