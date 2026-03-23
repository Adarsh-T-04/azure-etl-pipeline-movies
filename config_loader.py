"""
Config Loader — Reads YAML config and injects environment variable overrides.
Sensitive values (passwords, connection strings) should always come from env vars.
"""

import os
import logging
import yaml
from pathlib import Path

logger = logging.getLogger("AzureETL.Config")

# Env var overrides → config key path
ENV_OVERRIDES = {
    "AZURE_SQL_SERVER":   ("load", "server"),
    "AZURE_SQL_DATABASE": ("load", "database"),
    "AZURE_SQL_USER":     ("load", "username"),
    "AZURE_SQL_PASSWORD": ("load", "password"),
    "AZURE_SQL_TABLE":    ("load", "table_name"),
}


def load_config(config_path: str) -> dict:
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(path, "r") as f:
        config = yaml.safe_load(f)

    # Apply env var overrides (never hardcode secrets)
    for env_key, (section, field) in ENV_OVERRIDES.items():
        val = os.getenv(env_key)
        if val:
            config.setdefault(section, {})[field] = val
            logger.debug(f"Override applied: {env_key} → config[{section}][{field}]")

    _validate_config(config)
    return config


def _validate_config(config: dict):
    required = {
        "extract": ["required_cols"],
        "transform": [],
        "load": ["server", "database", "username", "password", "table_name"],
    }
    for section, fields in required.items():
        if section not in config:
            raise KeyError(f"Missing config section: [{section}]")
        for field in fields:
            if field not in config[section]:
                raise KeyError(f"Missing config key: [{section}][{field}]")
