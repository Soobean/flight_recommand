"""FastAPI 메인 애플리케이션"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="지능형 일본 항공권 분석기 API",
    description="일본 여행 항공권의 가격과 가치를 분석하는 지능형 API",
    version="0.1.0",
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발 환경, 운영시 수정 필요
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """API 상태 확인"""
    return {"message": "지능형 일본 항공권 분석기 API", "version": "0.1.0"}

@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "healthy"}
