"""Conversation Manager Agent for FHBG Eligibility Bot.

Manages the conversational flow, collects user inputs,
and orchestrates collaboration between other agents.
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum

logger = logging.getLogger(__name__)


class ConversationState(Enum):
    """Conversation stage states."""
    START = "start"
    COLLECTING_STATE = "collecting_state"
    COLLECTING_INCOME = "collecting_income"
    COLLECTING_PROPERTY_PRICE = "collecting_property_price"
    COLLECTING_FIRST_HOME = "collecting_first_home"
    COLLECTING_CITIZENSHIP = "collecting_citizenship"
    COLLECTING_RESIDENCY = "collecting_residency"
    COLLECTING_PROPERTY_TYPE = "collecting_property_type"
    PROCESSING = "processing"
    COMPLETE = "complete"


@dataclass
class UserProfile:
    """Container for user's collected information."""
    state: Optional[str] = None
    income: Optional[float] = None
    property_price: Optional[float] = None
    first_home_buyer: Optional[bool] = None
    citizenship_status: Optional[str] = None
    will_reside: Optional[bool] = None
    property_is_new: Optional[bool] = None

    def is_complete(self) -> bool:
        """Check if all required fields are filled."""
        required = [self.state, self.income, self.property_price, self.first_home_buyer]
        return all(x is not None for x in required)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {k: v for k, v in self.__dict__.items() if v is not None}


class ConversationManager:
    """Agent that manages chatbot conversation flow."""

    def __init__(self):
        """Initialize ConversationManager."""
        self.state = ConversationState.START
        self.user_profile = UserProfile()
        self.messages: List[str] = []
        self.eligibility_report = None
        self.rules = None

        # Conversation prompts
        self.prompts = {
            ConversationState.START: "Hello! I'll help you check your eligibility for the First Home Buyer Grant. Which state are you buying in? (NSW, VIC, QLD, WA)",
            ConversationState.COLLECTING_STATE: "Which state are you buying in?",  # Legacy, not used
            ConversationState.COLLECTING_INCOME: "What is your annual household income (before tax)? Please enter as a number (e.g., 80000)",
            ConversationState.COLLECTING_PROPERTY_PRICE: "What is the purchase price of the property? Please enter as a number (e.g., 700000)",
            ConversationState.COLLECTING_FIRST_HOME: "Is this your first home? (Please answer yes or no)",
            ConversationState.COLLECTING_CITIZENSHIP: "What is your citizenship/residency status? (e.g., Australian citizen, Permanent resident)",
            ConversationState.COLLECTING_RESIDENCY: "Do you intend to live in this property as your primary residence? (yes/no)",
            ConversationState.COLLECTING_PROPERTY_TYPE: "Is the property newly constructed? (yes/no) - Some grants only apply to new homes.",
            ConversationState.PROCESSING: "Let me check your eligibility...",
            ConversationState.COMPLETE: "Here are your results!",
        }

        # State validation
        self.supported_states = ["NSW", "VIC", "QLD", "WA"]

    def get_next_prompt(self) -> str:
        """Get the next question/prompt based on current state."""
        return self.prompts.get(self.state, "How can I help you?")

    def process_input(self, user_input: str) -> str:
        """Process user input and advance conversation.

        Args:
            user_input: Raw text from user.

        Returns:
            Bot response string.
        """
        self.messages.append(f"User: {user_input}")
        logger.debug(f"Processing input in state {self.state}: {user_input}")

        # Handle global commands (restart) from any state
        cmd = user_input.strip().lower()
        if cmd in ["restart", "start over", "begin again", "reset"]:
            self.reset()
            return self.get_next_prompt()

        # State machine processing
        if self.state == ConversationState.START:
            return self._handle_start(user_input)
        elif self.state == ConversationState.COLLECTING_STATE:
            return self._handle_state_input(user_input)
        elif self.state == ConversationState.COLLECTING_INCOME:
            return self._handle_income_input(user_input)
        elif self.state == ConversationState.COLLECTING_PROPERTY_PRICE:
            return self._handle_property_price_input(user_input)
        elif self.state == ConversationState.COLLECTING_FIRST_HOME:
            return self._handle_first_home_input(user_input)
        elif self.state == ConversationState.COLLECTING_CITIZENSHIP:
            return self._handle_citizenship_input(user_input)
        elif self.state == ConversationState.COLLECTING_RESIDENCY:
            return self._handle_residency_input(user_input)
        elif self.state == ConversationState.COLLECTING_PROPERTY_TYPE:
            return self._handle_property_type_input(user_input)
        elif self.state == ConversationState.PROCESSING:
            return self._handle_processing(user_input)
        elif self.state == ConversationState.COMPLETE:
            return self._handle_complete(user_input)
        else:
            return "I'm sorry, I got confused. Let's start over."

    def _handle_start(self, user_input: str) -> str:
        """Handle initial state - determine state selection."""
        self.user_profile.state = self._normalize_state(user_input)
        if not self.user_profile.state:
            return (
                "Please select a valid state: NSW, VIC, QLD, or WA.\n"
                "Which state are you buying in?"
            )

        # Load rules for this state
        from src.agents.rule_scraper import RuleScraper

        scraper = RuleScraper()
        self.rules = scraper.scrape_state_rules(self.user_profile.state)
        if not self.rules:
            return f"❌ Unable to load grant rules for {self.user_profile.state}. Please try again."

        self.state = ConversationState.COLLECTING_INCOME
        return self.get_next_prompt()

    def _handle_state_input(self, user_input: str) -> str:
        """This is legacy - state is handled in START now."""
        return self.get_next_prompt()

    def _handle_income_input(self, user_input: str) -> str:
        """Handle income input."""
        from src.utils.helpers import validate_financial_input

        try:
            clean = user_input.replace(",", "").replace("$", "")
            income = float(clean)
            is_valid, error_msg = validate_financial_input(
                income, "Income", min_val=0, max_val=10_000_000
            )
            if not is_valid:
                return f"Please enter a valid income: {error_msg}"
            self.user_profile.income = income
            self.state = ConversationState.COLLECTING_PROPERTY_PRICE
            return self.get_next_prompt()
        except ValueError:
            return "Please enter a valid number for your annual income (e.g., 80000):"

    def _handle_property_price_input(self, user_input: str) -> str:
        """Handle property price input."""
        from src.utils.helpers import validate_financial_input

        try:
            clean = user_input.replace(",", "").replace("$", "")
            price = float(clean)
            is_valid, error_msg = validate_financial_input(
                price, "Property price", min_val=0, max_val=50_000_000
            )
            if not is_valid:
                return f"Please enter a valid property price: {error_msg}"
            self.user_profile.property_price = price
            self.state = ConversationState.COLLECTING_FIRST_HOME
            return self.get_next_prompt()
        except ValueError:
            return "Please enter a valid number for the property price (e.g., 700000):"

    def _handle_first_home_input(self, user_input: str) -> str:
        """Handle first home buyer status."""
        normalized = user_input.strip().lower()
        if normalized in ["yes", "y", "true", "t", "yeah", "yep"]:
            self.user_profile.first_home_buyer = True
        elif normalized in ["no", "n", "false", "f", "nope"]:
            self.user_profile.first_home_buyer = False
        else:
            return "Please answer 'yes' or 'no'. Is this your first home?"

        self.state = ConversationState.COLLECTING_CITIZENSHIP
        return self.get_next_prompt()

    def _handle_citizenship_input(self, user_input: str) -> str:
        """Handle citizenship status."""
        from src.utils.helpers import sanitize_string

        # Sanitize input
        normalized = sanitize_string(user_input, max_length=100).lower()

        if "citizen" in normalized:
            self.user_profile.citizenship_status = "australian citizen"
        elif "permanent" in normalized or "pr" in normalized:
            self.user_profile.citizenship_status = "permanent resident"
        else:
            # For demo, allow other as neutral but sanitized
            self.user_profile.citizenship_status = sanitize_string(user_input, max_length=100)

        self.state = ConversationState.COLLECTING_RESIDENCY
        return self.get_next_prompt()

    def _handle_residency_input(self, user_input: str) -> str:
        """Handle residency intention."""
        normalized = user_input.strip().lower()
        if normalized in ["yes", "y", "true", "t", "yeah"]:
            self.user_profile.will_reside = True
        elif normalized in ["no", "n", "false", "f", "nope"]:
            self.user_profile.will_reside = False
        else:
            return "Please answer 'yes' or 'no'. Will you live in the property as your primary residence?"

        # Check if state rules require new construction
        rules_dict = self.rules.get("rules", {})
        if rules_dict.get("new_construction_only", False):
            self.state = ConversationState.COLLECTING_PROPERTY_TYPE
            return self.get_next_prompt()
        else:
            # Skip property type, proceed to processing
            self.state = ConversationState.PROCESSING
            return self.get_next_prompt()

    def _handle_property_type_input(self, user_input: str) -> str:
        """Handle property type (new vs existing)."""
        normalized = user_input.strip().lower()
        if normalized in ["yes", "y", "true", "t", "new", "brand new"]:
            self.user_profile.property_is_new = True
        elif normalized in ["no", "n", "false", "f", "existing", "old"]:
            self.user_profile.property_is_new = False
        else:
            return "Please answer 'yes' or 'no'. Is the property newly constructed?"

        self.state = ConversationState.PROCESSING
        return self.get_next_prompt()

    def _handle_processing(self, user_input: str) -> str:
        """Handle processing - skip user input and do validation."""
        # Import here to avoid circular dependencies
        from src.agents.rule_interpreter import RuleInterpreter

        interpreter = RuleInterpreter(self.rules)
        report = interpreter.validate_eligibility(self.user_profile.to_dict())
        self.eligibility_report = report

        # Format response
        if report.status.value == "eligible":
            response = (
                f"✅ **You are eligible for the {report.grant_name}!**\n\n"
                f"💰 **Grant Amount:** ${report.grant_amount:,.0f}\n\n"
            )
        else:
            response = (
                f"❌ **You are not currently eligible** for the {report.grant_name}.\n\n"
            )
            if report.missing_requirements:
                response += "🔴 **Missing requirements:**\n"
                for req in report.missing_requirements:
                    response += f"  • {req}\n"

        response += "\n📋 **Next Steps:**\n"
        for step in report.next_steps:
            response += f"  {step}\n"

        self.state = ConversationState.COMPLETE
        return response

    def _handle_complete(self, user_input: str) -> str:
        """Handle conversation completion."""
        if any(word in user_input.lower() for word in ["restart", "start over", "again"]):
            self.reset()
            return self.get_next_prompt()
        return (
            "Thank you for using the FHBG Eligibility Bot! "
            "Type 'restart' to check another property."
        )

    def _normalize_state(self, state_input: str) -> Optional[str]:
        """Normalize state input."""
        state_map = {
            "nsw": "NSW",
            "new south wales": "NSW",
            "vic": "VIC",
            "victoria": "VIC",
            "qld": "QLD",
            "queensland": "QLD",
            "wa": "WA",
            "western australia": "WA",
        }
        normalized = state_input.strip().lower()
        return state_map.get(normalized)

    def reset(self) -> None:
        """Reset conversation to initial state."""
        self.state = ConversationState.START
        self.user_profile = UserProfile()
        self.messages = []
        self.eligibility_report = None
        self.rules = None

    def get_summary(self) -> Dict[str, Any]:
        """Get conversation summary."""
        return {
            "state": self.state.value,
            "user_profile": self.user_profile.to_dict(),
            "eligibility_status": (
                self.eligibility_report.status.value if self.eligibility_report else None
            ),
            "grant_amount": self.eligibility_report.grant_amount if self.eligibility_report else None,
        }


def main():
    """CLI interface for testing conversation manager."""
    import sys

    manager = ConversationManager()
    print("\n🏡 FHBG Eligibility Bot - Interactive Demo")
    print("=" * 60)
    print(manager.get_next_prompt())

    while True:
        try:
            user_input = input("\n> ").strip()
            if user_input.lower() in ["exit", "quit", "bye"]:
                print("Goodbye!")
                break

            response = manager.process_input(user_input)
            print(f"\n🤖 Bot: {response}")

            if manager.state == ConversationState.COMPLETE:
                print("\n" + "=" * 60)
                summary = manager.get_summary()
                if summary.get("eligibility_status"):
                    print(f"✅ Final Status: {summary['eligibility_status']}")
                    print(f"💰 Grant: ${summary.get('grant_amount', 0):,.0f}")
                print("\nType 'restart' to check another property or 'exit' to quit.")

        except KeyboardInterrupt:
            print("\n\nInterrupted. Goodbye!")
            sys.exit(0)
        except Exception as e:
            logger.error(f"Error in conversation: {e}")
            print(f"⚠️  An error occurred: {e}")
            manager.reset()
            print("\nLet's start over.")
            print(manager.get_next_prompt())


if __name__ == "__main__":
    main()
