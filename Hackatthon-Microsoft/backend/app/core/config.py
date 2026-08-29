import os
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseModel):
    PROJECT_NAME: str = "Maritime Operations Intelligence Platform"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # AI / LLM Configurations
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "auto")  # "azure_openai", "openai", "gemini", or "mock"
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")
    AZURE_OPENAI_API_KEY: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    AZURE_OPENAI_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    AZURE_OPENAI_DEPLOYMENT_NAME: str = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
    
    # Engine Settings
    SPATIAL_SEARCH_RADIUS_NM: float = 120.0
    CRITICAL_RISK_THRESHOLD: float = 75.0
    HIGH_RISK_THRESHOLD: float = 50.0
    WATCH_RISK_THRESHOLD: float = 25.0
    
    # Simulation Settings
    FLEET_SIZE: int = 50
    DEFAULT_WEATHER_UPDATE_INTERVAL_SEC: int = 15


settings = Settings()
