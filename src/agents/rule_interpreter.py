"""Rule Interpreter Agent for FHBG Eligibility Bot.

Validates user-provided data against scraped eligibility rules
and determines grant eligibility status.
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class EligibilityStatus(Enum):
    """Eligibility determination result."""
    ELIGIBLE = "eligible"
    NOT_ELIGIBLE = "not_eligible"
    NEEDS_REVIEW = "needs_review"


@dataclass
class ValidationResult:
    """Result of a single rule validation."""
    rule_name: str
    passed: bool
    user_value: Any
    required_value: Any
    message: str


@dataclass
class EligibilityReport:
    """Comprehensive eligibility report."""
    status: EligibilityStatus
    state: str
    grant_amount: float
    grant_name: str
    passed_rules: List[str] = field(default_factory=list)
    failed_rules: List[ValidationResult] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    missing_requirements: List[str] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)


class RuleInterpreter:
    """Agent that interprets rules and validates user eligibility."""

    def __init__(self, rules: Dict[str, Any]):
        """Initialize RuleInterpreter with cached rules.

        Args:
            rules: Dictionary of eligibility rules for a state.
        """
        self.rules = rules
        self.state = rules.get("state", "UNKNOWN")
        self.grant_name = rules.get("grant_name", "First Home Owner Grant")
        self.grant_amount = rules.get("rules", {}).get("grant_amount", 0)
        self._validate_rules_structure()

    def _validate_rules_structure(self) -> None:
        """Validate that required rules are present."""
        required_keys = ["income_cap", "property_price_cap", "first_home_buyer_required"]
        rules_dict = self.rules.get("rules", {})

        missing_keys = [k for k in required_keys if k not in rules_dict]
        if missing_keys:
            logger.warning(f"Missing required rule keys: {missing_keys}")

    def validate_eligibility(self, user_data: Dict[str, Any]) -> EligibilityReport:
        """Validate user eligibility against all rules.

        Args:
            user_data: Dictionary containing user's answers.
                Required keys: income, property_price, state, first_home_buyer,
                citizenship_status, will_reside

        Returns:
            EligibilityReport with detailed results.
        """
        logger.info(f"Validating eligibility for user in {self.state}")

        report = EligibilityReport(
            status=EligibilityStatus.ELIGIBLE,
            state=self.state,
            grant_amount=self.grant_amount,
            grant_name=self.grant_name,
            sources=self.rules.get("sources", []),
        )

        rules_dict = self.rules.get("rules", {})

        # Rule 1: Income cap
        self._check_income_cap(user_data, rules_dict, report)

        # Rule 2: Property price cap
        self._check_property_price_cap(user_data, rules_dict, report)

        # Rule 3: First home buyer status
        self._check_first_home_buyer(user_data, rules_dict, report)

        # Rule 4: Citizenship/residency status
        self._check_citizenship(user_data, rules_dict, report)

        # Rule 5: Residency requirement (intention to live in property)
        self._check_residency_intention(user_data, rules_dict, report)

        # Rule 6: New construction only (if applicable)
        self._check_construction_type(user_data, rules_dict, report)

        # Determine overall status
        if report.failed_rules:
            report.status = EligibilityStatus.NOT_ELIGIBLE
            report.missing_requirements = [
                f"{v.rule_name}: {v.message}" for v in report.failed_rules
            ]

        # Generate next steps
        report.next_steps = self._generate_next_steps(report, user_data)

        logger.info(
            f"Eligibility check complete: {report.status.value}, "
            f"grant amount: ${self.grant_amount:,}"
        )
        return report

    def _check_income_cap(
        self,
        user_data: Dict[str, Any],
        rules_dict: Dict[str, Any],
        report: EligibilityReport,
    ) -> None:
        """Validate household income against cap."""
        income_cap = rules_dict.get("income_cap")
        if income_cap is None:
            logger.warning("No income_cap rule defined")
            return

        user_income = user_data.get("income", 0)
        result = ValidationResult(
            rule_name="Income Cap",
            passed=user_income <= income_cap,
            user_value=user_income,
            required_value=income_cap,
            message="",
        )

        if result.passed:
            report.passed_rules.append("Income Cap")
            logger.debug(f"Income {user_income} <= cap {income_cap} ✓")
        else:
            result.message = f"Your income (${user_income:,}) exceeds the cap (${income_cap:,})"
            report.failed_rules.append(result)
            logger.info(f"Income check failed: {result.message}")

    def _check_property_price_cap(
        self,
        user_data: Dict[str, Any],
        rules_dict: Dict[str, Any],
        report: EligibilityReport,
    ) -> None:
        """Validate property price against cap."""
        price_cap = rules_dict.get("property_price_cap")
        if price_cap is None:
            logger.warning("No property_price_cap rule defined")
            return

        property_price = user_data.get("property_price", 0)
        result = ValidationResult(
            rule_name="Property Price Cap",
            passed=property_price <= price_cap,
            user_value=property_price,
            required_value=price_cap,
            message="",
        )

        if result.passed:
            report.passed_rules.append("Property Price Cap")
            logger.debug(f"Property price ${property_price:,} <= cap ${price_cap:,} ✓")
        else:
            result.message = f"Property price (${property_price:,}) exceeds cap (${price_cap:,})"
            report.failed_rules.append(result)
            logger.info(f"Property price check failed: {result.message}")

    def _check_first_home_buyer(
        self,
        user_data: Dict[str, Any],
        rules_dict: Dict[str, Any],
        report: EligibilityReport,
    ) -> None:
        """Validate first home buyer status."""
        required = rules_dict.get("first_home_buyer_required", True)
        user_is_first_home_buyer = user_data.get("first_home_buyer", False)

        result = ValidationResult(
            rule_name="First Home Buyer Status",
            passed=not required or user_is_first_home_buyer,
            user_value=user_is_first_home_buyer,
            required_value=required,
            message="",
        )

        if result.passed:
            report.passed_rules.append("First Home Buyer Status")
            logger.debug("First home buyer check ✓")
        else:
            result.message = "You must be a first home buyer to qualify for this grant"
            report.failed_rules.append(result)
            logger.info("First home buyer check failed")

    def _check_citizenship(
        self,
        user_data: Dict[str, Any],
        rules_dict: Dict[str, Any],
        report: EligibilityReport,
    ) -> None:
        """Validate citizenship/residency status."""
        required = rules_dict.get("citizenship_required", "")
        user_status = user_data.get("citizenship_status", "").lower()

        # Normalize statuses
        valid_statuses = {
            "australian_citizen_or_permanent_resident": [
                "citizen",
                "permanent resident",
                "pr",
                "australian citizen",
                "citizenship",
            ],
            "citizen_only": ["citizen", "australian citizen", "citizenship"],
        }

        result = ValidationResult(
            rule_name="Citizenship/Residency",
            passed=False,
            user_value=user_status,
            required_value=required,
            message="",
        )

        if required in valid_statuses:
            result.passed = any(
                keyword in user_status for keyword in valid_statuses[required]
            )

        if result.passed:
            report.passed_rules.append("Citizenship/Residency")
            logger.debug("Citizenship check ✓")
        else:
            result.message = f"You must be {required.replace('_', ' ')}"
            report.failed_rules.append(result)
            logger.info("Citizenship check failed")

    def _check_residency_intention(
        self,
        user_data: Dict[str, Any],
        rules_dict: Dict[str, Any],
        report: EligibilityReport,
    ) -> None:
        """Validate residency intention (must live in property)."""
        requirement = rules_dict.get("residency_requirement", "")
        user_will_reside = user_data.get("will_reside", False)

        if not requirement:
            return  # No requirement specified

        result = ValidationResult(
            rule_name="Residency Intention",
            passed=user_will_reside,
            user_value=user_will_reside,
            required_value=requirement,
            message="",
        )

        if result.passed:
            report.passed_rules.append("Residency Intention")
            logger.debug("Residency intention check ✓")
        else:
            result.message = "You must live in the property as your primary residence"
            report.failed_rules.append(result)
            logger.info("Residency intention check failed")

    def _check_construction_type(
        self,
        user_data: Dict[str, Any],
        rules_dict: Dict[str, Any],
        report: EligibilityReport,
    ) -> None:
        """Validate property type (new construction vs existing)."""
        new_construction_only = rules_dict.get("new_construction_only", False)
        is_new_home = user_data.get("property_is_new", None)

        if not new_construction_only:
            return  # No restriction

        if is_new_home is None:
            # Not provided - add warning but not a failure
            report.warnings.append(
                "Property type not specified. Grant may be limited to new construction."
            )
            return

        result = ValidationResult(
            rule_name="Property Type",
            passed=is_new_home,
            user_value=is_new_home,
            required_value=True,
            message="",
        )

        if result.passed:
            report.passed_rules.append("Property Type")
            logger.debug("Construction type check ✓")
        else:
            result.message = "This grant is only available for new construction"
            report.failed_rules.append(result)
            logger.info("Construction type check failed")

    def _generate_next_steps(
        self,
        report: EligibilityReport,
        user_data: Dict[str, Any],
    ) -> List[str]:
        """Generate recommended next steps based on eligibility."""
        steps = []

        if report.status == EligibilityStatus.ELIGIBLE:
            steps.append(f"✅ You are eligible for the {self.grant_name}!")
            steps.append(f"💰 Grant amount: ${self.grant_amount:,.0f}")

            # Add state-specific application link
            if self.state == "NSW":
                steps.append(
                    "📍 Apply via: https://www.revenue.nsw.gov.au/grants-schemes/first-home-buyer"
                )
            elif self.state == "VIC":
                steps.append(
                    "📍 Apply via: https://www.sro.vic.gov.au/first-home-owner-grant"
                )
            else:
                steps.append(
                    f"📍 Visit your state revenue office website to apply"
                )

            # Additional advice
            steps.append("📋 Next steps:")
            steps.append("   1. Gather required documents (ID, proof of income, contract)")
            steps.append("   2. Complete the grant application form")
            steps.append("   3. Submit before settlement/completion date")
            steps.append("   4. Notify your lender if using for home loan")

        else:
            steps.append("❌ You are not currently eligible for this grant.")
            steps.append("💡 Consider the following options:")
            steps.append(
                "   - Adjust property price or location (some grants have regional caps)"
            )
            steps.append("   - Review income requirements (some grants have household caps)")
            steps.append("   - Check eligibility for other state/federal programs")

            # Specific advice based on failed rules
            for failure in report.failed_rules:
                if "Income" in failure.rule_name:
                    steps.append(
                        f"   - Income cap is ${failure.required_value:,} (your income: ${failure.user_value:,})"
                    )
                elif "Property Price" in failure.rule_name:
                    steps.append(
                        f"   - Price cap is ${failure.required_value:,} (your property: ${failure.user_value:,})"
                    )

        # Add source attribution
        if report.sources:
            steps.append(f"📚 Source: {', '.join(report.sources)}")

        return steps


def main():
    """CLI interface for rule_interpreter."""
    import argparse

    parser = argparse.ArgumentParser(description="Validate FHBG eligibility")
    parser.add_argument(
        "--state", default="NSW", choices=["NSW", "VIC", "QLD", "WA"], help="State"
    )
    parser.add_argument("--income", type=float, required=True, help="Annual income")
    parser.add_argument(
        "--property-price", type=float, required=True, help="Property purchase price"
    )
    parser.add_argument(
        "--first-home",
        action="store_true",
        help="Is this your first home?",
    )
    parser.add_argument(
        "--citizenship",
        default="citizen",
        choices=["citizen", "permanent resident", "pr", "citizenship"],
        help="Citizenship status",
    )
    parser.add_argument(
        "--will-reside",
        action="store_true",
        help="Will you live in the property?",
    )
    parser.add_argument(
        "--is-new",
        action="store_true",
        help="Is the property newly constructed?",
    )

    args = parser.parse_args()

    # Load rules using RuleScraper
    from src.agents.rule_scraper import RuleScraper

    scraper = RuleScraper()
    rules = scraper.scrape_state_rules(args.state)
    if not rules:
        print(f"❌ Could not load rules for {args.state}")
        return 1

    # Create interpreter
    interpreter = RuleInterpreter(rules)

    # Prepare user data
    user_data = {
        "income": args.income,
        "property_price": args.property_price,
        "state": args.state,
        "first_home_buyer": args.first_home,
        "citizenship_status": args.citizenship,
        "will_reside": args.will_reside,
        "property_is_new": args.is_new,
    }

    # Validate
    report = interpreter.validate_eligibility(user_data)

    # Print report
    print("\n" + "=" * 60)
    print(f"🏡 FHBG Eligibility Report: {self.grant_name}")
    print("=" * 60)

    if report.status == EligibilityStatus.ELIGIBLE:
        print(f"✅ Status: ELIGIBLE")
        print(f"💰 Grant Amount: ${report.grant_amount:,.0f}")
    else:
        print(f"❌ Status: NOT ELIGIBLE")
        if report.missing_requirements:
            print("\n🔴 Missing requirements:")
            for req in report.missing_requirements:
                print(f"   - {req}")

    print(f"\n📊 Validation Summary:")
    print(f"   Passed: {len(report.passed_rules)}")
    print(f"   Failed: {len(report.failed_rules)}")

    if report.warnings:
        print(f"\n⚠️  Warnings:")
        for warning in report.warnings:
            print(f"   - {warning}")

    print(f"\n📋 Next Steps:")
    for step in report.next_steps:
        print(f"   {step}")

    return 0 if report.status == EligibilityStatus.ELIGIBLE else 1


if __name__ == "__main__":
    exit(main())
