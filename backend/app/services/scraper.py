"""
SHL Assessment Catalog Scraper

Robustly extracts SHL Individual Test Solutions catalog using BeautifulSoup.
Includes retry logic, deduplication, validation, and structured data export.
"""

import json
import logging
import time
from typing import List, Dict, Optional, Set
from datetime import datetime
from urllib.parse import urljoin, urlparse
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup

from app.models.catalog import CatalogEntry


# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class SHLScraper:
    """
    Robust scraper for SHL assessment catalog.
    
    Features:
    - Connection pooling with retry logic
    - HTML parsing with BeautifulSoup
    - Deduplication by URL
    - Schema validation via Pydantic
    - Persistent JSON export
    """
    
    # SHL domain constants
    BASE_URL = "https://www.shl.com"
    CATALOG_URL = "https://www.shl.com/en/solutions/assessments/"
    
    # Request configuration
    REQUEST_TIMEOUT = 10  # seconds
    MAX_RETRIES = 3
    RETRY_BACKOFF_FACTOR = 0.5
    
    # Parsing constants
    MIN_DESCRIPTION_LENGTH = 20
    
    def __init__(self, output_path: str = "data/shl_catalog.json"):
        """
        Initialize the scraper.
        
        Args:
            output_path: Path to save catalog JSON
        """
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Session with retry logic
        self.session = self._create_session()
        
        # Track seen URLs to prevent duplicates
        self.seen_urls: Set[str] = set()
        
        # Collected catalog entries
        self.catalog: List[CatalogEntry] = []
    
    def _create_session(self) -> requests.Session:
        """
        Create requests session with retry logic.
        
        Returns:
            Configured requests.Session with exponential backoff
        """
        session = requests.Session()
        
        retry_strategy = Retry(
            total=self.MAX_RETRIES,
            backoff_factor=self.RETRY_BACKOFF_FACTOR,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "HEAD"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set user agent to appear as legitimate browser
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        
        return session
    
    def fetch_page(self, url: str) -> Optional[str]:
        """
        Fetch a page with error handling and timeout.
        
        Args:
            url: URL to fetch
            
        Returns:
            HTML content or None if fetch fails
        """
        try:
            logger.info(f"Fetching: {url}")
            response = self.session.get(
                url,
                timeout=self.REQUEST_TIMEOUT,
                allow_redirects=True
            )
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None
    
    def parse_catalog_page(self, html: str) -> List[Dict[str, str]]:
        """
        Parse assessment listings from catalog page HTML.
        
        Args:
            html: Raw HTML content
            
        Returns:
            List of assessment dictionaries with name, url, description
        """
        assessments = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find assessment containers
            # This selector may need adjustment based on actual SHL page structure
            assessment_containers = soup.find_all(
                ['div', 'article', 'li'],
                class_=lambda x: x and any(
                    keyword in x.lower() 
                    for keyword in ['assessment', 'test', 'solution', 'card', 'item']
                )
            )
            
            if not assessment_containers:
                # Fallback: look for links in main content
                logger.warning("No assessment containers found, trying fallback method")
                assessment_containers = soup.find_all('a', href=True)
            
            for container in assessment_containers:
                try:
                    assessment = self._extract_assessment_from_container(container)
                    if assessment:
                        assessments.append(assessment)
                except Exception as e:
                    logger.debug(f"Failed to extract assessment from container: {e}")
                    continue
            
            logger.info(f"Extracted {len(assessments)} assessments from page")
            return assessments
            
        except Exception as e:
            logger.error(f"Failed to parse catalog page: {e}")
            return []
    
    def _extract_assessment_from_container(self, container) -> Optional[Dict[str, str]]:
        """
        Extract assessment metadata from a single container.
        
        Args:
            container: BeautifulSoup element
            
        Returns:
            Dictionary with name, url, description or None
        """
        # Extract name
        name_elem = container.find(['h1', 'h2', 'h3', 'h4', 'h5', 'a', 'span'])
        name = name_elem.get_text(strip=True) if name_elem else None
        
        if not name or len(name) < 3:
            return None
        
        # Extract URL
        link_elem = container.find('a', href=True)
        if not link_elem:
            link_elem = container if container.name == 'a' else None
        
        if not link_elem:
            return None
        
        relative_url = link_elem.get('href', '')
        url = urljoin(self.BASE_URL, relative_url)
        
        # Validate URL
        if not self._is_valid_url(url):
            return None
        
        # Extract description
        desc_elem = container.find(['p', 'span', 'div'])
        description = desc_elem.get_text(strip=True) if desc_elem else ""
        
        if len(description) < self.MIN_DESCRIPTION_LENGTH:
            description = f"Assessment: {name}"
        
        return {
            "name": name,
            "url": url,
            "description": description[:500]  # Limit description length
        }
    
    def _is_valid_url(self, url: str) -> bool:
        """
        Validate that URL is from SHL domain.
        
        Args:
            url: URL to validate
            
        Returns:
            True if valid SHL URL
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            valid_domains = [
                "shl.com",
                "www.shl.com",
                "shldirect.com",
                "www.shldirect.com"
            ]
            
            return domain in valid_domains and parsed.scheme in ['http', 'https']
        except Exception:
            return False
    
    def enrich_assessment(self, assessment: Dict[str, str]) -> Optional[CatalogEntry]:
        """
        Fetch full assessment page and extract rich metadata.
        
        Args:
            assessment: Initial assessment dictionary
            
        Returns:
            Enriched CatalogEntry or None
        """
        url = assessment.get("url")
        
        if not url or url in self.seen_urls:
            return None
        
        # Mark as seen to prevent duplicates
        self.seen_urls.add(url)
        
        # Fetch assessment page
        html = self.fetch_page(url)
        if not html:
            return None
        
        # Add small delay to be respectful to servers
        time.sleep(0.5)
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract test type
            test_type = self._extract_test_type(soup, assessment.get("name", ""))
            
            # Extract skills
            skills = self._extract_skills(soup, assessment.get("description", ""))
            
            # Extract duration
            duration = self._extract_duration(soup)
            
            # Extract keywords
            keywords = self._extract_keywords(soup, assessment.get("name", ""))
            
            # Create catalog entry
            entry = CatalogEntry(
                name=assessment.get("name", ""),
                url=url,
                description=assessment.get("description", ""),
                test_type=test_type,
                skills=skills,
                duration=duration,
                keywords=keywords
            )
            
            logger.info(f"Enriched: {entry.name}")
            return entry
            
        except Exception as e:
            logger.error(f"Failed to enrich assessment {url}: {e}")
            return None
    
    def _extract_test_type(self, soup: BeautifulSoup, name: str) -> str:
        """
        Determine assessment type from page content.
        
        Args:
            soup: Parsed HTML
            name: Assessment name for fallback matching
            
        Returns:
            Test type string
        """
        page_text = soup.get_text().lower()
        
        type_indicators = {
            "cognitive": ["reasoning", "numerical", "verbal", "inductive", "deductive"],
            "personality": ["personality", "behavior", "traits", "opq", "papi"],
            "situational": ["sjt", "judgment", "scenario", "situational"],
            "ability": ["ability", "aptitude", "skills", "competency"],
            "language": ["language", "english", "communication"],
            "technical": ["technical", "programming", "coding", "developer"]
        }
        
        for test_type, keywords in type_indicators.items():
            if any(keyword in page_text for keyword in keywords):
                return test_type
        
        # Fallback to heuristic based on name
        name_lower = name.lower()
        if "personality" in name_lower:
            return "personality"
        elif "judgment" in name_lower:
            return "situational"
        
        return "general"
    
    def _extract_skills(self, soup: BeautifulSoup, description: str) -> str:
        """
        Extract measured skills from page content.
        
        Args:
            soup: Parsed HTML
            description: Assessment description
            
        Returns:
            Comma-separated skills string
        """
        common_skills = [
            "decision-making", "leadership", "teamwork", "communication",
            "problem-solving", "reasoning", "numerical reasoning",
            "verbal reasoning", "inductive reasoning", "deductive reasoning",
            "personality", "behavior", "reliability", "accuracy"
        ]
        
        page_text = soup.get_text().lower()
        found_skills = []
        
        for skill in common_skills:
            if skill in page_text or skill.replace(" ", "-") in page_text:
                found_skills.append(skill)
        
        return ", ".join(found_skills[:8])  # Limit to 8 skills
    
    def _extract_duration(self, soup: BeautifulSoup) -> str:
        """
        Extract typical assessment duration.
        
        Args:
            soup: Parsed HTML
            
        Returns:
            Duration string (e.g., "20-30 minutes")
        """
        page_text = soup.get_text()
        
        # Look for duration patterns
        import re
        duration_pattern = r'(\d+(?:-\d+)?)\s*(?:minutes|mins|minutes?|hours?)'
        matches = re.findall(duration_pattern, page_text, re.IGNORECASE)
        
        if matches:
            return f"{matches[0]} minutes"
        
        return "20-30 minutes"  # Default
    
    def _extract_keywords(self, soup: BeautifulSoup, name: str) -> List[str]:
        """
        Extract SEO keywords for semantic search.
        
        Args:
            soup: Parsed HTML
            name: Assessment name
            
        Returns:
            List of keywords
        """
        keywords = []
        
        # Extract from meta tags
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords:
            content = meta_keywords.get('content', '')
            keywords.extend(content.split(',')[:5])
        
        # Extract from name
        name_parts = name.lower().split()
        keywords.extend([p for p in name_parts if len(p) > 3])
        
        # Common assessment keywords
        common_keywords = [
            "assessment", "test", "evaluation", "recruitment",
            "hiring", "talent", "screening"
        ]
        keywords.extend(common_keywords)
        
        # Deduplicate and limit
        return list(set(keywords))[:10]
    
    def scrape(self, max_assessments: Optional[int] = None) -> List[CatalogEntry]:
        """
        Execute full scrape of SHL catalog.
        
        Args:
            max_assessments: Maximum assessments to collect (None = unlimited)
            
        Returns:
            List of CatalogEntry objects
        """
        logger.info(f"Starting SHL catalog scrape (max: {max_assessments})")
        
        # Fetch main catalog page
        html = self.fetch_page(self.CATALOG_URL)
        if not html:
            logger.error("Failed to fetch main catalog page")
            return []
        
        # Parse initial assessments
        assessments = self.parse_catalog_page(html)
        logger.info(f"Found {len(assessments)} assessments on catalog page")
        
        # Enrich each assessment
        for i, assessment in enumerate(assessments):
            if max_assessments and len(self.catalog) >= max_assessments:
                break
            
            try:
                entry = self.enrich_assessment(assessment)
                if entry:
                    self.catalog.append(entry)
            except Exception as e:
                logger.error(f"Error enriching assessment {i}: {e}")
        
        logger.info(f"Scrape complete: {len(self.catalog)} assessments collected")
        return self.catalog
    
    def save_catalog(self) -> bool:
        """
        Save catalog to JSON file.
        
        Returns:
            True if successful
        """
        try:
            # Convert Pydantic models to dicts
            catalog_data = [entry.model_dump() for entry in self.catalog]
            
            # Create metadata
            metadata = {
                "total_entries": len(self.catalog),
                "last_updated": datetime.utcnow().isoformat() + "Z",
                "version": "1.0.0",
                "scraper_version": "1.0.0"
            }
            
            # Save to file
            output = {
                "metadata": metadata,
                "assessments": catalog_data
            }
            
            with open(self.output_path, 'w', encoding='utf-8') as f:
                json.dump(output, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved catalog to {self.output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save catalog: {e}")
            return False
    
    def load_fallback_catalog(self) -> bool:
        """
        Load fallback catalog if file exists.
        
        Returns:
            True if catalog was loaded
        """
        try:
            if not self.output_path.exists():
                logger.warning(f"Catalog file not found at {self.output_path}")
                return False
            
            with open(self.output_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            assessments = data.get("assessments", [])
            self.catalog = [
                CatalogEntry(**assessment) 
                for assessment in assessments
            ]
            
            logger.info(f"Loaded {len(self.catalog)} assessments from file")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load catalog: {e}")
            return False


def create_sample_catalog(output_path: str = "data/shl_catalog.json") -> bool:
    """
    Create a sample SHL catalog for development/testing.
    
    Args:
        output_path: Path to save sample catalog
        
    Returns:
        True if successful
    """
    sample_assessments = [
        {
            "name": "Situational Judgment Test (SJT)",
            "url": "https://www.shl.com/en/solutions/assessments/situational-judgment-test/",
            "description": "Measures behavioral competencies and judgment in realistic workplace scenarios. Assesses decision-making, problem-solving, and people skills.",
            "test_type": "situational",
            "skills": "decision-making, judgment, problem-solving, communication",
            "duration": "20-30 minutes",
            "keywords": ["behavioral", "judgment", "scenarios", "workplace"]
        },
        {
            "name": "Numerical Reasoning Test",
            "url": "https://www.shl.com/en/solutions/assessments/numerical-reasoning/",
            "description": "Assesses ability to work with numerical data and perform mathematical calculations. Used for roles requiring quantitative skills.",
            "test_type": "cognitive",
            "skills": "numerical reasoning, data analysis, mathematical skills",
            "duration": "25-35 minutes",
            "keywords": ["numerical", "quantitative", "data", "reasoning"]
        },
        {
            "name": "Verbal Reasoning Test",
            "url": "https://www.shl.com/en/solutions/assessments/verbal-reasoning/",
            "description": "Evaluates ability to comprehend written information and make logical conclusions. Essential for communication-intensive roles.",
            "test_type": "cognitive",
            "skills": "verbal reasoning, reading comprehension, logical thinking",
            "duration": "20-30 minutes",
            "keywords": ["verbal", "reading", "comprehension", "reasoning"]
        },
        {
            "name": "Inductive Reasoning Test",
            "url": "https://www.shl.com/en/solutions/assessments/inductive-reasoning/",
            "description": "Measures ability to identify patterns and draw conclusions from data. Important for analytical and technical roles.",
            "test_type": "cognitive",
            "skills": "pattern recognition, inductive reasoning, analytical thinking",
            "duration": "20-25 minutes",
            "keywords": ["patterns", "inductive", "analytical", "logic"]
        },
        {
            "name": "OPQ32 Personality Questionnaire",
            "url": "https://www.shl.com/en/solutions/assessments/opq32/",
            "description": "Comprehensive personality assessment measuring 32 personality factors. Provides insights into work style, preferences, and potential.",
            "test_type": "personality",
            "skills": "personality traits, work style, behavioral preferences",
            "duration": "45-60 minutes",
            "keywords": ["personality", "behavior", "traits", "opq"]
        },
        {
            "name": "Deductive Reasoning Test",
            "url": "https://www.shl.com/en/solutions/assessments/deductive-reasoning/",
            "description": "Evaluates logical reasoning ability using syllogisms and formal logic. Particularly relevant for technical and managerial positions.",
            "test_type": "cognitive",
            "skills": "deductive reasoning, logical thinking, problem-solving",
            "duration": "20-25 minutes",
            "keywords": ["deductive", "logic", "reasoning", "syllogisms"]
        },
        {
            "name": "PAPI-ER Personality Assessment",
            "url": "https://www.shl.com/en/solutions/assessments/papi-er/",
            "description": "Assessment of personality and work-related behaviors. Quick personality profiling tool for recruitment and team building.",
            "test_type": "personality",
            "skills": "personality assessment, behavioral profiling",
            "duration": "15-20 minutes",
            "keywords": ["personality", "behavior", "papi", "assessment"]
        },
        {
            "name": "Verify - General Ability",
            "url": "https://www.shl.com/en/solutions/assessments/verify/",
            "description": "Adaptive assessment measuring cognitive abilities including reasoning, numerical, and verbal skills. Modern and mobile-optimized.",
            "test_type": "ability",
            "skills": "general ability, reasoning, numerical, verbal",
            "duration": "20-25 minutes",
            "keywords": ["ability", "adaptive", "verify", "general"]
        }
    ]
    
    try:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to CatalogEntry objects
        entries = [CatalogEntry(**assessment) for assessment in sample_assessments]
        
        # Create metadata
        metadata = {
            "total_entries": len(entries),
            "last_updated": datetime.utcnow().isoformat() + "Z",
            "version": "1.0.0",
            "source": "sample"
        }
        
        # Save
        output = {
            "metadata": metadata,
            "assessments": [entry.model_dump() for entry in entries]
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Created sample catalog with {len(entries)} assessments")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create sample catalog: {e}")
        return False
