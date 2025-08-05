import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from app.services.cache_service import CacheService
from app.services.monthly_price_analyzer import MonthlyPriceAnalyzer

logger = logging.getLogger(__name__)


class MonthlyDataCollectionService:
    """월별 데이터 수집 비즈니스 로직을 담당하는 서비스"""

    def __init__(self, cache_service: CacheService = None):
        """
        서비스 초기화

        Args:
            cache_service: 캐시 서비스 인스턴스
        """
        self.cache_service = cache_service or CacheService()
        self.analyzer = MonthlyPriceAnalyzer()

    async def collect_monthly_data(
        self, year: int, month: int, origin: str = "ICN", trip_duration: int = 4
    ) -> Dict[str, Any]:
        """
        특정 월의 지역별 최저가 데이터 수집

        Args:
            year: 대상 연도
            month: 대상 월
            origin: 출발지 공항 코드
            trip_duration: 여행 기간 (일)

        Returns:
            수집 결과 딕셔너리
        """
        try:
            logger.info(f"월별 데이터 수집 시작: {year}년 {month}월, 출발지: {origin}")

            # 데이터 수집
            result = await self.analyzer.get_monthly_cheapest_dates(
                target_year=year,
                target_month=month,
                origin=origin,
                trip_duration=trip_duration,
            )

            if not result["success"]:
                return {
                    "success": False,
                    "message": f"데이터 수집 실패: {result.get('message', 'Unknown error')}",
                    "year": year,
                    "month": month,
                    "origin": origin,
                }

            # 캐시에 저장
            cache_result = await self._save_to_cache(year, month, origin, result["data"])

            return {
                "success": True,
                "message": f"데이터 수집 완료: {year}년 {month}월",
                "year": year,
                "month": month,
                "origin": origin,
                "regions_collected": len(result["data"].get("regions", {})),
                "cache_saved": cache_result,
                "collected_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"월별 데이터 수집 실패: {str(e)}")
            return {
                "success": False,
                "message": f"수집 중 오류 발생: {str(e)}",
                "year": year,
                "month": month,
                "origin": origin,
                "error": str(e),
            }

    def collect_monthly_data_sync(
        self, year: int, month: int, origin: str = "ICN", trip_duration: int = 4
    ) -> Dict[str, Any]:
        """
        동기 버전의 월별 데이터 수집 (Celery 작업용)

        Args:
            year: 대상 연도
            month: 대상 월
            origin: 출발지 공항 코드
            trip_duration: 여행 기간 (일)

        Returns:
            수집 결과 딕셔너리
        """
        try:
            # 새 이벤트 루프 생성
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                result = loop.run_until_complete(
                    self.collect_monthly_data(year, month, origin, trip_duration)
                )
                return result
            finally:
                loop.close()

        except Exception as e:
            logger.error(f"동기 데이터 수집 실패: {str(e)}")
            return {
                "success": False,
                "message": f"동기 수집 중 오류 발생: {str(e)}",
                "year": year,
                "month": month,
                "origin": origin,
                "error": str(e),
            }

    async def _save_to_cache(
        self, year: int, month: int, origin: str, data: Dict[str, Any]
    ) -> bool:
        """
        수집된 데이터를 캐시에 저장

        Args:
            year: 연도
            month: 월
            origin: 출발지
            data: 저장할 데이터

        Returns:
            저장 성공 여부
        """
        try:
            cache_key = f"monthly_cheapest:{origin}:{year}:{month:02d}"
            cache_data = {
                "data": data,
                "collected_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(hours=12)).isoformat(),
            }

            # 12시간 캐시
            success = self.cache_service.set_cache(cache_key, cache_data, 43200)

            if success:
                logger.info(f"데이터 캐시 저장 성공: {cache_key}")
            else:
                logger.warning(f"데이터 캐시 저장 실패: {cache_key}")

            return success

        except Exception as e:
            logger.error(f"캐시 저장 중 오류: {str(e)}")
            return False

    def get_cached_monthly_data(
        self, year: int, month: int, origin: str = "ICN"
    ) -> Optional[Dict[str, Any]]:
        """
        캐시된 월별 데이터 조회

        Args:
            year: 연도
            month: 월
            origin: 출발지

        Returns:
            캐시된 데이터 또는 None
        """
        try:
            cache_key = f"monthly_cheapest:{origin}:{year}:{month:02d}"
            cached_data = self.cache_service.get_cache(cache_key)

            if cached_data:
                # 만료 시간 확인
                expires_at_str = cached_data.get("expires_at")
                if expires_at_str:
                    expires_at = datetime.fromisoformat(expires_at_str)
                    if datetime.now() > expires_at:
                        logger.info(f"캐시 만료됨: {cache_key}")
                        self.cache_service.delete_cache(cache_key)
                        return None

                logger.info(f"캐시 데이터 반환: {cache_key}")
                return cached_data

        except Exception as e:
            logger.warning(f"캐시 데이터 읽기 실패: {str(e)}")

        return None

    def is_month_data_available(
        self, year: int, month: int, origin: str = "ICN"
    ) -> bool:
        """
        해당 월 데이터가 캐시에 있는지 확인

        Args:
            year: 연도
            month: 월
            origin: 출발지

        Returns:
            데이터 존재 여부
        """
        try:
            cache_key = f"monthly_cheapest:{origin}:{year}:{month:02d}"
            return self.cache_service.is_cache_valid(cache_key)
        except Exception as e:
            logger.warning(f"캐시 존재 확인 실패: {str(e)}")
            return False

    def force_refresh_month_data(
        self, year: int, month: int, origin: str = "ICN"
    ) -> Dict[str, Any]:
        """
        특정 월 데이터 강제 갱신

        Args:
            year: 연도
            month: 월
            origin: 출발지

        Returns:
            갱신 결과
        """
        try:
            # 기존 캐시 삭제
            cache_key = f"monthly_cheapest:{origin}:{year}:{month:02d}"
            deleted = self.cache_service.delete_cache(cache_key)

            logger.info(f"기존 캐시 삭제 {'성공' if deleted else '실패'}: {cache_key}")

            # 새로 수집
            result = self.collect_monthly_data_sync(year, month, origin)

            return {
                "success": result["success"],
                "message": f"강제 갱신 {'완료' if result['success'] else '실패'}",
                "cache_deleted": deleted,
                "collection_result": result,
            }

        except Exception as e:
            logger.error(f"강제 갱신 실패: {str(e)}")
            return {
                "success": False,
                "message": f"강제 갱신 중 오류 발생: {str(e)}",
                "error": str(e),
            }

    def cleanup_expired_cache(self) -> Dict[str, Any]:
        """
        만료된 월별 캐시 데이터 정리

        Returns:
            정리 결과
        """
        try:
            # 월별 캐시 키 패턴으로 정리
            pattern = "monthly_cheapest:*"
            cleaned_count = self.cache_service.clear_cache_pattern(pattern)

            logger.info(f"만료된 월별 캐시 {cleaned_count}개 정리 완료")

            return {
                "success": True,
                "message": f"만료된 캐시 {cleaned_count}개 정리 완료",
                "cleaned_count": cleaned_count,
                "cleaned_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"캐시 정리 실패: {str(e)}")
            return {
                "success": False,
                "message": f"캐시 정리 중 오류 발생: {str(e)}",
                "error": str(e),
                "cleaned_count": 0,
            }

    def get_collection_statistics(self) -> Dict[str, Any]:
        """
        월별 데이터 수집 통계 조회

        Returns:
            통계 정보
        """
        try:
            # 월별 캐시 키들 조회
            pattern = "monthly_cheapest:*"
            cache_keys_result = self.cache_service._get_redis_cache_keys(pattern, 1000)

            if isinstance(cache_keys_result, dict):
                keys = cache_keys_result.get("keys", [])
                total_count = cache_keys_result.get("total", 0)
            else:
                keys = []
                total_count = 0

            # 월별/지역별 분류
            months_by_origin = {}
            for key in keys:
                try:
                    # monthly_cheapest:ICN:2024:03 형식 파싱
                    parts = key.split(":")
                    if len(parts) >= 4:
                        origin = parts[1]
                        year = parts[2]
                        month = parts[3]

                        if origin not in months_by_origin:
                            months_by_origin[origin] = []
                        months_by_origin[origin].append(f"{year}-{month}")

                except Exception:
                    continue

            return {
                "success": True,
                "total_cached_months": total_count,
                "months_by_origin": months_by_origin,
                "cache_keys": keys[:20],  # 최대 20개만 표시
                "last_updated": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"통계 조회 실패: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "total_cached_months": 0,
                "months_by_origin": {},
            }