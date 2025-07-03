from datetime import date, datetime
from typing import Any, Dict, Optional

from app.config.settings import settings
from app.services.amadeus_service import AmadeusService
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/flights", tags=["flights"])


class FlightSearchRequest(BaseModel):
    """항공편 검색 요청 모델"""

    origin: str = Field(..., description="출발지 IATA 코드", example="ICN")
    destination: str = Field(..., description="도착지 IATA 코드", example="NRT")
    departure_date: str = Field(
        ..., description="출발 날짜 (YYYY-MM-DD)", example="2025-08-15"
    )
    return_date: Optional[str] = Field(
        None, description="귀국 날짜 (YYYY-MM-DD)", example="2025-08-18"
    )
    adults: int = Field(1, description="성인 승객 수", example=1)
    currency: str = Field("KRW", description="통화 코드", example="KRW")


class CheapestDateRequest(BaseModel):
    """최저가 날짜 검색 요청 모델"""

    origin: str = Field(..., description="출발지 IATA 코드", example="ICN")
    destination: str = Field(..., description="도착지 IATA 코드", example="NRT")
    departure_date: str = Field(
        ..., description="출발 날짜 (YYYY-MM-DD)", example="2025-08-15"
    )
    duration: Optional[int] = Field(None, description="여행 기간 (일수)", example=4)


# 의존성 주입
def get_amadeus_service() -> AmadeusService:
    """Amadeus 서비스 인스턴스 반환"""
    return AmadeusService()


@router.post("/search")
async def search_flights(
    request: FlightSearchRequest,
    amadeus_service: AmadeusService = Depends(get_amadeus_service),
) -> Dict[str, Any]:
    """
    실시간 항공편 검색

    일본 여행 항공편을 실시간으로 검색합니다.
    """
    try:
        result = await amadeus_service.search_flight_offers(
            origin=request.origin,
            destination=request.destination,
            departure_date=request.departure_date,
            return_date=request.return_date,
            adults=request.adults,
            currency=request.currency,
        )

        if result["success"]:
            return {
                "success": True,
                "message": "항공편 검색 완료",
                "data": result["data"],
                "meta": result.get("meta", {}),
                "dictionaries": result.get("dictionaries", {}),
            }
        else:
            raise HTTPException(status_code=404, detail=result["message"])

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"항공편 검색 중 오류가 발생했습니다: {str(e)}")


@router.post("/cheapest-dates")
async def search_cheapest_dates(
    request: CheapestDateRequest,
    amadeus_service: AmadeusService = Depends(get_amadeus_service),
) -> Dict[str, Any]:
    """
    최저가 날짜 검색

    특정 구간의 최저가 항공편 날짜를 검색합니다.
    """
    try:
        result = await amadeus_service.search_cheapest_dates(
            origin=request.origin,
            destination=request.destination,
            departure_date=request.departure_date,
            duration=request.duration,
        )

        if result["success"]:
            return {
                "success": True,
                "message": "최저가 날짜 검색 완료",
                "data": result["data"],
                "meta": result.get("meta", {}),
            }
        else:
            raise HTTPException(status_code=404, detail=result["message"])

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"최저가 날짜 검색 중 오류가 발생했습니다: {str(e)}")


@router.get("/airport/{iata_code}")
async def get_airport_info(
    iata_code: str, amadeus_service: AmadeusService = Depends(get_amadeus_service)
) -> Dict[str, Any]:
    """
    공항 정보 조회

    IATA 코드로 공항 정보를 조회합니다.
    """
    try:
        result = await amadeus_service.get_airport_info(iata_code.upper())

        if result["success"]:
            return {"success": True, "message": "공항 정보 조회 완료", "data": result["data"]}
        else:
            raise HTTPException(status_code=404, detail=result["message"])

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"공항 정보 조회 중 오류가 발생했습니다: {str(e)}")
