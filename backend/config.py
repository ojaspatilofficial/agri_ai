"""
Configuration file for API keys and settings
"""
import os
import json
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent

# Environment variables
DATA_GOV_IN_API_KEY = os.getenv("DATA_GOV_IN_API_KEY", "")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
GROK_API_KEY        = os.getenv("GROK_API_KEY", "")
GROQ_API_KEY        = os.getenv("GROQ_API_KEY", "")

# Local config file
CONFIG_FILE = BASE_DIR / "api_config.json"

def _read_config_file() -> dict:
    """Read api_config.json once."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

_cfg = _read_config_file()


def get_data_gov_api_key() -> str:
    return DATA_GOV_IN_API_KEY or _cfg.get("data_gov_api_key", "")


def get_openweather_api_key() -> str:
    return OPENWEATHER_API_KEY or _cfg.get("openweather_api_key", "")


def get_grok_api_key() -> str:
    """xAI Grok key (optional)."""
    return GROK_API_KEY or _cfg.get("grok_api_key", "")


def get_groq_api_key() -> str:
    """Groq (console.groq.com) key — used for vision-based disease detection."""
    return GROQ_API_KEY or _cfg.get("groq_api_key", "")


# ── Exported config dict ────────────────────────────────────────
API_CONFIG = {
    "data_gov_api_key":     get_data_gov_api_key(),
    "data_gov_base_url":    "https://api.data.gov.in/resource",
    "market_data_endpoint": "market-prices",
    "openweather_api_key":  get_openweather_api_key(),
    "openweather_base_url": "https://api.openweathermap.org/data/2.5",
    "grok_api_key":         get_grok_api_key(),
    "grok_base_url":        "https://api.x.ai/v1",
    "grok_vision_model":    "grok-2-vision-1212",
    "groq_api_key":         get_groq_api_key(),
    "groq_base_url":        "https://api.groq.com/openai/v1",
    "groq_vision_model":    "meta-llama/llama-4-scout-17b-16e-instruct",
}
