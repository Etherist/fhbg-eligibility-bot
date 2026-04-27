"""Pytest configuration and fixtures for FHBG Eligibility Bot tests."""

import sys
from pathlib import Path

import pytest

# Add src to path for tests
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def sample_nsw_rules():
    """Return sample NSW rules for testing."""
    return {
        "state": "NSW",
        "grant_name": "First Home Buyer Choice",
        "rules": {
            "income_cap": 150000,
            "property_price_cap": 1500000,
            "first_home_buyer_required": True,
            "citizenship_required": "australian_citizen_or_permanent_resident",
            "new_construction_only": False,
            "grant_amount": 10000,
        },
        "sources": ["https://revenue.nsw.gov.au"],
    }


@pytest.fixture
def eligible_user_data():
    """Return sample eligible user data."""
    return {
        "state": "NSW",
        "income": 80000,
        "property_price": 700000,
        "first_home_buyer": True,
        "citizenship_status": "citizen",
        "will_reside": True,
    }


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
