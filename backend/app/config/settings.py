from pathlib import Path
from typing import List, Optional
import secrets

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 기본 설정
    APP_NAME: str = Field(default="지능형 일본 항공권 분석기")
    VERSION: str = Field(default="0.2.0")
    DEBUG: bool = Field(default=False)
    ENVIRONMENT: str = Field(default="development")

    # Amadeus API 설정
    AMADEUS_CLIENT_ID: str = Field(description="Amadeus 클라이언트 ID")
    AMADEUS_CLIENT_SECRET: str = Field(description="Amadeus 클라이언트 시크릿")
    AMADEUS_BASE_URL: str = Field(default="https://test.api.amadeus.com")
    AMADEUS_HOSTNAME: str = Field(default="test")

    # Azure OpenAI 설정
    AZURE_OPENAI_API_KEY: Optional[str] = Field(default=None)
    AZURE_OPENAI_ENDPOINT: Optional[str] = Field(default=None)
    AZURE_OPENAI_API_VERSION: str = Field(default="2025-04-01-preview")
    AZURE_OPENAI_DEPLOYMENT_NAME: str = Field(default="gpt-4.1")
    AZURE_OPENAI_MODEL: str = Field(default="gpt-4.1")
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

    REDIS_HOST: Optional[str] = Field(default=None, description="Redis 호스트 ")
    REDIS_PORT: Optional[str] = Field(default=None, description="Redis 포트")
    REDIS_USERNAME: Optional[str] = Field(default=None, description="Redis 사용자명")
    REDIS_PASSWORD: Optional[str] = Field(default=None, description="Redis 비밀번호")

    # Celery 설정
    CELERY_BROKER_URL: Optional[str] = Field(default=None, description="Celery 브로커 URL")
    CELERY_RESULT_BACKEND: Optional[str] = Field(default=None, description="Celery 결과 백엔드")

    SECRET_KEY: str = Field(
        default='@VQC2PP$^#Ozbu6suJLoLq03ay1CVyMi$%XRdO9QH7qgEc!C$M14owWA3z!uS1NJ',
        min_length=32,
        description="보안 키 (환경변수 필수 - 프로덕션 환경에서는 반드시 설정)",
    )
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)

    # CORS 설정
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"]
    )

    # 로깅 설정
    LOG_LEVEL: str = Field(default="INFO")

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError("보안 키는 최소 32자 이상이어야 합니다.")
        return v

    @field_validator("AMADEUS_CLIENT_ID")
    @classmethod
    def validate_amadeus_credentials(cls, v, info):
        if info.data.get("USE_REAL_AMADEUS", False) and not v:
            raise ValueError("실제 Amadeus 사용시 클라이언트 ID가 필요합니다.")
        return v

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",
    }


settings = Settings()

log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)