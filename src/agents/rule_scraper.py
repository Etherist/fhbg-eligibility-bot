"""Rule Scraper Agent for FHBG Eligibility Bot.

Fetches and parses eligibility criteria from state government websites
or loads from cached JSON files for demo purposes.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import hashlib

import requests
from bs4 import BeautifulSoup
import time

# Configure logging
logger = logging.getLogger(__name__)


class RuleScraper:
    """Agent responsible for fetching and caching FHBG eligibility rules."""

    def __init__(
        self,
        data_path: str = "src/data/",
        cache_ttl: int = 86400,  # 24 hours
        scrape_delay: float = 2.0,
        validate_paths: bool = True,
    ):
        """Initialize RuleScraper.

        Args:
            data_path: Path to data directory containing cached rules.
                      Default is relative to project root.
            cache_ttl: Cache TTL in seconds.
            scrape_delay: Delay between scrapes to avoid rate limiting.
            validate_paths: Enforce path traversal protection (disable for tests).

        Security:
            When validate_paths=True, data_path is resolved relative to project
            root and validated to prevent directory traversal.
        """
        # Security: Resolve data_path relative to project root (not cwd)
        project_root = Path(__file__).parent.parent.parent.resolve()
        if not Path(data_path).is_absolute():
            data_path = str(project_root / data_path)
        self.data_path = Path(data_path).resolve()

        # Validate path is within project root (if enabled)
        if validate_paths and not self.data_path.is_relative_to(project_root):
            raise ValueError(
                f"data_path must be within project directory: {project_root}. "
                f"Got: {self.data_path}"
            )

        self.cache_ttl = cache_ttl
        self.scrape_delay = scrape_delay
        self._ensure_data_dir()

    def _ensure_data_dir(self) -> None:
        """Ensure data directory exists."""
        self.data_path.mkdir(parents=True, exist_ok=True)

    def scrape_state_rules(
        self,
        state: str,
        force_refresh: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """Scrape or load cached rules for a given state.

        Args:
            state: State abbreviation (e.g., 'NSW', 'VIC').
            force_refresh: Force re-scrape even if cache is valid.

        Returns:
            Dictionary of eligibility rules or None if failed.
        """
        state = state.upper()
        cache_file = self.data_path / f"{state.lower()}_rules.json"

        # Check cache validity
        if cache_file.exists() and not force_refresh:
            cache_age = time.time() - cache_file.stat().st_mtime
            if cache_age < self.cache_ttl:
                logger.info(f"Loading cached rules for {state}")
                return self._load_json(cache_file)

        logger.info(f"Scraping rules for {state}")

        # Map states to their official URLs
        state_urls = {
            "NSW": "https://www.revenue.nsw.gov.au/grants-schemes/first-home-buyer",
            "VIC": "https://www.sro.vic.gov.au/first-home-owner-grant",
            "QLD": "https://www.qro.qld.gov.au/grants/first-home-owner-grant",
            "WA": "https://www.wa.gov.au/organisation/department-of-finance/first-home-owner-grant",
        }

        if state not in state_urls:
            logger.error(f"Unsupported state: {state}")
            return None

        try:
            # For demo, use static data; for production, implement real scraping
            if state == "NSW":
                rules = self._scrape_nsw_rules()
            else:
                rules = self._get_static_rules(state)

            # Cache the results
            self._save_json(cache_file, rules)
            logger.info(f"Successfully scraped and cached rules for {state}")
            return rules

        except Exception as e:
            logger.error(f"Failed to scrape rules for {state}: {e}")
            # Fall back to cached data if available
            if cache_file.exists():
                logger.info(f"Falling back to cached rules for {state}")
                return self._load_json(cache_file)
            return None

    def _scrape_nsw_rules(self) -> Dict[str, Any]:
        """Scrape NSW First Home Buyer Choice grant rules.

        For demo purposes, this returns static data. In production,
        you would implement actual web scraping or RAG retrieval.
        """
        time.sleep(self.scrape_delay)  # Be polite

        # NSW First Home Buyer Choice - Current rules (2024)
        # Source: https://www.revenue.nsw.gov.au/grants-schemes/first-home-buyer
        return {
            "state": "NSW",
            "grant_name": "First Home Buyer Choice",
            "effective_date": "2024-01-01",
            "rules": {
                "income_cap": 150000,  # Annual household income <= $150k
                "property_price_cap": 1500000,  # Property price <= $1.5M
                "first_home_buyer_required": True,
                "citizenship_required": "australian_citizen_or_permanent_resident",
                "residency_requirement": "must_live_in_property_within_6_months",
                "deputy_required": False,  # No minimum deposit requirement explicitly
                "new_construction_only": False,  # Applies to both new and existing homes
                "grant_amount": 10000,  # $10,000 grant
                "additional_benefits": [
                    "stamp_duty_exemption_or_concession",
                    "no_lenders_mortgage_insurance_required_for_borrowers_with_5_deposit",
                ],
            },
            "sources": [
                "https://www.revenue.nsw.gov.au/grants-schemes/first-home-buyer"
            ],
        }

    def _get_static_rules(self, state: str) -> Dict[str, Any]:
        """Get static rules for states other than NSW (demo)."""
        time.sleep(self.scrape_delay)

        # Placeholder rules - extend with actual data for each state
        base_rules = {
            "state": state,
            "grant_name": f"{state} First Home Owner Grant",
            "effective_date": "2024-01-01",
            "rules": {
                "income_cap": 120000,
                "property_price_cap": 600000,
                "first_home_buyer_required": True,
                "citizenship_required": "australian_citizen_or_permanent_resident",
                "residency_requirement": "must_live_in_property_within_6_months",
                "deputy_required": False,
                "new_construction_only": True,  # Most states only for new homes
                "grant_amount": 10000,
                "additional_benefits": [],
            },
            "sources": [],
        }

        # Customize per state (simplified)
        if state == "VIC":
            base_rules["grant_name"] = "First Home Owner Grant"
            base_rules["rules"]["grant_amount"] = 10000
            base_rules["sources"] = [
                "https://www.sro.vic.gov.au/first-home-owner-grant"
            ]
        elif state == "QLD":
            base_rules["grant_name"] = "First Home Owner Grant"
            base_rules["rules"]["grant_amount"] = 15000
            base_rules["sources"] = [
                "https://www.qro.qld.gov.au/grants/first-home-owner-grant"
            ]
        elif state == "WA":
            base_rules["grant_name"] = "First Home Owner Grant"
            base_rules["rules"]["grant_amount"] = 10000
            base_rules["sources"] = [
                "https://www.wa.gov.au/organisation/department-of-finance/first-home-owner-grant"
            ]

        return base_rules

    def _load_json(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Load JSON from file."""
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {file_path}: {e}")
            return None
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            return None

    def _save_json(self, file_path: Path, data: Dict[str, Any]) -> None:
        """Save JSON to file."""
        try:
            with open(file_path, "w") as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved rules to {file_path}")
        except Exception as e:
            logger.error(f"Failed to save rules: {e}")

    def get_supported_states(self) -> list[str]:
        """Get list of supported states."""
        return ["NSW", "VIC", "QLD", "WA"]

    def validate_state(self, state: str) -> bool:
        """Check if state is supported."""
        return state.upper() in self.get_supported_states()

    def clear_cache(self, state: Optional[str] = None) -> bool:
        """Clear cached rules for a state or all states."""
        try:
            if state:
                cache_file = self.data_path / f"{state.lower()}_rules.json"
                if cache_file.exists():
                    cache_file.unlink()
                    logger.info(f"Cleared cache for {state}")
            else:
                for file in self.data_path.glob("*_rules.json"):
                    file.unlink()
                logger.info("Cleared all rule caches")
            return True
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return False


def main():
    """CLI interface for rule_scraper."""
    import argparse

    parser = argparse.ArgumentParser(description="Scrape FHBG grant rules")
    parser.add_argument(
        "state",
        choices=["NSW", "VIC", "QLD", "WA"],
        help="State to scrape rules for",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force refresh even if cache is valid",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output file path (default: src/data/{state}_rules.json)",
    )
    parser.add_argument(
        "--clear-cache",
        action="store_true",
        help="Clear cache instead of scraping",
    )

    args = parser.parse_args()

    scraper = RuleScraper()

    if args.clear_cache:
        scraper.clear_cache(args.state)
        return

    rules = scraper.scrape_state_rules(args.state, force_refresh=args.force)

    if rules:
        if args.output:
            output_path = Path(args.output)
        else:
            output_path = Path(f"src/data/{args.state.lower()}_rules.json")

        scraper._save_json(output_path, rules)
        print(f"✅ Rules for {args.state} saved to {output_path}")
        print(f"   Grant: {rules['grant_name']}")
        print(f"   Amount: ${rules['rules']['grant_amount']:,}")
        print(f"   Income cap: ${rules['rules']['income_cap']:,}")
        print(f"   Property price cap: ${rules['rules']['property_price_cap']:,}")
    else:
        print(f"❌ Failed to scrape rules for {args.state}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
