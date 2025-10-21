"""애플리케이션 설정 관리"""
from typing import List, Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """애플리케이션 설정 클래스"""

    # 보안 설정
    SECRET_KEY: str = Field(..., min_length=32, description="JWT 서명용 비밀키")
    ALGORITHM: str = Field(default="HS256", description="JWT 알고리즘")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="액세스 토큰 만료 시간")

    # 애플리케이션 설정
    APP_NAME: str = Field(default="지능형 일본 항공권 분석기")
    VERSION: str = Field(default="0.2.0")
    DEBUG: bool = Field(default=False)
    ENVIRONMENT: str = Field(default="development")

    # CORS 설정
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="허용할 CORS Origins",
    )

    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        """CORS origins를 파싱 (문자열 또는 리스트 지원)"""
        if isinstance(v, str):
            # JSON 배열 문자열인 경우
            import json

            try:
                return json.loads(v)
            except json.JSONDecodeError:
                # 쉼표로 구분된 문자열인 경우
                return [origin.strip() for origin in v.split(",")]
        return v

    # 데이터베이스 설정
    DATABASE_URL: str = Field(
        ..., description="데이터베이스 연결 URL (SQLAlchemy 형식)"
    )
    DATABASE_ECHO: bool = Field(
        default=False, description="SQL 쿼리 로깅 여부 (개발용)"
    )

    # Azure Database 설정 (선택적, DATABASE_URL 사용 권장)
    AZURE_DB_HOST: Optional[str] = None
    AZURE_DB_NAME: Optional[str] = None
    AZURE_DB_USER: Optional[str] = None
    AZURE_DB_PASSWORD: Optional[str] = None
    AZURE_DB_PORT: int = Field(default=5432)
    AZURE_DB_SSLMODE: str = Field(default="require")

    # Redis 설정
    REDIS_URL: str = Field(..., description="Redis 연결 URL")
    REDIS_HOST: Optional[str] = None
    REDIS_PORT: Optional[int] = None
    REDIS_USERNAME: Optional[str] = None
    REDIS_PASSWORD: Optional[str] = None

    # Celery 설정
    CELERY_BROKER_URL: str = Field(..., description="Celery 브로커 URL")
    CELERY_RESULT_BACKEND: str = Field(..., description="Celery 결과 백엔드 URL")

    # Amadeus API 설정
    AMADEUS_CLIENT_ID: str = Field(..., description="Amadeus API 클라이언트 ID")
    AMADEUS_CLIENT_SECRET: str = Field(..., description="Amadeus API 시크릿")
    AMADEUS_BASE_URL: str = Field(
        default="https://test.api.amadeus.com", description="Amadeus API 베이스 URL"
    )
    AMADEUS_HOSTNAME: str = Field(default="test", description="Amadeus 호스트명")
    USE_REAL_AMADEUS: bool = Field(
        default=True, description="실제 Amadeus API 사용 여부"
    )
    ENABLE_DUMMY_FALLBACK: bool = Field(
        default=True, description="더미 데이터 폴백 활성화"
    )

    # 환율 API 설정
    KOREAEXIM_API_KEY: str = Field(..., description="한국수출입은행 환율 API 키")

    # Azure OpenAI 설정
    AZURE_OPENAI_API_KEY: str = Field(..., description="Azure OpenAI API 키")
    AZURE_OPENAI_ENDPOINT: str = Field(..., description="Azure OpenAI 엔드포인트")
    AZURE_OPENAI_API_VERSION: str = Field(
        default="2025-04-01-preview", description="Azure OpenAI API 버전"
    )
    AZURE_OPENAI_DEPLOYMENT_NAME: str = Field(
        default="gpt-4.1", description="Azure OpenAI 배포 이름"
    )
    AZURE_OPENAI_MODEL: str = Field(default="gpt-4.1", description="OpenAI 모델명")
    AZURE_OPENAI_MAX_TOKENS: int = Field(
        default=4000, description="최대 토큰 수"
    )

    # Anthropic 설정
    ANTHROPIC_API_KEY: str = Field(..., description="Anthropic API 키")

    # 로깅 설정
    LOG_LEVEL: str = Field(default="INFO", description="로그 레벨")

    # 테스트 설정 (선택적)
    TEST_REDIS_URL: Optional[str] = None
    TEST_DATABASE_URL: Optional[str] = None

    class Config:
        """Pydantic 설정"""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "allow"  # 추가 환경변수 허용

    @property
    def is_development(self) -> bool:
        """개발 환경 여부"""
        return self.ENVIRONMENT == "development"

    @property
    def is_production(self) -> bool:
        """운영 환경 여부"""
        return self.ENVIRONMENT == "production"

    @property
    def is_testing(self) -> bool:
        """테스트 환경 여부"""
        return self.ENVIRONMENT == "testing"


# 전역 설정 인스턴스
settings = Settings()
