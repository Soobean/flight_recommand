from datetime import date, datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, validator

from app.services.monthly_price_analyzer import MonthlyPriceAnalyzer

router = APIRouter(prefix="/flights", tags=["monthly-analysis"])


# Request/Response 모델


class MonthlySearchRequest(BaseModel):
    """월별 검색 요청 모델"""

    year: Optional[int] = Field(None, description="대상 연도 (미지정시 현재 연도)", example=2025)
    month: Optional[int] = Field(
        None, description="대상 월 (1-12, 미지정시 현재 월)", ge=1, le=12, example=8
    )
    origin: str = Field("ICN", description="출발지 IATA 코드", example="ICN")
    duration: int = Field(4, description="여행 기간 (일수)", ge=2, le=14, example=4)

    @validator("year")
    def validate_year(cls, v):
        if v is not None:
            current_year = datetime.now().year
            if v < current_year or v > current_year + 2:
                raise ValueError(f"연도는 {current_year}년부터 {current_year + 2}년까지 가능합니다")
        return v

    @validator("month")
    def validate_month(cls, v):
        if v is not None and (v < 1 or v > 12):
            raise ValueError("월은 1부터 12까지 가능합니다")
        return v


class RegionCheapestInfo(BaseModel):
    """지역별 최저가 정보"""

    region_name: str = Field(..., description="지역 이름")
    airport: str = Field(..., description="공항 코드")
    cheapest_option: Dict = Field(..., description="최저가 옵션")
    price_statistics: Dict = Field(..., description="가격 통계")


class MonthlyAnalysisResponse(BaseModel):
    """월별 분석 응답 모델"""

    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="응답 메시지")
    data: Dict[str, Any] = Field(..., description="분석 결과")


def get_monthly_analyzer() -> MonthlyPriceAnalyzer:
    """월별 가격 분석기 인스턴스 반환"""
    return MonthlyPriceAnalyzer()


# API 엔드포인트


@router.get("/monthly-cheapest", response_model=MonthlyAnalysisResponse)
async def get_monthly_cheapest_dates(
    year: Optional[int] = Query(None, description="대상 연도 (기본값: 현재 연도)"),
    month: Optional[int] = Query(None, description="대상 월 (기본값: 현재 월)", ge=1, le=12),
    origin: str = Query("ICN", description="출발지 IATA 코드"),
    adults: int = Query(1, description="성인 승객 수", ge=1, le=9),
    duration: int = Query(4, description="여행 기간 (일수)", ge=2, le=14),
    analyzer: MonthlyPriceAnalyzer = Depends(get_monthly_analyzer),
) -> Dict[str, Any]:
    """
    월별 지역별 최저가 일자 검색

    **기본 동작**: 이번 달 기준으로 각 일본 지역의 최저가 왕복 항공편 일자를 검색합니다.

    **사용 예시**:
    - `GET /monthly-cheapest` → 이번 달 최저가 (성인 1명)
    - `GET /monthly-cheapest?adults=2&month=8` → 8월 최저가 (성인 2명)
    - `GET /monthly-cheapest?year=2025&month=12&adults=4` → 2025년 12월 최저가 (성인 4명)
    """
    try:
        # 기본값 설정
        today = date.today()
        target_year = year if year is not None else today.year
        target_month = month if month is not None else today.month

        # 과거 날짜 검증
        if target_year == today.year and target_month < today.month:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"과거 월({target_month}월)은 검색할 수 없습니다. "
                    f"현재 월({today.month}월) 이후를 선택해주세요."
                ),
            )

        # 월별 최저가 검색 실행
        result = await analyzer.get_monthly_cheapest_dates(
            target_year=target_year,
            target_month=target_month,
            origin=origin,
            trip_duration=duration,
            adults=adults,
        )

        if result["success"]:
            # 프론트엔드용 데이터 구조로 변환
            frontend_data = _format_for_frontend(result["data"])

            return {
                "success": True,
                "message": f"{target_year}년 {target_month}월 지역별 최저가 검색 완료",
                "data": frontend_data,
            }
        else:
            raise HTTPException(status_code=500, detail=result["message"])

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"월별 최저가 검색 중 오류가 발생했습니다: {str(e)}")


@router.get("/this-month-cheapest", response_model=MonthlyAnalysisResponse)
async def get_this_month_cheapest(
    origin: str = Query("ICN", description="출발지 IATA 코드"),
    adults: int = Query(1, description="성인 승객 수", ge=1, le=9),
    duration: int = Query(4, description="여행 기간 (일수)", ge=2, le=14),
    analyzer: MonthlyPriceAnalyzer = Depends(get_monthly_analyzer),
) -> Dict[str, Any]:
    """
    이번 달 지역별 최저가 검색 (단축 엔드포인트)

    앱의 기본 화면에서 사용하는 핵심 API입니다.
    """
    try:
        result = await analyzer.get_current_month_cheapest(origin=origin, adults=adults)

        if result["success"]:
            frontend_data = _format_for_frontend(result["data"])

            return {
                "success": True,
                "message": "이번 달 지역별 최저가 검색 완료",
                "data": frontend_data,
            }
        else:
            raise HTTPException(status_code=500, detail=result["message"])

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"이번 달 최저가 검색 중 오류가 발생했습니다: {str(e)}",
        )


@router.get("/next-month-cheapest", response_model=MonthlyAnalysisResponse)
async def get_next_month_cheapest(
    origin: str = Query("ICN", description="출발지 IATA 코드"),
    adults: int = Query(1, description="성인 승객 수", ge=1, le=9),
    duration: int = Query(4, description="여행 기간 (일수)", ge=2, le=14),
    analyzer: MonthlyPriceAnalyzer = Depends(get_monthly_analyzer),
) -> Dict[str, Any]:
    """
    다음 달 지역별 최저가 검색

    사용자가 미리 다음 달 여행을 계획할 때 사용합니다.
    """
    try:
        result = await analyzer.get_next_month_cheapest(origin=origin, adults=adults)

        if result["success"]:
            frontend_data = _format_for_frontend(result["data"])

            return {
                "success": True,
                "message": "다음 달 지역별 최저가 검색 완료",
                "data": frontend_data,
            }
        else:
            raise HTTPException(status_code=500, detail=result["message"])

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"다음 달 최저가 검색 중 오류가 발생했습니다: {str(e)}",
        )


@router.get("/monthly-analysis/{year}/{month}", response_model=MonthlyAnalysisResponse)
async def get_specific_month_analysis(
    year: int,
    month: int,
    origin: str = Query("ICN", description="출발지 IATA 코드"),
    adults: int = Query(1, description="성인 승객 수", ge=1, le=9),
    duration: int = Query(4, description="여행 기간 (일수)", ge=2, le=14),
    analyzer: MonthlyPriceAnalyzer = Depends(get_monthly_analyzer),
) -> Dict[str, Any]:
    """
    특정 월 지역별 최저가 검색 (RESTful 방식)

    **사용 예시**:
    - `GET /monthly-analysis/2025/8` → 2025년 8월
    - `GET /monthly-analysis/2026/12` → 2026년 12월
    """
    # 날짜 유효성 검증
    current_year = datetime.now().year
    if year < current_year or year > current_year + 2:
        raise HTTPException(
            status_code=400,
            detail=f"연도는 {current_year}년부터 {current_year + 2}년까지 가능합니다",
        )

    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="월은 1부터 12까지 가능합니다")

    # 과거 날짜 검증
    today = date.today()
    if year == today.year and month < today.month:
        raise HTTPException(
            status_code=400,
            detail=f"과거 월은 검색할 수 없습니다. 현재 월({today.month}월) 이후를 선택해주세요.",
        )

    try:
        result = await analyzer.get_monthly_cheapest_dates(
            target_year=year,
            target_month=month,
            origin=origin,
            trip_duration=duration,
            adults=adults,
        )

        if result["success"]:
            frontend_data = _format_for_frontend(result["data"])

            return {
                "success": True,
                "message": f"{year}년 {month}월 지역별 최저가 검색 완료",
                "data": frontend_data,
            }
        else:
            raise HTTPException(status_code=500, detail=result["message"])

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"{year}년 {month}월 최저가 검색 중 오류가 발생했습니다: {str(e)}",
        )


# 유틸리티 함수


def _format_for_frontend(analysis_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    프론트엔드에서 사용하기 쉬운 형태로 데이터 변환
    """
    if not analysis_data or "regions" not in analysis_data:
        return analysis_data

    # 지역별 데이터를 프론트엔드 친화적으로 변환
    formatted_regions = {}

    for region_id, region_data in analysis_data["regions"].items():
        if region_data and "cheapest_option" in region_data:
            cheapest = region_data["cheapest_option"]
            stats = region_data.get("price_statistics", {})

            formatted_regions[region_id] = {
                "region_name": region_data["region_name"],
                "airport": region_data["airport"],
                "best_dates": {
                    "departure_date": cheapest["departure_date"],
                    "return_date": cheapest["return_date"],
                    "duration_days": cheapest["duration_days"],
                },
                "price_info": {
                    "best_price": cheapest["price"],
                    "currency": cheapest["currency"],
                    "avg_price": stats.get("avg_price", 0),
                    "min_price": stats.get("min_price", 0),
                    "max_price": stats.get("max_price", 0),
                },
                "alternatives": region_data.get("all_options", [])[:3],  # 상위 3개 대안
            }

    # 가격순으로 정렬
    sorted_regions = dict(
        sorted(
            formatted_regions.items(), key=lambda x: x[1]["price_info"]["best_price"]
        )
    )

    return {
        "search_info": {
            "year": analysis_data["year"],
            "month": analysis_data["month"],
            "origin": analysis_data["origin"],
            "trip_duration": analysis_data["trip_duration"],
            "search_date_range": analysis_data["search_date_range"],
        },
        "regions": sorted_regions,
        "summary": {
            "total_regions": len(sorted_regions),
            "cheapest_region": (
                min(
                    sorted_regions.keys(),
                    key=lambda x: sorted_regions[x]["price_info"]["best_price"],
                )
                if sorted_regions
                else None
            ),
            "price_range": {
                "min": (
                    min(
                        [r["price_info"]["best_price"] for r in sorted_regions.values()]
                    )
                    if sorted_regions
                    else 0
                ),
                "max": (
                    max(
                        [r["price_info"]["best_price"] for r in sorted_regions.values()]
                    )
                    if sorted_regions
                    else 0
                ),
            },
        },
    }


# 헬스 체크


@router.get("/monthly-analysis/health")
async def monthly_analysis_health_check(
    analyzer: MonthlyPriceAnalyzer = Depends(get_monthly_analyzer),
) -> Dict[str, Any]:
    """
    월별 분석 서비스 상태 확인
    """
    return {
        "service": "monthly_analysis",
        "status": "healthy",
        "amadeus_active": analyzer.is_active,
        "supported_regions": len(analyzer.japan_regions),
        "regions": list(analyzer.japan_regions.keys()),
        "timestamp": datetime.now().isoformat(),
    }
