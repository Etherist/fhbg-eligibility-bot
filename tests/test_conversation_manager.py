"""Unit tests for conversation_manager agent."""

import pytest

from src.agents.conversation_manager import ConversationManager, ConversationState, UserProfile


class TestConversationManager:
    """Test suite for ConversationManager."""

    @pytest.fixture
    def manager(self):
        """Create ConversationManager instance."""
        return ConversationManager()

    def test_initial_state_is_start(self, manager):
        """Test initial conversation state."""
        assert manager.state == ConversationState.START

    def test_get_initial_prompt(self, manager):
        """Test initial greeting message."""
        prompt = manager.get_next_prompt()
        assert "which state" in prompt.lower()
        assert "nsw" in prompt.lower()

    def test_handle_valid_state_transitions_to_income(self, manager):
        """Test entering valid state transitions to income collection."""
        response = manager.process_input("NSW")
        assert manager.state == ConversationState.COLLECTING_INCOME
        assert manager.user_profile.state == "NSW"
        assert "income" in response.lower()

    def test_handle_invalid_state_keeps_in_state_collection(self, manager):
        """Test invalid state keeps conversation in state collection."""
        response = manager.process_input("XYZ")
        # Should remain in COLLECTING_STATE or go back to ask for state
        assert manager.state in [ConversationState.COLLECTING_STATE, ConversationState.START]
        assert "valid state" in response.lower()

    def test_handle_income_valid_number(self, manager):
        """Test valid income input."""
        manager.state = ConversationState.COLLECTING_INCOME
        manager.user_profile.state = "NSW"

        response = manager.process_input("80000")

        assert manager.user_profile.income == 80000.0
        assert manager.state == ConversationState.COLLECTING_PROPERTY_PRICE
        assert "property" in response.lower()

    def test_handle_invalid_income_prompts_retry(self, manager):
        """Test invalid income input triggers retry."""
        manager.state = ConversationState.COLLECTING_INCOME
        manager.user_profile.state = "NSW"

        response = manager.process_input("abc")

        assert manager.state == ConversationState.COLLECTING_INCOME
        assert "valid number" in response.lower()

    def test_handle_property_price_valid(self, manager):
        """Test valid property price input."""
        manager.state = ConversationState.COLLECTING_PROPERTY_PRICE
        manager.user_profile.state = "NSW"
        manager.user_profile.income = 80000

        response = manager.process_input("700000")

        assert manager.user_profile.property_price == 700000.0
        assert manager.state == ConversationState.COLLECTING_FIRST_HOME

    def test_handle_first_home_yes(self, manager):
        """Test first home buyer 'yes'."""
        manager.state = ConversationState.COLLECTING_FIRST_HOME
        manager.user_profile.state = "NSW"
        manager.user_profile.income = 80000
        manager.user_profile.property_price = 700000

        response = manager.process_input("yes")

        assert manager.user_profile.first_home_buyer is True
        assert manager.state == ConversationState.COLLECTING_CITIZENSHIP

    def test_handle_first_home_no(self, manager):
        """Test first home buyer 'no'."""
        manager.state = ConversationState.COLLECTING_FIRST_HOME
        manager.user_profile.state = "NSW"
        manager.user_profile.income = 80000
        manager.user_profile.property_price = 700000

        response = manager.process_input("no")

        assert manager.user_profile.first_home_buyer is False
        assert manager.state == ConversationState.COLLECTING_CITIZENSHIP

    def test_handle_citizenship_creates_profile(self, manager):
        """Test citizenship input."""
        manager.state = ConversationState.COLLECTING_CITIZENSHIP
        manager.user_profile.state = "NSW"
        manager.user_profile.income = 80000
        manager.user_profile.property_price = 700000
        manager.user_profile.first_home_buyer = True

        response = manager.process_input("citizen")

        assert "citizen" in manager.user_profile.citizenship_status.lower()
        assert manager.state == ConversationState.COLLECTING_RESIDENCY

    def test_residency_yes_skips_property_type_in_nsw(self, manager):
        """Test that NSW doesn't require property type (no new construction requirement)."""
        manager.state = ConversationState.COLLECTING_RESIDENCY
        manager.user_profile.state = "NSW"
        manager.user_profile.income = 80000
        manager.user_profile.property_price = 700000
        manager.user_profile.first_home_buyer = True
        manager.user_profile.citizenship_status = "citizen"
        # Provide rules for eligibility check
        manager.rules = {
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
            "sources": [],
        }

        response = manager.process_input("yes")

        assert manager.user_profile.will_reside is True
        # Should proceed directly to processing since NSW has no new construction requirement
        assert manager.state == ConversationState.PROCESSING

    def test_residency_no_transitions_to_processing(self, manager):
        """Test that 'no' to residency still goes to processing (eligibility check will fail)."""
        manager.state = ConversationState.COLLECTING_RESIDENCY
        manager.user_profile.state = "NSW"
        manager.user_profile.income = 80000
        manager.user_profile.property_price = 700000
        manager.user_profile.first_home_buyer = True
        manager.user_profile.citizenship_status = "citizen"
        # Provide rules for eligibility check
        manager.rules = {
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
            "sources": [],
        }

        response = manager.process_input("no")

        assert manager.user_profile.will_reside is False
        assert manager.state == ConversationState.PROCESSING

    def test_processing_produces_result(self, manager):
        """Test processing state generates eligibility result."""
        # Setup complete profile
        manager.user_profile.state = "NSW"
        manager.user_profile.income = 80000
        manager.user_profile.property_price = 700000
        manager.user_profile.first_home_buyer = True
        manager.user_profile.citizenship_status = "citizen"
        manager.user_profile.will_reside = True
        manager.state = ConversationState.PROCESSING
        # Provide rules for eligibility check
        manager.rules = {
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
            "sources": [],
        }

        response = manager.process_input("")

        assert manager.state == ConversationState.COMPLETE
        assert manager.eligibility_report is not None
        assert "eligible" in response.lower() or "eligible" in response.lower()

    def test_restart_resets_conversation(self, manager):
        """Test restart command resets all data."""
        # Fill some data
        manager.user_profile.state = "NSW"
        manager.user_profile.income = 80000
        manager.state = ConversationState.COLLECTING_PROPERTY_PRICE

        response = manager.process_input("restart")

        assert manager.state == ConversationState.START
        assert manager.user_profile.state is None
        assert manager.user_profile.income is None

    def test_user_profile_is_complete_returns_correct(self, manager):
        """Test UserProfile.is_complete() method."""
        profile = UserProfile()
        assert profile.is_complete() is False

        profile.state = "NSW"
        assert profile.is_complete() is False

        profile.income = 80000
        assert profile.is_complete() is False

        profile.property_price = 700000
        assert profile.is_complete() is False

        profile.first_home_buyer = True
        assert profile.is_complete() is True

    def test_user_profile_to_dict_excludes_nones(self, manager):
        """Test UserProfile.to_dict() excludes None values."""
        profile = UserProfile()
        profile.state = "NSW"
        profile.income = 80000
        # property_price, first_home_buyer are None

        d = profile.to_dict()

        assert "state" in d
        assert "income" in d
        assert "property_price" not in d
        assert "first_home_buyer" not in d

    def test_normalize_state_lowercase_input(self, manager):
        """Test state normalization for various inputs."""
        assert manager._normalize_state("nsw") == "NSW"
        assert manager._normalize_state("New South Wales") == "NSW"
        assert manager._normalize_state("VIC") == "VIC"
        assert manager._normalize_state("victoria") == "VIC"
        assert manager._normalize_state("QLD") == "QLD"
        assert manager._normalize_state("WA") == "WA"
        assert manager._normalize_state("NY") is None
