#!/usr/bin/env python3
"""
Seed script for FHBG Eligibility Bot.

Populates initial data (sample test cases, rules, etc.).
Primarily used for demo purposes and initial setup.
"""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.agents.rule_scraper import RuleScraper


def seed_nsw_rules(force: bool = False) -> bool:
    """Seed NSW rules file."""
    print("🌱 Seeding NSW grant rules...")

    scraper = RuleScraper()
    rules = scraper.scrape_state_rules("NSW", force_refresh=force)

    if rules:
        print(f"✅ NSW rules saved to src/data/nsw_rules.json")
        print(f"   Grant: {rules['grant_name']}")
        print(f"   Amount: ${rules['rules']['grant_amount']:,}")
        return True
    else:
        print("❌ Failed to seed NSW rules")
        return False


def seed_sample_users() -> None:
    """Verify sample users file exists."""
    path = Path("src/data/sample_users.json")
    if path.exists():
        with open(path) as f:
            data = json.load(f)
        print(f"✅ Sample users loaded: {len(data['test_cases'])} test cases")
    else:
        print("⚠️  sample_users.json not found")


def main():
    """Main seeding function."""
    import argparse

    parser = argparse.ArgumentParser(description="Seed demo data")
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Force re-seed even if files exist",
    )
    parser.add_argument(
        "--rules-only",
        action="store_true",
        help="Only seed rules",
    )
    parser.add_argument(
        "--users-only",
        action="store_true",
        help="Only verify sample users",
    )

    args = parser.parse_args()

    success = True

    if not args.users_only:
        success = seed_nsw_rules(force=args.force) and success

    if not args.rules_only:
        seed_sample_users()

    if success:
        print("\n✅ Seeding complete!")
        print("\nNext steps:")
        print("  1. Run tests: pytest")
        print("  2. Try CLI: python src/chatbot/cli.py")
        print("  3. Start Rasa: rasa train && rasa shell")
        return 0
    else:
        print("\n❌ Seeding failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
