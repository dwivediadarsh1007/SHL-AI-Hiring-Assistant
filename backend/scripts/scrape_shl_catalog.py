"""
Executable script to scrape SHL catalog.

Usage:
    python scripts/scrape_shl_catalog.py [--max N] [--sample]

Options:
    --max N       Maximum number of assessments to scrape (default: unlimited)
    --sample      Create sample catalog instead of scraping live
"""

import sys
import argparse
import logging
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.scraper import SHLScraper, create_sample_catalog


def main():
    """Main entry point for scraper."""
    parser = argparse.ArgumentParser(
        description="Scrape SHL assessment catalog"
    )
    parser.add_argument(
        "--max",
        type=int,
        default=None,
        help="Maximum number of assessments to scrape"
    )
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Create sample catalog instead of live scraping"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/shl_catalog.json",
        help="Output file path"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    if args.sample:
        logger.info("Creating sample catalog...")
        success = create_sample_catalog(args.output)
        if success:
            logger.info(f"✓ Sample catalog created at {args.output}")
            return 0
        else:
            logger.error("✗ Failed to create sample catalog")
            return 1
    else:
        logger.info("Starting SHL catalog scrape...")
        scraper = SHLScraper(output_path=args.output)
        
        # Try to scrape
        catalog = scraper.scrape(max_assessments=args.max)
        
        if not catalog:
            logger.warning("No assessments scraped, trying to load existing catalog...")
            if scraper.load_fallback_catalog():
                logger.info(f"✓ Loaded {len(scraper.catalog)} assessments from file")
                return 0
            else:
                logger.error("✗ Failed to scrape and no fallback available")
                return 1
        
        # Save catalog
        success = scraper.save_catalog()
        if success:
            logger.info(f"✓ Scraped and saved {len(scraper.catalog)} assessments")
            return 0
        else:
            logger.error("✗ Failed to save catalog")
            return 1


if __name__ == "__main__":
    sys.exit(main())
