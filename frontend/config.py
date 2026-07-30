"""Runtime configuration for the frontend service."""

import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_DB_PATH = "out/.meta.json"
DEFAULT_CONFIG_PATH = "config.yaml"


@dataclass(frozen=True)
class Settings:
    """Frontend settings, resolved from environment variables.

    Attributes:
        db_path: Path to the database file written by the encoder.
        config_path: Path to the encoder config file.

    """

    db_path: Path
    config_path: Path

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            db_path=Path(os.environ.get("O3_DB_PATH", DEFAULT_DB_PATH)),
            config_path=Path(os.environ.get("O3_CONFIG_PATH", DEFAULT_CONFIG_PATH)),
        )


def get_settings() -> Settings:
    """Settings dependency (re-read per request so env changes take effect on reload)."""
    return Settings.from_env()

