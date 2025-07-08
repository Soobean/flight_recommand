import asyncio
import calendar
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from amadeus import Client

from app.config.settings import settings

logger = logging.getLogger(__name__)


class MonthlyPriceAnalyzer:
    """월별 가격 분석기"""

    def __init__(self):
        """초기화"""
        if settings.AMADEUS_CLIENT_ID and settings.AMADEUS_CLIENT_SECRET:
            self.client = Client(
                client_id=settings.AMADEUS_CLIENT_ID,
                client_secret=settings.AMADEUS_CLIENT_SECRET,
                hostname=settings.AMADEUS_HOSTNAME,
                log_level="debug",
            )
            self.is_active = True
        else:
            self.client = None
            self.is_active = False

        self.executor = ThreadPoolExecutor(max_workers=5)

        # 일본 지역별 공항 정보
        self.japan_regions = {
            "hokkaido": {
                "name": "홋카이도",
                "airports": ["CTS"],
                "main_airport": "CTS",
            },
            "kanto": {
                "name": "간토 (도쿄)",
                "airports": ["NRT", "HND"],
                "main_airport": "NRT",
            },
            "kansai": {
                "name": "간사이 (오사카)",
                "airports": ["KIX"],
                "main_airport": "KIX",
            },
            "chubu": {
                "name": "중부 (나고야)",
                "airports": ["NGO"],
                "main_airport": "NGO",
            },
            "kyushu": {
                "name": "규슈 (후쿠오카)",
                "airports": ["FUK"],
                "main_airport": "FUK",
            },
            "okinawa": {"name": "오키나와", "airports": ["OKA"], "main_airport": "OKA"},
        }

    async def get_monthly_cheapest_dates(
        self,
        target_year: int,
        target_month: int,
        origin: str = "ICN",
        trip_duration: int = 4,
        adults: int = 1,
    ) -> Dict[str, Any]:
        """
        특정 월의 지역별 최저가 일자 검색

        Args:
            target_year: 대상 연도
            target_month: 대상 월 (1-12)
            origin: 출발지 (기본값: ICN)
            trip_duration: 여행 기간 (기본값: 4일)
            adults: 성인 승객 수 (기본값: 1명)

        Returns:
            지역별 최저가 일자 정보
        """
        logger.info(f"월별 최저가 검색 시작: {target_year}년 {target_month}월")

        # 해당 월의 검색 가능한 날짜 범위 계산
        search_dates = self._get_search_dates(target_year, target_month)

        if not search_dates:
            return {
                "success": False,
                "message": "검색 가능한 날짜가 없습니다",
                "data": {},
            }

        # 각 지역별로 최저가 검색
        regional_results = {}

        for region_id, region_info in self.japan_regions.items():
            logger.info(f"지역 검색 시작: {region_info['name']}")

            region_result = await self._find_cheapest_dates_for_region(
                origin=origin,
                region_id=region_id,
                region_info=region_info,
                search_dates=search_dates,
                trip_duration=trip_duration,
            )

            if region_result:
                regional_results[region_id] = region_result

        return {
            "success": True,
            "message": f"{target_year}년 {target_month}월 지역별 최저가 검색 완료",
            "data": {
                "year": target_year,
                "month": target_month,
                "origin": origin,
                "trip_duration": trip_duration,
                "regions": regional_results,
                "total_regions": len(regional_results),
                "search_date_range": {
                    "start": search_dates[0].strftime("%Y-%m-%d"),
                    "end": search_dates[-1].strftime("%Y-%m-%d"),
                    "total_dates": len(search_dates),
                },
            },
        }

    def _get_search_dates(self, target_year: int, target_month: int) -> List[date]:
        """
        검색 가능한 날짜 목록 생성
        현재 날짜 이후의 날짜만 검색 대상으로 함
        """
        today = date.today()

        # 해당 월의 첫날과 마지막날
        first_day = date(target_year, target_month, 1)
        last_day = date(
            target_year, target_month, calendar.monthrange(target_year, target_month)[1]
        )

        # 현재 날짜 이후의 날짜만 선택
        search_dates = []
        current_date = max(first_day, today + timedelta(days=7))  # 최소 7일 후부터

        while current_date <= last_day:
            search_dates.append(current_date)
            current_date += timedelta(days=1)

        # 주 단위로 샘플링 (API 호출량 최적화)
        if len(search_dates) > 8:
            # 일주일에 2번씩 샘플링
            sampled_dates = []
            for i in range(0, len(search_dates), 3):  # 3일마다
                if i < len(search_dates):
                    sampled_dates.append(search_dates[i])
            search_dates = sampled_dates

        logger.info(
            f"검색 대상 날짜: {len(search_dates)}개 - {search_dates[0]} ~ {search_dates[-1]}"
        )
        return search_dates

    async def _find_cheapest_dates_for_region(
        self,
        origin: str,
        region_id: str,
        region_info: Dict,
        search_dates: List[date],
        trip_duration: int,
        adults: int = 1,
    ) -> Optional[Dict[str, Any]]:
        """
        특정 지역의 최저가 일자 검색
        """
        destination = region_info["main_airport"]
        cheapest_price = float("inf")
        best_dates = None
        all_results = []

        # 각 날짜별로 가격 검색
        for departure_date in search_dates:
            return_date = departure_date + timedelta(days=trip_duration)

            # 해당 월을 벗어나지 않는지 확인
            if return_date.month != departure_date.month and departure_date.day > 25:
                continue

            try:
                result = await self._search_flight_price(
                    origin=origin,
                    destination=destination,
                    departure_date=departure_date.strftime("%Y-%m-%d"),
                    return_date=return_date.strftime("%Y-%m-%d"),
                    adults=adults,
                )

                if result and result.get("success") and result.get("data"):
                    flight_offer = result["data"][0]
                    price_str = flight_offer.get("price", {}).get("total", "999999")

                    try:
                        price = float(price_str)

                        # 결과 저장
                        flight_result = {
                            "departure_date": departure_date.strftime("%Y-%m-%d"),
                            "return_date": return_date.strftime("%Y-%m-%d"),
                            "price": price,
                            "currency": flight_offer.get("price", {}).get(
                                "currency", "EUR"
                            ),
                            "duration_days": trip_duration,
                        }
                        all_results.append(flight_result)

                        # 최저가 업데이트
                        if price < cheapest_price:
                            cheapest_price = price
                            best_dates = flight_result

                    except (ValueError, TypeError):
                        continue

            except Exception as e:
                logger.warning(f"날짜 {departure_date} 검색 실패: {str(e)}")
                continue

        if best_dates:
            # 평균 가격 계산
            prices = [
                r["price"] for r in all_results if isinstance(r["price"], (int, float))
            ]
            avg_price = sum(prices) / len(prices) if prices else 0

            return {
                "region_name": region_info["name"],
                "airport": destination,
                "cheapest_option": best_dates,
                "price_statistics": {
                    "min_price": min(prices) if prices else 0,
                    "max_price": max(prices) if prices else 0,
                    "avg_price": round(avg_price, 2),
                    "price_samples": len(prices),
                },
                "all_options": sorted(all_results, key=lambda x: x["price"])[
                    :5
                ],  # 상위 5개만
            }

        return None

    async def _search_flight_price(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: str,
        adults: int = 1,
    ) -> Optional[Dict[str, Any]]:
        """
        특정 날짜의 항공편 가격 검색
        """
        if not self.is_active:
            return await self._get_dummy_flight_price(
                origin, destination, departure_date, return_date, adults
            )

        def _search():
            params = {
                "originLocationCode": origin,
                "destinationLocationCode": destination,
                "departureDate": departure_date,
                "returnDate": return_date,
                "adults": adults,
                "currencyCode": "EUR",
                "max": 1,  # 최저가 1개만
            }

            logger.debug(f"항공편 가격 검색: {params}")
            return self.client.shopping.flight_offers_search.get(**params)

        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(self.executor, _search)

            return {
                "success": True,
                "data": response.data if hasattr(response, "data") else [],
            }

        except Exception as error:
            logger.warning(
                f"API 호출 실패 ({origin}->{destination}, {departure_date}): {str(error)}"
            )
            return None

    async def _get_dummy_flight_price(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: str,
        adults: int = 1,
    ) -> Dict[str, Any]:
        """더미 항공편 가격 데이터"""
        # 목적지별 기본 가격 (시뮬레이션)
        base_prices = {
            "NRT": 280000,
            "HND": 290000,
            "KIX": 250000,
            "CTS": 320000,
            "NGO": 270000,
            "FUK": 230000,
            "OKA": 350000,
        }

        # 날짜별 가격 변동 시뮬레이션
        base_price = base_prices.get(destination, 280000)

        # 요일별 가격 변동 (금토일 비쌈)
        dept_date = datetime.strptime(departure_date, "%Y-%m-%d")
        weekday_multiplier = 1.2 if dept_date.weekday() in [4, 5, 6] else 1.0

        # 월별 시즌 변동
        month_multipliers = {
            3: 1.4,
            4: 1.5,
            5: 1.3,  # 봄 (벚꽃)
            7: 1.2,
            8: 1.3,  # 여름
            10: 1.3,
            11: 1.4,  # 가을 (단풍)
            12: 1.1,
            1: 1.2,  # 겨울
        }
        season_multiplier = month_multipliers.get(dept_date.month, 1.0)

        final_price = int(base_price * weekday_multiplier * season_multiplier * adults)

        return {
            "success": True,
            "data": [
                {
                    "type": "flight-offer",
                    "price": {"currency": "KRW", "total": str(final_price)},
                }
            ],
        }

    async def get_current_month_cheapest(
        self, origin: str = "ICN", adults: int = 1
    ) -> Dict[str, Any]:
        """
        이번 달 지역별 최저가 검색 (기본 기능)
        """
        today = date.today()
        return await self.get_monthly_cheapest_dates(
            target_year=today.year,
            target_month=today.month,
            origin=origin,
            adults=adults,
        )

    async def get_next_month_cheapest(
        self, origin: str = "ICN", adults: int = 1
    ) -> Dict[str, Any]:
        """
        다음 달 지역별 최저가 검색
        """
        today = date.today()
        next_month = today.month + 1 if today.month < 12 else 1
        next_year = today.year if today.month < 12 else today.year + 1

        return await self.get_monthly_cheapest_dates(
            target_year=next_year, target_month=next_month, origin=origin, adults=adults
        )

    def __del__(self):
        """리소스 정리"""
        if hasattr(self, "executor"):
            self.executor.shutdown(wait=False)


# 편의 함수들


async def search_monthly_cheapest_dates(
    year: int, month: int, origin: str = "ICN", duration: int = 4
) -> Dict[str, Any]:
    """
    월별 최저가 검색 편의 함수
    """
    analyzer = MonthlyPriceAnalyzer()
    return await analyzer.get_monthly_cheapest_dates(year, month, origin, duration)


async def get_this_month_cheapest(origin: str = "ICN") -> Dict[str, Any]:
    """
    이번 달 최저가 검색 편의 함수
    """
    analyzer = MonthlyPriceAnalyzer()
    return await analyzer.get_current_month_cheapest(origin)
