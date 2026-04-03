"""
Configuration file for API keys, database, and settings
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).parent

# ── Database Configuration ─────────────────────────────────────────
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:farming123@localhost:5432/smart_farming",
)

# ── API Keys ───────────────────────────────────────────────────────
DATA_GOV_IN_API_KEY = os.getenv("DATA_GOV_IN_API_KEY", "")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")

# Alternative: Read from a local config file (create this file with your API key)
CONFIG_FILE = BASE_DIR / "api_config.json"

def get_data_gov_api_key():
    """
    Get the data.gov.in API key from environment or config file
    """
    # First try environment variable
    if DATA_GOV_IN_API_KEY:
        return DATA_GOV_IN_API_KEY
    
    # Try reading from config file
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
    """
    Get the OpenWeather API key from environment or config file
    """
    # First try environment variable
    if OPENWEATHER_API_KEY:
        return OPENWEATHER_API_KEY
    
    # Try reading from config file
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

# ── API Configuration Dict (legacy compat) ─────────────────────────
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
