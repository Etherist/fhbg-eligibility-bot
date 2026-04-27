"""Rasa Custom Actions for FHBG Eligibility Bot.

Integrates the FHBG agents (scraper, interpreter, reporter)
with the Rasa conversational AI framework.
"""

import json
import logging
import os
from typing import Dict, Any, Text

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, EventType
from rasa_sdk.types import DomainDict

logger = logging.getLogger(__name__)


class ActionCheckEligibility(Action):
    """Custom action to check eligibility using our agents."""

    def name(self) -> Text:
        return "action_check_eligibility"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> list[EventType]:
        """Main eligibility check action."""
        logger.info("Running action_check_eligibility")

        try:
            # Import our agents
            from src.agents.rule_scraper import RuleScraper
            from src.agents.rule_interpreter import RuleInterpreter

            # Extract slots (user data)
            state = tracker.get_slot("state")
            income = tracker.get_slot("income")
            property_price = tracker.get_slot("property_price")
            first_home = tracker.get_slot("first_home_buyer")
            citizenship = tracker.get_slot("citizenship_status")
            will_reside = tracker.get_slot("will_reside")
            property_is_new = tracker.get_slot("property_is_new")

            # Validate we have minimum required data
            if not all([state, income, property_price, first_home is not None]):
                missing = []
                if not state:
                    missing.append("state")
                if income is None:
                    missing.append("income")
                if property_price is None:
                    missing.append("property_price")
                if first_home is None:
                    missing.append("first_home_buyer")

                dispatcher.utter_message(
                    text=f"❌ Missing required information: {', '.join(missing)}. "
                         "Let's start over."
                )
                return [SlotSet("eligibility_status", "incomplete")]

            # Load rules
            scraper = RuleScraper()
            rules = scraper.scrape_state_rules(state)
            if not rules:
                dispatcher.utter_message(
                    text=f"❌ Unable to load grant rules for {state}. "
                         "Please try again or select a different state."
                )
                return [SlotSet("eligibility_status", "error")]

            # Create interpreter and check eligibility
            interpreter = RuleInterpreter(rules)
            user_data = {
                "state": state,
                "income": float(income),
                "property_price": float(property_price),
                "first_home_buyer": bool(first_home),
                "citizenship_status": str(citizenship) if citizenship else "unknown",
                "will_reside": bool(will_reside) if will_reside is not None else None,
                "property_is_new": bool(property_is_new) if property_is_new is not None else None,
            }

            report = interpreter.validate_eligibility(user_data)

            # Store report in slot (serialize to JSON)
            report_dict = {
                "status": report.status.value,
                "state": report.state,
                "grant_amount": report.grant_amount,
                "grant_name": report.grant_name,
                "passed_rules": report.passed_rules,
                "failed_rules": [
                    {"rule_name": fr.rule_name, "message": fr.message}
                    for fr in report.failed_rules
                ],
                "warnings": report.warnings,
                "missing_requirements": report.missing_requirements,
                "next_steps": report.next_steps,
                "sources": report.sources,
            }

            # Send summary to user
            self._send_summary(dispatcher, user_data, report)

            events = [
                SlotSet("eligibility_status", report.status.value),
                SlotSet("eligibility_report", json.dumps(report_dict)),
            ]

            logger.info(
                f"Eligibility check complete: {report.status.value}, "
                f"grant: ${report.grant_amount:,}"
            )
            return events

        except Exception as e:
            logger.error(f"Error in action_check_eligibility: {e}", exc_info=True)
            dispatcher.utter_message(
                text=f"❌ An error occurred while checking eligibility: {str(e)}. "
                     "Please try again."
            )
            return [SlotSet("eligibility_status", "error")]

    def _send_summary(
        self,
        dispatcher: CollectingDispatcher,
        user_data: Dict[str, Any],
        report: Any,
    ) -> None:
        """Send eligibility summary to user."""
        if report.status.value == "eligible":
            message = (
                f"✅ **You are eligible for the {report.grant_name}!**\n\n"
                f"💰 **Grant Amount:** ${report.grant_amount:,.0f}\n\n"
            )
        else:
            message = (
                f"❌ **You are currently not eligible** for the {report.grant_name}.\n\n"
            )
            if report.missing_requirements:
                message += "🔴 **Missing requirements:**\n"
                for req in report.missing_requirements:
                    message += f"  • {req}\n"

        message += "\n📋 **Next Steps:**\n"
        for step in report.next_steps[:5]:  # Limit to first 5 steps
            message += f"  {step}\n"

        if report.sources:
            message += f"\n📚 *Source: {', '.join(report.sources)}*"

        dispatcher.utter_message(text=message)


class ActionGenerateReport(Action):
    """Custom action to generate a downloadable report."""

    def name(self) -> Text:
        return "action_generate_report"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> list[EventType]:
        """Generate and send report."""
        logger.info("Running action_generate_report")

        try:
            from src.agents.reporter import ReportGenerator

            # Retrieve eligibility report from slot
            report_json = tracker.get_slot("eligibility_report")
            if not report_json:
                dispatcher.utter_message(
                    text="No eligibility data found. Please complete the eligibility check first."
                )
                return []

            # Reconstruct report object
            report_data = json.loads(report_json)

            # Build user profile from slots
            user_profile = {
                "state": tracker.get_slot("state"),
                "income": tracker.get_slot("income"),
                "property_price": tracker.get_slot("property_price"),
                "first_home_buyer": tracker.get_slot("first_home_buyer"),
                "citizenship_status": tracker.get_slot("citizenship_status"),
                "will_reside": tracker.get_slot("will_reside"),
                "property_is_new": tracker.get_slot("property_is_new"),
            }

            # Generate report
            config = ReportGenerator()
            output_format = "markdown"  # For chat display
            report_content = config._generate_markdown({
                "user": user_profile,
                "report": type("Report", (), report_data)(),
                "timestamp": __import__('datetime').datetime.now(),
            })

            # Send as code block for easy reading
            dispatcher.utter_message(text="Here's your detailed eligibility report:")
            dispatcher.utter_message(text=f"```\n{report_content}\n```")

            # Also generate and save file
            saved_path = config.generate_report(user_profile, type("Report", (), report_data)())
            if saved_path:
                dispatcher.utter_message(
                    text=f"📄 A copy of your report has been saved to: {saved_path}"
                )

            return []

        except Exception as e:
            logger.error(f"Error generating report: {e}")
            dispatcher.utter_message(
                text=f"❌ Could not generate report: {str(e)}"
            )
            return []


class ActionResetSlots(Action):
    """Reset all slots to restart conversation."""

    def name(self) -> Text:
        return "action_reset_slots"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> list[EventType]:
        """Reset all collected slots."""
        logger.info("Resetting slots")

        slots_to_reset = [
            "state",
            "income",
            "property_price",
            "first_home_buyer",
            "citizenship_status",
            "will_reside",
            "property_is_new",
            "eligibility_report",
            "eligibility_status",
        ]

        events = [SlotSet(slot, None) for slot in slots_to_reset]
        return events


class ActionDefaultFallback(Action):
    """Default fallback for when NLU confidence is low."""

    def name(self) -> Text:
        return "action_default_fallback"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> list[EventType]:
        """Handle fallback."""
        dispatcher.utter_message(
            text="I'm not sure I understood that. Could you rephrase or answer the current question?"
        )
        return []
