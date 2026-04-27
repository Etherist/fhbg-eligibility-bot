"""Configuration management for FHBG Eligibility Bot."""

import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

from src.utils.helpers import get_project_root


@dataclass
class Config:
    """Application configuration loaded from environment."""

    # Scraping
    scrape_delay: float = float(os.getenv("SCRAPE_DELAY", "2"))
    scrape_timeout: int = int(os.getenv("SCRAPE_TIMEOUT", "30"))

    # Caching
    rule_cache_ttl: int = int(os.getenv("RULE_CACHE_TTL", "86400"))  # 24h

    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    # Paths
    data_path: str = os.getenv("NSW_RULES_PATH", "src/data/")
    report_output_dir: str = os.getenv("REPORT_OUTPUT_DIR", "reports/")

    # Rasa
    rasa_model_path: str = os.getenv("RASA_MODEL_PATH", "models/")
    rasa_action_port: int = int(os.getenv("RASA_ACTION_SERVER_PORT", "5055"))

    # Project paths
    project_root: Path = get_project_root()

    @classmethod
    def load(cls, env_file: Optional[str] = None) -> "Config":
        """Load configuration from environment."""
        load_dotenv(env_file)
        return cls()


# Global config instance
config = Config.load()
