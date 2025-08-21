
# config/settings.py
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # LangSmith Configuration
    LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
    LANGSMITH_TRACING = os.getenv("LANGSMITH_TRACING", "true").lower() == "true"
    LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "aircraft-research-agent")
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Search Configuration
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
    
    # Scraping Configuration
    REQUEST_TIMEOUT = 30
    MAX_RETRIES = 3
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

settings = Settings()
