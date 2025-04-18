from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # API Keys
    YANDEX_SEARCH_API_KEY: str = os.getenv("YANDEX_SEARCH_API_KEY", "AQVNzFVoXQpLzucXJ-LUM1h1GaOgo3N1mdwjI-0u")
    SPARK_API_KEY: str = os.getenv("SPARK_API_KEY", "")
    
    # API Endpoints
    YANDEX_SEARCH_API_URL: str = "https://searchapi.api.cloud.yandex.net/v2/web/searchAsync"
    OPERATIONS_API_URL: str = "https://operation.api.cloud.yandex.net/operations"
    SPARK_API_BASE_URL: str = "https://spark-api.ru/api/v1"
    
    # Application Settings
    FLASK_HOST: str = "0.0.0.0"
    FLASK_PORT: int = 5000
    FASTAPI_HOST: str = "0.0.0.0"
    FASTAPI_PORT: int = 8000
    
    # Validation Criteria
    COMPANY_STATUS: str = "Действующее · ЕГРЮЛ"
    COMPANY_SIZE: str = "Средние"
    RISK_LEVEL: str = "Низкий"
    IFR_RANGE: tuple = (0, 30)
    IDO_RANGE: tuple = (0, 40)
    IPD_RANGE: tuple = (79, 100)
    MIN_REVENUE: float = 50_000_000  # 50 млн
    
    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings() 