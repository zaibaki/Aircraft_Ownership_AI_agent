# config/settings.py
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

# Base paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
FAA_DB_DIR = DATA_DIR / "faa_db"
CACHE_DIR = DATA_DIR / "cache"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
FAA_DB_DIR.mkdir(exist_ok=True)
CACHE_DIR.mkdir(exist_ok=True)

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
LANGSMITH_TRACING = os.getenv("LANGSMITH_TRACING", "true")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# FAA URLs
FAA_BASE_URL = "https://registry.faa.gov"
FAA_DOWNLOAD_URL = "https://www.faa.gov/licenses_certificates/aircraft_certification/aircraft_registry/releasable_aircraft_download"

# OpenCorporates
OPENCORPORATES_BASE_URL = "https://opencorporates.com/reconcile"

# Cache settings
CACHE_TTL = 3600 * 24  # 24 hours
USE_REDIS = os.getenv("REDIS_URL") is not None
