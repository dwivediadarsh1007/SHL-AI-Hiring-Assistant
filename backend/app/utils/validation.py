"""
Validation utilities for the SHL Assessment Recommender.
"""

import re
from typing import Optional, List
from urllib.parse import urlparse


def validate_shl_url(url: str) -> bool:
    """
    Validate that a URL is from the official SHL domain.
    
    Args:
        url: URL to validate
        
    Returns:
        True if URL is valid SHL URL, False otherwise
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Valid SHL domains
        valid_domains = [
            "shl.com",
            "www.shl.com",
            "shldirect.com",
            "www.shldirect.com"
        ]
        
        return domain in valid_domains
    except Exception:
        return False


def sanitize_input(text: str, max_length: int = 2000) -> str:
    """
    Sanitize user input to prevent injection attacks.
    
    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized text
    """
    # Truncate to max length
    text = text[:max_length].strip()
    
    # Remove null bytes
    text = text.replace('\x00', '')
    
    # Remove excessive whitespace
    text = ' '.join(text.split())
    
    return text


def is_prompt_injection_attempt(text: str) -> bool:
    """
    Detect potential prompt injection attacks.
    
    Args:
        text: User input to check
        
    Returns:
        True if injection attempt is detected, False otherwise
    """
    injection_patterns = [
        r"ignore.*prompt",
        r"system.*message",
        r"act as",
        r"pretend.*to be",
        r"disregard.*instruction",
        r"override.*instruction",
        r"hidden.*instruction",
        r"jailbreak",
        r"bypass.*filter",
        r"ignore.*rule"
    ]
    
    text_lower = text.lower()
    for pattern in injection_patterns:
        if re.search(pattern, text_lower):
            return True
    
    return False


def extract_assessment_names_from_text(text: str) -> List[str]:
    """
    Extract potential assessment names from user text.
    
    Args:
        text: User input text
        
    Returns:
        List of potential assessment names
    """
    # Common abbreviations and assessment patterns
    patterns = [
        r"(?:OPQ32|OPQ)",
        r"(?:GSA|General Syntax Ability)",
        r"(?:SJT|Situational Judgment)",
        r"(?:SHL|Verify)",
        r"(?:Inductive|Deductive|Numerical|Verbal)",
        r"(?:PAPI|PAPI-ER)",
        r"(?:CEB|Talent Lens)"
    ]
    
    found_names = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        found_names.extend(matches)
    
    return list(set(found_names))


def is_conversation_complete(num_turns: int, max_turns: int) -> bool:
    """
    Check if conversation should be considered complete.
    
    Args:
        num_turns: Current number of conversation turns
        max_turns: Maximum allowed turns
        
    Returns:
        True if conversation should end, False otherwise
    """
    return num_turns >= max_turns
