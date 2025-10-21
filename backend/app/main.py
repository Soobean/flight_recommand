"""FastAPI 메인 애플리케이션"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
import time

from app.core.config import settings
from app.core.logging import setup_logging, get_logger, log_api_call
from app.core.database import check_db_connection
from app.core.exceptions import (
    AppException,
    app_exception_handler,
    validation_exception_handler,
    http_exception_handler,
    sqlalchemy_exception_handler,
    general_exception_handler,
)

# 로깅 초기화
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    애플리케이션 시작/종료 시 실행되는 이벤트 핸들러

    - 시작: 데이터베이스 연결 확인
    - 종료: 리소스 정리
    """
    # 시작 이벤트
    logger.info(f"🚀 애플리케이션 시작 - {settings.APP_NAME} v{settings.VERSION}")
    logger.info(f"환경: {settings.ENVIRONMENT}")

    # 데이터베이스 연결 확인
    if check_db_connection():
        logger.info("✅ 데이터베이스 연결 성공")
    else:
        logger.error("❌ 데이터베이스 연결 실패")

    yield

    # 종료 이벤트
    logger.info("🛑 애플리케이션 종료")


# FastAPI 애플리케이션 생성
app = FastAPI(
    title=settings.APP_NAME,
    description="일본 여행 항공권의 가격과 가치를 분석하는 지능형 API",
    version=settings.VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 요청/응답 로깅 미들웨어
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    모든 HTTP 요청/응답 로깅

    - 요청 메서드, 경로
    - 응답 상태 코드
    - 처리 시간
    """
    start_time = time.time()

    response = await call_next(request)

    duration = time.time() - start_time
    log_api_call(
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration=duration,
    )

    return response


# 예외 핸들러 등록
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, http_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)


# 루트 엔드포인트
@app.get("/", tags=["Root"])
async def root():
    """API 루트 - 기본 정보 반환"""
    return {
        "message": settings.APP_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    헬스 체크 엔드포인트

    데이터베이스 연결 상태 확인 포함
    """
    db_healthy = check_db_connection()

    return {
        "status": "healthy" if db_healthy else "unhealthy",
        "database": "connected" if db_healthy else "disconnected",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }


# API 라우터 등록 (향후 추가)
# from app.api.v1 import auth, flights, users
# app.include_router(auth.router, prefix="/api/v1/auth", tags=["인증"])
# app.include_router(flights.router, prefix="/api/v1/flights", tags=["항공권"])
# app.include_router(users.router, prefix="/api/v1/users", tags=["사용자"])
