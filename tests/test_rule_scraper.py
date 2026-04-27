"""Unit tests for rule_scraper agent."""

import json
import tempfile
from pathlib import Path
import pytest

from src.agents.rule_scraper import RuleScraper


class TestRuleScraper:
    """Test suite for RuleScraper agent."""

    def test_scrape_nsw_rules_returns_valid_structure(self):
        """Test scraping NSW rules returns expected structure."""
        scraper = RuleScraper()
        rules = scraper.scrape_state_rules("NSW", force_refresh=True)

        assert rules is not None
        assert rules["state"] == "NSW"
        assert "grant_name" in rules
        assert "rules" in rules
        assert "income_cap" in rules["rules"]
        assert "property_price_cap" in rules["rules"]
        assert "grant_amount" in rules["rules"]

    def test_scrape_cached_rules_loads_from_file(self, tmp_path):
        """Test that cached rules are loaded from file."""
        # Create test data
        test_rules = {
            "state": "NSW",
            "grant_name": "Test Grant",
            "rules": {
                "income_cap": 100000,
                "property_price_cap": 1000000,
                "first_home_buyer_required": True,
                "grant_amount": 5000,
            },
            "sources": ["https://test.example.com"],
        }

        # Save to temp file
        cache_file = tmp_path / "nsw_rules.json"
        with open(cache_file, "w") as f:
            json.dump(test_rules, f)

        # Load with scraper (using validate_paths=False to allow test temp directory)
        scraper = RuleScraper(data_path=str(tmp_path) + "/", validate_paths=False)
        loaded = scraper.scrape_state_rules("NSW")

        assert loaded == test_rules

    def test_invalid_state_returns_none(self):
        """Test that unsupported state returns None."""
        scraper = RuleScraper()
        rules = scraper.scrape_state_rules("XYZ")
        assert rules is None

    def test_cache_clear_removes_cached_file(self, tmp_path):
        """Test cache clearing functionality."""
        # Create dummy cache file
        cache_file = tmp_path / "nsw_rules.json"
        cache_file.write_text("{}")

        scraper = RuleScraper(data_path=str(tmp_path) + "/", validate_paths=False)
        scraper.clear_cache("NSW")

        assert not cache_file.exists()

    def test_get_supported_states_returns_list(self):
        """Test supported states list."""
        scraper = RuleScraper()
        states = scraper.get_supported_states()

        assert isinstance(states, list)
        assert "NSW" in states
        assert "VIC" in states
        assert "QLD" in states
        assert "WA" in states

    def test_validate_state_accepts_valid(self):
        """Test state validation accepts valid states."""
        scraper = RuleScraper()
        assert scraper.validate_state("NSW") is True
        assert scraper.validate_state("nsw") is True
        assert scraper.validate_state("vic") is True

    def test_validate_state_rejects_invalid(self):
        """Test state validation rejects invalid states."""
        scraper = RuleScraper()
        assert scraper.validate_state("NY") is False
        assert scraper.validate_state("") is False

    def test_nsw_rules_have_correct_values(self):
        """Test NSW rules contain correct expected values."""
        scraper = RuleScraper()
        rules = scraper.scrape_state_rules("NSW", force_refresh=True)

        assert rules["state"] == "NSW"
        assert rules["grant_name"] == "First Home Buyer Choice"
        assert rules["rules"]["grant_amount"] == 10000
        assert rules["rules"]["income_cap"] == 150000
        assert rules["rules"]["property_price_cap"] == 1500000
        assert rules["rules"]["first_home_buyer_required"] is True
        assert rules["rules"]["new_construction_only"] is False
