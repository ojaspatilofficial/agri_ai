import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# ── Database Configuration ──────────────────────────────────────────
# Default to SQLite for easy setup, but allow override via env for PostgreSQL
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    f"sqlite+aiosqlite:///{BASE_DIR}/agri_ai.db"
)

# ── API Keys & Endpoints ───────────────────────────────────────────
OPENWEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "")
DATA_GOV_API_KEY = os.getenv("DATA_GOV_API_KEY", "")
CONFIG_FILE = BASE_DIR / "config.json"

def get_data_gov_api_key():
    """Get the Data.gov.in API key from environment or config file"""
    if DATA_GOV_API_KEY:
        return DATA_GOV_API_KEY
    if CONFIG_FILE.exists():
        import json
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                return config.get('data_gov_api_key', '')
        except:
            pass
    return ""

def get_openweather_api_key():
    """Get the OpenWeather API key from environment or config file"""
    if OPENWEATHER_API_KEY:
        return OPENWEATHER_API_KEY
    if CONFIG_FILE.exists():
        import json
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                return config.get('openweather_api_key', '')
        except:
            pass
    return ""

# ── Ollama / LLM Configuration ────────────────────────────────────
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral:latest")

# ── Unified Configuration Dict ─────────────────────────────────────
API_CONFIG = {
    "data_gov_api_key": get_data_gov_api_key(),
    "data_gov_base_url": "https://api.data.gov.in/resource",
    "market_data_endpoint": "market-prices",
    "openweather_api_key": get_openweather_api_key(),
    "openweather_base_url": "https://api.openweathermap.org/data/2.5",
    "database_url": DATABASE_URL,
    "ollama_base_url": OLLAMA_BASE_URL,
    "ollama_model": OLLAMA_MODEL,
}

# ── Logging ────────────────────────────────────────────────────────
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
