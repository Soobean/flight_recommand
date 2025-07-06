from datetime import datetime, timedelta
from typing import Any, Dict


def enhance_flight_search_response(
    result: Dict[str, Any], request, *args, **kwargs
) -> Dict[str, Any]:
    flights = result.get("data", [])

    return {
        "flights": flights,
        "search_params": {
            "origin": request.origin,
            "destination": request.destination,
            "departure_date": request.departure_date,
            "return_date": request.return_date,
            "adults": request.adults,
            "currency": request.currency,
        },
        "search_timestamp": datetime.now().isoformat(),
        "from_cache": False,
        "result_count": len(flights) if flights else 0,
    }


def enhance_duration_search_response(
    result: Dict[str, Any], request, *args, **kwargs
) -> Dict[str, Any]:
    """기간별 검색 응답 보강"""
    flights = result.get("data", [])

    # 귀국 날짜 계산
    departure = datetime.strptime(request.departure_date, "%Y-%m-%d").date()
    return_date = departure + timedelta(days=request.duration_days - 1)

    return {
        "flights": flights,
        "trip_details": {
            "departure_date": request.departure_date,
            "return_date": return_date.strftime("%Y-%m-%d"),
            "duration_days": request.duration_days,
            "nights": request.duration_days - 1,
            "destination": request.destination,
            "description": f"{request.duration_days - 1}박 {request.duration_days}일",
        },
        "search_params": {
            "origin": request.origin,
            "destination": request.destination,
            "duration_days": request.duration_days,
            "adults": request.adults,
            "currency": request.currency,
        },
        "search_timestamp": datetime.now().isoformat(),
        "from_cache": False,
        "result_count": len(flights) if flights else 0,
    }


def enhance_cheapest_dates_response(
    result: Dict[str, Any], request, *args, **kwargs
) -> Dict[str, Any]:
    """최저가 날짜 응답 보강"""
    search_result = result.get("data", [])

    # 가격 분석
    price_analysis = {}
    if search_result:
        prices = []
        for item in search_result:
            try:
                price = float(item.get("price", {}).get("total", 0))
                prices.append(price)
            except (ValueError, TypeError):
                continue

        if prices:
            price_analysis = {
                "min_price": min(prices),
                "max_price": max(prices),
                "avg_price": sum(prices) / len(prices),
                "price_range": max(prices) - min(prices),
                "savings_potential": (
                    f"최대 {max(prices) - min(prices):,.0f}원 절약 가능"
                    if len(prices) > 1
                    else "N/A"
                ),
            }

    return {
        "cheapest_options": search_result,
        "search_params": {
            "origin": request.origin,
            "destination": request.destination,
            "base_departure_date": request.departure_date,
            "duration": request.duration,
            "flexibility_days": request.flexibility_days,
        },
        "price_analysis": price_analysis,
        "search_timestamp": datetime.now().isoformat(),
        "result_count": len(search_result) if search_result else 0,
        "recommendations": {
            "best_value": search_result[0] if search_result else None,
            "booking_advice": "가격은 실시간으로 변동될 수 있으니 빠른 예약을 권장합니다.",
        },
    }


def enhance_airport_info_response(
    result: Dict[str, Any], iata_code: str, *args, **kwargs
) -> Dict[str, Any]:
    """공항 정보 응답 보강"""
    airport_data = result.get("data", {})

    return {
        **airport_data,
        "queried_iata": iata_code.upper(),
        "last_updated": datetime.now().isoformat(),
    }


def get_popular_routes_data(origin: str = "ICN", limit: int = 10) -> Dict[str, Any]:
    """인기 노선 더미 데이터 생성"""
    # 실제로는 DB에서 집계된 데이터를 가져와야 함
    popular_routes = [
        {
            "destination": "NRT",
            "city": "도쿄",
            "avg_price": 280000,
            "search_count": 1250,
        },
        {
            "destination": "KIX",
            "city": "오사카",
            "avg_price": 250000,
            "search_count": 890,
        },
        {
            "destination": "CTS",
            "city": "삿포로",
            "avg_price": 320000,
            "search_count": 650,
        },
        {
            "destination": "FUK",
            "city": "후쿠오카",
            "avg_price": 230000,
            "search_count": 580,
        },
        {
            "destination": "NGO",
            "city": "나고야",
            "avg_price": 270000,
            "search_count": 420,
        },
        {
            "destination": "OKA",
            "city": "나하",
            "avg_price": 350000,
            "search_count": 380,
        },
    ]

    return {
        "origin": origin,
        "popular_routes": popular_routes[:limit],
        "total_routes": min(len(popular_routes), limit),
        "data_source": "aggregated_search_statistics",
        "last_updated": datetime.now().isoformat(),
        "note": "실제 운영시에는 사용자 검색 데이터 기반으로 분석",
    }
