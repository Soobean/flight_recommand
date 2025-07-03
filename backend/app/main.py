import sys
from typing import Any, Dict

from app.api.v1.flights import router as flights_router
from app.config.settings import settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title=settings.APP_NAME,
    description="일본 여행 항공권의 가격과 가치를 분석하는 지능형 API",
    version=settings.VERSION,
    debug=settings.DEBUG,
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발 환경, 운영시 수정 필요
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(flights_router, prefix="/api/v1")


@app.get("/")
async def root() -> Dict[str, Any]:
    """API 상태 확인"""
    return {
        "message": settings.APP_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    }


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """헬스 체크"""
    return {
        "status": "healthy",
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
        "environment": settings.ENVIRONMENT,
    }
