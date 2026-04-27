#!/usr/bin/env python3
"""
Command-line interface for FHBG Eligibility Bot.

Provides an interactive CLI for testing eligibility without Rasa.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.agents.conversation_manager import ConversationManager
from src.utils.helpers import setup_logging


def interactive_mode():
    """Run interactive CLI session."""
    manager = ConversationManager()
    setup_logging()

    print("\n" + "=" * 70)
    print("🏡 FHBG Eligibility Bot - Interactive CLI")
    print("=" * 70)
    print("Type 'help' for commands, 'exit' to quit.\n")

    print(manager.get_next_prompt())

    while True:
        try:
            user_input = input("\n> ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["exit", "quit", "bye"]:
                print("\n👋 Thank you for using FHBG Eligibility Bot!")
                break

            if user_input.lower() in ["help", "?"]:
                print("\nCommands:")
                print("  help - Show this help message")
                print("  restart - Start over")
                print("  status - Show current conversation status")
                print("  export - Export current result to JSON")
                print("  exit - Quit the application")
                print("  <any other input> - Answer the current question")
                continue

            if user_input.lower() == "restart":
                manager.reset()
                print("\n🔄 Starting over...")
                print(manager.get_next_prompt())
                continue

            if user_input.lower() == "status":
                summary = manager.get_summary()
                print("\n📊 Conversation Status:")
                print(f"  State: {summary['state']}")
                print(f"  Profile: {json.dumps(summary['user_profile'], indent=2)}")
                if summary.get("eligibility_status"):
                    print(f"  Eligibility: {summary['eligibility_status']}")
                    print(f"  Grant Amount: ${summary.get('grant_amount', 0):,.0f}")
                continue

            if user_input.lower() == "export" and manager.eligibility_report:
                export_data = {
                    "user_profile": manager.user_profile.to_dict(),
                    "eligibility_report": {
                        "status": manager.eligibility_report.status.value,
                        "state": manager.eligibility_report.state,
                        "grant_amount": manager.eligibility_report.grant_amount,
                        "grant_name": manager.eligibility_report.grant_name,
                        "passed_rules": manager.eligibility_report.passed_rules,
                        "missing_requirements": manager.eligibility_report.missing_requirements,
                        "next_steps": manager.eligibility_report.next_steps,
                        "sources": manager.eligibility_report.sources,
                    }
                }
                filename = f"eligibility_export_{Path(__file__).stem}.json"
                with open(filename, "w") as f:
                    json.dump(export_data, f, indent=2)
                print(f"\n✅ Exported to {filename}")
                continue

            # Process regular input
            response = manager.process_input(user_input)
            print(f"\n🤖 {response}")

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            sys.exit(0)
        except Exception as e:
            print(f"\n⚠️  Error: {e}")
            import logging
            logging.exception("Conversation error")


def quick_check_mode(args):
    """Run single eligibility check from command line arguments."""
    from src.agents.rule_scraper import RuleScraper
    from src.agents.rule_interpreter import RuleInterpreter
    from src.utils.helpers import validate_financial_input

    # Validate financial inputs
    for field_name, value, max_val in [
        ("Income", args.income, 10_000_000),
        ("Property price", args.property_price, 50_000_000),
    ]:
        is_valid, error_msg = validate_financial_input(value, field_name, min_val=0, max_val=max_val)
        if not is_valid:
            print(f"❌ Invalid {field_name.lower()}: {error_msg}")
            return 1

    # Load rules using RuleScraper
    scraper = RuleScraper()
    rules = scraper.scrape_state_rules(args.state)
    if not rules:
        print(f"❌ Could not load rules for {args.state}")
        return 1

    # Create interpreter
    interpreter = RuleInterpreter(rules)

    # Prepare user data
    user_data = {
        "state": args.state,
        "income": args.income,
        "property_price": args.property_price,
        "first_home_buyer": args.first_home,
        "citizenship_status": args.citizenship,
        "will_reside": args.will_reside,
        "property_is_new": args.is_new,
    }

    # Validate
    report = interpreter.validate_eligibility(user_data)

    # Print results
    print("\n" + "=" * 60)
    print(f"🏡 FHBG Eligibility Check - {args.state}")
    print("=" * 60)

    if report.status.value == "eligible":
        print(f"✅ ELIGIBLE")
        print(f"💰 Grant Amount: ${report.grant_amount:,.0f}")
    else:
        print(f"❌ NOT ELIGIBLE")
        if report.missing_requirements:
            print("\n🔴 Missing requirements:")
            for req in report.missing_requirements:
                print(f"  • {req}")

    print(f"\n📋 Summary:")
    print(f"  State: {args.state}")
    print(f"  Income: ${args.income:,.0f}")
    print(f"  Property: ${args.property_price:,.0f}")
    print(f"  First home: {'Yes' if args.first_home else 'No'}")

    # Print next steps compactly
    print(f"\n➡️  Next steps:")
    for step in report.next_steps[:3]:
        print(f"  {step}")

    return 0 if report.status.value == "eligible" else 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="FHBG Eligibility Bot CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python cli.py

  # Quick check (non-interactive)
  python cli.py check --state NSW --income 80000 --property-price 700000 --first-home

  # Run with debug logging
  python cli.py --log-level DEBUG

Interactive Commands:
  help    - Show help
  restart - Start over
  status  - Show current status
  export  - Export result to JSON
  exit    - Quit
        """,
    )

    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Set logging level",
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # 'check' subcommand for non-interactive checks
    check_parser = subparsers.add_parser(
        "check", help="Run a single eligibility check without interactive mode"
    )
    check_parser.add_argument("--state", required=True, choices=["NSW", "VIC", "QLD", "WA"])
    check_parser.add_argument("--income", type=float, required=True, help="Annual income")
    check_parser.add_argument("--property-price", type=float, required=True, help="Property price")
    check_parser.add_argument("--first-home", action="store_true", help="First home buyer")
    check_parser.add_argument("--citizenship", default="citizen", help="Citizenship status")
    check_parser.add_argument("--will-reside", action="store_true", help="Will reside in property")
    check_parser.add_argument("--is-new", action="store_true", help="Property is newly built")

    args = parser.parse_args()

    # Setup logging
    setup_logging(level=args.log_level)

    if args.command == "check":
        return quick_check_mode(args)
    else:
        # Interactive mode (default)
        interactive_mode()
        return 0


if __name__ == "__main__":
    sys.exit(main())
