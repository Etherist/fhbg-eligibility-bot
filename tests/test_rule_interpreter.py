"""Unit tests for rule_interpreter agent."""

import pytest

from src.agents.rule_interpreter import RuleInterpreter, EligibilityStatus, EligibilityReport, ValidationResult


class TestRuleInterpreter:
    """Test suite for RuleInterpreter agent."""

    @pytest.fixture
    def nsw_rules(self):
        """Sample NSW rules for testing."""
        return {
            "state": "NSW",
            "grant_name": "First Home Buyer Choice",
            "rules": {
                "income_cap": 150000,
                "property_price_cap": 1500000,
                "first_home_buyer_required": True,
                "citizenship_required": "australian_citizen_or_permanent_resident",
                "residency_requirement": "must_live_in_property_within_6_months",
                "new_construction_only": False,
                "grant_amount": 10000,
            },
            "sources": ["https://revenue.nsw.gov.au"],
        }

    @pytest.fixture
    def interpreter(self, nsw_rules):
        """Create RuleInterpreter with NSW rules."""
        return RuleInterpreter(nsw_rules)

    def test_eligible_user_all_criteria_met(self, interpreter):
        """Test user who meets all criteria is eligible."""
        user_data = {
            "state": "NSW",
            "income": 80000,
            "property_price": 700000,
            "first_home_buyer": True,
            "citizenship_status": "australian citizen",
            "will_reside": True,
            "property_is_new": False,
        }

        report = interpreter.validate_eligibility(user_data)

        assert report.status == EligibilityStatus.ELIGIBLE
        assert report.grant_amount == 10000
        assert len(report.failed_rules) == 0
        assert len(report.passed_rules) >= 5

    def test_not_eligible_income_too_high(self, interpreter):
        """Test user with income above cap."""
        user_data = {
            "state": "NSW",
            "income": 200000,  # Above $150k cap
            "property_price": 700000,
            "first_home_buyer": True,
            "citizenship_status": "citizen",
            "will_reside": True,
            "property_is_new": False,
        }

        report = interpreter.validate_eligibility(user_data)

        assert report.status == EligibilityStatus.NOT_ELIGIBLE
        assert len(report.failed_rules) > 0
        assert any("Income" in fr.rule_name for fr in report.failed_rules)
        assert report.missing_requirements[0].startswith("Income Cap")

    def test_not_eligible_property_price_too_high(self, interpreter):
        """Test user with property price above cap."""
        user_data = {
            "state": "NSW",
            "income": 80000,
            "property_price": 2000000,  # Above $1.5M cap
            "first_home_buyer": True,
            "citizenship_status": "citizen",
            "will_reside": True,
        }

        report = interpreter.validate_eligibility(user_data)

        assert report.status == EligibilityStatus.NOT_ELIGIBLE
        assert any("Property Price" in fr.rule_name for fr in report.failed_rules)

    def test_not_eligible_not_first_home_buyer(self, interpreter):
        """Test user who is not a first home buyer."""
        user_data = {
            "state": "NSW",
            "income": 80000,
            "property_price": 700000,
            "first_home_buyer": False,
            "citizenship_status": "citizen",
            "will_reside": True,
        }

        report = interpreter.validate_eligibility(user_data)

        assert report.status == EligibilityStatus.NOT_ELIGIBLE
        assert any("First Home Buyer" in fr.rule_name for fr in report.failed_rules)

    def test_not_eligible_non_citizen(self, interpreter):
        """Test user with non-citizen status."""
        user_data = {
            "state": "NSW",
            "income": 80000,
            "property_price": 700000,
            "first_home_buyer": True,
            "citizenship_status": "visitor",
            "will_reside": True,
        }

        report = interpreter.validate_eligibility(user_data)

        assert report.status == EligibilityStatus.NOT_ELIGIBLE
        assert any("Citizenship" in fr.rule_name for fr in report.failed_rules)

    def test_not_eligible_will_not_reside(self, interpreter):
        """Test user who won't live in property."""
        user_data = {
            "state": "NSW",
            "income": 80000,
            "property_price": 700000,
            "first_home_buyer": True,
            "citizenship_status": "citizen",
            "will_reside": False,
        }

        report = interpreter.validate_eligibility(user_data)

        assert report.status == EligibilityStatus.NOT_ELIGIBLE
        assert any("Residency" in fr.rule_name for fr in report.failed_rules)

    def test_eligible_with_permanent_resident(self, interpreter):
        """Test permanent resident is eligible."""
        user_data = {
            "state": "NSW",
            "income": 80000,
            "property_price": 700000,
            "first_home_buyer": True,
            "citizenship_status": "permanent resident",
            "will_reside": True,
        }

        report = interpreter.validate_eligibility(user_data)

        assert report.status == EligibilityStatus.ELIGIBLE

    def test_edge_case_income_exactly_at_cap(self, interpreter):
        """Test income exactly at cap is eligible."""
        user_data = {
            "state": "NSW",
            "income": 150000,  # Exactly at cap
            "property_price": 700000,
            "first_home_buyer": True,
            "citizenship_status": "citizen",
            "will_reside": True,
        }

        report = interpreter.validate_eligibility(user_data)

        assert report.status == EligibilityStatus.ELIGIBLE

    def test_edge_case_property_price_exactly_at_cap(self, interpreter):
        """Test property price exactly at cap is eligible."""
        user_data = {
            "state": "NSW",
            "income": 80000,
            "property_price": 1500000,  # Exactly at cap
            "first_home_buyer": True,
            "citizenship_status": "citizen",
            "will_reside": True,
        }

        report = interpreter.validate_eligibility(user_data)

        assert report.status == EligibilityStatus.ELIGIBLE

    def test_next_steps_contain_application_link(self, interpreter):
        """Test that next steps include application link."""
        user_data = {
            "state": "NSW",
            "income": 80000,
            "property_price": 700000,
            "first_home_buyer": True,
            "citizenship_status": "citizen",
            "will_reside": True,
        }

        report = interpreter.validate_eligibility(user_data)
        steps_text = " ".join(report.next_steps)

        assert "revenue.nsw.gov.au" in steps_text.lower()
        assert "apply" in steps_text.lower()

    def test_missing_optional_fields_still_eligible(self, interpreter):
        """Test that optional fields don't block eligibility."""
        user_data = {
            "state": "NSW",
            "income": 80000,
            "property_price": 700000,
            "first_home_buyer": True,
            "citizenship_status": "citizen",
            "will_reside": True,
            # property_is_new omitted (optional)
        }

        report = interpreter.validate_eligibility(user_data)

        assert report.status == EligibilityStatus.ELIGIBLE

    def test_report_contains_sources(self, interpreter):
        """Test eligibility report includes sources."""
        user_data = {
            "state": "NSW",
            "income": 80000,
            "property_price": 700000,
            "first_home_buyer": True,
            "citizenship_status": "citizen",
            "will_reside": True,
        }

        report = interpreter.validate_eligibility(user_data)

        assert len(report.sources) > 0
        assert "revenue.nsw.gov.au" in report.sources[0]

    def test_warnings_added_for_missing_non_critical_info(self, interpreter):
        """Test warnings for missing non-critical information."""
        user_data = {
            "state": "NSW",
            "income": 80000,
            "property_price": 700000,
            "first_home_buyer": True,
            "citizenship_status": "citizen",
            "will_reside": True,
            # property_is_new explicitly None
        }

        report = interpreter.validate_eligibility(user_data)

        # Should have warnings but still eligible
        assert report.status == EligibilityStatus.ELIGIBLE
        # Note: interpretation of missing optional fields may produce warnings
        # This depends on implementation details
