import os
from typing import Optional
from pydantic import BaseSettings

class Settings(BaseSettings):
    # API Configuration
    app_title: str = "Bank Phishing Detector"
    app_version: str = "1.0.0"
    app_description: str = "Production-ready phishing detection service using Google Gemini API"
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    
    # Google Gemini API
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-1.5-pro"
    gemini_temperature: float = 0.1
    gemini_max_tokens: int = 2048
    
    # Risk Scoring Weights
    deterministic_weight: float = 0.6
    gemini_weight: float = 0.4
    
    # Thresholds
    high_risk_threshold: float = 70.0
    medium_risk_threshold: float = 40.0
    
    # Security
    allowed_origins: list = ["*"]
    max_request_size: int = 10 * 1024 * 1024  # 10MB
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    
    class Config:
        env_file = ".env"
        env_prefix = "PHISHING_DETECTOR_"

settings = Settings()
