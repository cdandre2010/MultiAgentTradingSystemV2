from typing import Optional, Dict, Any, List
from pydantic import validator
from pydantic_settings import BaseSettings
import os
from pathlib import Path

class Settings(BaseSettings):
    # API settings
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "Multi-Agent Trading System"
    VERSION: str = "2.0.0"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    # Database URLs
    DATABASE_URI: Optional[str] = None
    NEO4J_URI: Optional[str] = None
    NEO4J_USERNAME: Optional[str] = None
    NEO4J_PASSWORD: Optional[str] = None
    INFLUXDB_URL: Optional[str] = None
    INFLUXDB_TOKEN: Optional[str] = None
    INFLUXDB_ORG: Optional[str] = None
    INFLUXDB_BUCKET: Optional[str] = None
    REDIS_URL: Optional[str] = None
    
    # JWT
    SECRET_KEY: str = "your-secret-key-here"  # In production, use a secure generated key
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Claude API
    ANTHROPIC_API_KEY: Optional[str] = None
    
    # Logging
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: str) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

settings = Settings()

# Ensure the required environment variables are present
def validate_settings() -> Dict[str, Any]:
    """Validate that all required settings are provided"""
    missing = []
    warnings = []
    
    # Critical settings
    if not settings.SECRET_KEY or settings.SECRET_KEY == "your-secret-key-here":
        warnings.append("SECRET_KEY not set or using default (insecure for production)")
    
    if not settings.ANTHROPIC_API_KEY:
        missing.append("ANTHROPIC_API_KEY")
    
    # Database settings - will be required later
    if not settings.DATABASE_URI:
        warnings.append("DATABASE_URI not set")
    
    if not settings.NEO4J_URI or not settings.NEO4J_USERNAME or not settings.NEO4J_PASSWORD:
        warnings.append("Neo4j connection details not fully configured")
    
    if not settings.INFLUXDB_URL or not settings.INFLUXDB_TOKEN:
        warnings.append("InfluxDB connection details not fully configured")
    
    return {
        "valid": len(missing) == 0,
        "missing": missing,
        "warnings": warnings,
    }