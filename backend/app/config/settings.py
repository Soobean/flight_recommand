import os
from pathlib import Path
from typing import List, Optional

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 기본 설정
    APP_NAME: str = Field(default="지능형 일본 항공권 분석기")
    VERSION: str = Field(default="0.2.0")
    DEBUG: bool = Field(default=False)
    ENVIRONMENT: str = Field(default="development")

    # Amadeus API 설정
    AMADEUS_CLIENT_ID: str = Field(default="")
    AMADEUS_CLIENT_SECRET: str = Field(default="")
    AMADEUS_BASE_URL: str = Field(default="https://test.api.amadeus.com")
    AMADEUS_HOSTNAME: str = Field(default="test")

    # Azure OpenAI 설정
    AZURE_OPENAI_API_KEY: Optional[str] = Field(default=None)
    AZURE_OPENAI_ENDPOINT: Optional[str] = Field(default=None)
    AZURE_OPENAI_API_VERSION: str = Field(default="2024-02-01")
    AZURE_OPENAI_DEPLOYMENT_NAME: str = Field(default="gpt-4o-mini")
    AZURE_OPENAI_MODEL: str = Field(default="gpt-4o-mini")
    AZURE_OPENAI_MAX_TOKENS: int = Field(default=4000)

    # 데이터베이스 설정
    DATABASE_URL: Optional[str] = Field(default=None)
    DATABASE_ECHO: bool = Field(default=False)

    # Azure 데이터베이스 설정
    AZURE_DB_HOST: Optional[str] = Field(default=None)
    AZURE_DB_NAME: Optional[str] = Field(default=None)
    AZURE_DB_USER: Optional[str] = Field(default=None)
    AZURE_DB_PASSWORD: Optional[str] = Field(default=None)
    AZURE_DB_PORT: Optional[str] = Field(default=None)
    AZURE_DB_SSLMODE: Optional[str] = Field(default=None)

    # Amadeus 추가 설정
    USE_REAL_AMADEUS: bool = Field(default=False)
    ENABLE_DUMMY_FALLBACK: bool = Field(default=True)

    # Redis 설정
    REDIS_URL: Optional[str] = Field(default="redis://localhost:6379/0")

    # Celery 설정
    CELERY_BROKER_URL: Optional[str] = Field(default="redis://localhost:6379/1")
    CELERY_RESULT_BACKEND: Optional[str] = Field(default="redis://localhost:6379/2")

    # 보안 설정
    SECRET_KEY: str = Field(default="your-secret-key-here")
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)

    # CORS 설정
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"]
    )

    # 로깅 설정
    LOG_LEVEL: str = Field(default="INFO")

    @validator("ALLOWED_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


settings = Settings()

log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
