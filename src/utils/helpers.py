"""Utility functions for FHBG Eligibility Bot."""

import logging
import sys
from pathlib import Path
from typing import Optional

import dotenv


def setup_logging(level: str = "INFO") -> None:
    """Configure application logging.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR).
    """
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )


def load_env(env_file: Optional[str] = None) -> None:
    """Load environment variables from .env file.

    Args:
        env_file: Path to .env file. Defaults to .env in project root.
    """
    if env_file:
        dotenv.load_dotenv(env_file)
    else:
        dotenv.load_dotenv()


def get_project_root() -> Path:
    """Get project root directory."""
    return Path(__file__).parent.parent.parent


def validate_input(value: Any, value_type: type, min_val: Optional[float] = None, max_val: Optional[float] = None) -> tuple[bool, str]:
    """Validate user input.

    Args:
        value: Input value to validate.
        value_type: Expected type (int, float, str, bool).
        min_val: Minimum allowed value (for numeric types).
        max_val: Maximum allowed value (for numeric types).

    Returns:
        Tuple of (is_valid, error_message).
    """
    try:
        if value_type == float:
            val = float(value)
            if min_val is not None and val < min_val:
                return False, f"Value must be at least {min_val}"
            if max_val is not None and val > max_val:
                return False, f"Value cannot exceed {max_val}"
            return True, ""
        elif value_type == int:
            val = int(value)
            if min_val is not None and val < min_val:
                return False, f"Value must be at least {min_val}"
            if max_val is not None and val > max_val:
                return False, f"Value cannot exceed {max_val}"
            return True, ""
        elif value_type == bool:
            if isinstance(value, str):
                return value.lower() in ["yes", "y", "true", "t", "1"], "Please answer yes/no"
            return bool(value), ""
        elif value_type == str:
            if not value or not value.strip():
                return False, "Value cannot be empty"
            return True, ""
        return True, ""
    except (ValueError, TypeError):
        return False, f"Invalid {value_type.__name__} value"


def validate_financial_input(value: float, field_name: str, min_val: float = 0, max_val: float = 10_000_000) -> tuple[bool, str]:
    """Validate financial inputs (income, property price) with bounds.

    Args:
        value: Numeric value to validate.
        field_name: Human-readable name (e.g., "Income", "Property price").
        min_val: Minimum allowed value (default: 0).
        max_val: Maximum allowed value (default: $10M).

    Returns:
        Tuple of (is_valid, error_message).
    """
    if value < min_val:
        return False, f"{field_name} must be at least ${min_val:,.0f}"
    if value > max_val:
        return False, f"{field_name} cannot exceed ${max_val:,.0f}"
    return True, ""


def sanitize_string(value: str, max_length: int = 200) -> str:
    """Sanitize user-provided string input.

    Strips whitespace, truncates to max_length, removes control characters.

    Args:
        value: Raw string input.
        max_length: Maximum allowed length.

    Returns:
        Sanitized string.
    """
    # Strip surrounding whitespace
    cleaned = value.strip()
    # Remove control characters (except newline, tab)
    cleaned = "".join(c for c in cleaned if ord(c) >= 32 or c in "\n\t")
    # Truncate
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length]
    return cleaned


def format_currency(amount: float) -> str:
    """Format number as Australian currency."""
    return f"${amount:,.0f}"


def normalize_state(state: str) -> Optional[str]:
    """Normalize state input to standard abbreviation."""
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
    return state_map.get(state.strip().lower())
