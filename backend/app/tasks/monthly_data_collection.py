import asyncio
import json
import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict

import redis
from celery import Celery
from celery.schedules import crontab

from app.config.settings import settings
from app.services.monthly_price_analyzer import MonthlyPriceAnalyzer

# Celery 앱 설정
celery_app = Celery(
    "monthly_flight_analyzer",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Redis 클라이언트
redis_client = redis.Redis.from_url(settings.REDIS_URL)

logger = logging.getLogger(__name__)


# 메인 데이터 수집 태스크


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 3})
def collect_monthly_cheapest_data(self, year: int, month: int, origin: str = "ICN"):
    """
    특정 월의 지역별 최저가 데이터 수집

    Args:
        year: 대상 연도
        month: 대상 월
        origin: 출발지 공항 코드
    """
    try:
        logger.info(f"월별 데이터 수집 시작: {year}년 {month}월, 출발지: {origin}")

        # 비동기 함수를 동기적으로 실행
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        analyzer = MonthlyPriceAnalyzer()
        result = loop.run_until_complete(
            analyzer.get_monthly_cheapest_dates(
                target_year=year, target_month=month, origin=origin, trip_duration=4
            )
        )

        loop.close()

        if result["success"]:
            # Redis에 캐시 저장
            cache_key = f"monthly_cheapest:{origin}:{year}:{month:02d}"
            cache_data = {
                "data": result["data"],
                "collected_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(hours=12)).isoformat(),
            }

            redis_client.setex(
                cache_key,
                timedelta(hours=12),  # 12시간 캐시
                json.dumps(cache_data, default=str),
            )

            logger.info(f"데이터 수집 완료 및 캐시 저장: {cache_key}")

            # 작업 상태 업데이트
            self.update_state(
                state="SUCCESS",
                meta={
                    "year": year,
                    "month": month,
                    "origin": origin,
                    "regions_collected": len(result["data"].get("regions", {})),
                    "cache_key": cache_key,
                },
            )

            return f"Successfully collected data for {year}-{month:02d} from {origin}"

        else:
            raise Exception(f"데이터 수집 실패: {result.get('message', 'Unknown error')}")

    except Exception as e:
        logger.error(f"월별 데이터 수집 실패: {str(e)}")

        # 실패 시 재시도
        self.update_state(
            state="FAILURE", meta={"error": str(e), "year": year, "month": month}
        )

        # 30분 후 재시도
        raise self.retry(countdown=1800, max_retries=3)


# 자동 스케줄링 태스크


@celery_app.task
def collect_current_month_data():
    """
    이번 달 데이터 수집 (메인 화면용)
    매일 새벽 3시에 실행
    """
    today = date.today()
    return collect_monthly_cheapest_data.delay(
        year=today.year, month=today.month, origin="ICN"
    )


@celery_app.task
def collect_next_month_data():
    """
    다음 달 데이터 수집 (미리 준비)
    매주 일요일 새벽 4시에 실행
    """
    today = date.today()
    next_month = today.month + 1 if today.month < 12 else 1
    next_year = today.year if today.month < 12 else today.year + 1

    return collect_monthly_cheapest_data.delay(
        year=next_year, month=next_month, origin="ICN"
    )


@celery_app.task
def collect_popular_months_data():
    """
    인기 여행 월 데이터 미리 수집
    매월 1일 새벽 2시에 실행
    """
    today = date.today()
    current_year = today.year

    # 인기 여행 월 (봄, 가을)
    popular_months = [3, 4, 5, 10, 11]

    tasks = []
    for month in popular_months:
        # 현재 월 이후의 인기 월만 수집
        if month >= today.month:
            task = collect_monthly_cheapest_data.delay(
                year=current_year, month=month, origin="ICN"
            )
            tasks.append(task.id)
        elif month < today.month:
            # 내년 동일 월
            task = collect_monthly_cheapest_data.delay(
                year=current_year + 1, month=month, origin="ICN"
            )
            tasks.append(task.id)

    logger.info(f"인기 월 데이터 수집 시작: {len(tasks)}개 작업")
    return tasks


# 캐시 관리 태스크


@celery_app.task
def cleanup_expired_cache():
    """
    만료된 캐시 데이터 정리
    매일 새벽 1시에 실행
    """
    try:
        # 월별 캐시 키 패턴
        pattern = "monthly_cheapest:*"
        keys = redis_client.keys(pattern)

        cleaned_count = 0
        for key in keys:
            try:
                data = redis_client.get(key)
                if data:
                    cache_info = json.loads(data)
                    expires_at = datetime.fromisoformat(
                        cache_info.get("expires_at", "")
                    )

                    if datetime.now() > expires_at:
                        redis_client.delete(key)
                        cleaned_count += 1

            except (json.JSONDecodeError, ValueError, KeyError):
                # 잘못된 형식의 캐시는 삭제
                redis_client.delete(key)
                cleaned_count += 1

        logger.info(f"만료된 캐시 {cleaned_count}개 정리 완료")
        return f"Cleaned {cleaned_count} expired cache entries"

    except Exception as e:
        logger.error(f"캐시 정리 실패: {str(e)}")
        return f"Cache cleanup failed: {str(e)}"


@celery_app.task
def update_cache_statistics():
    """
    캐시 사용 통계 업데이트
    매시간 실행
    """
    try:
        pattern = "monthly_cheapest:*"
        keys = redis_client.keys(pattern)

        stats = {
            "total_cached_months": len(keys),
            "cache_keys": [key.decode() for key in keys],
            "last_updated": datetime.now().isoformat(),
        }

        # 통계 정보 저장
        redis_client.setex("cache_statistics", timedelta(hours=1), json.dumps(stats))

        return stats

    except Exception as e:
        logger.error(f"캐시 통계 업데이트 실패: {str(e)}")
        return {"error": str(e)}


# 수동 실행 태스크


@celery_app.task
def force_collect_month_data(year: int, month: int, origin: str = "ICN"):
    """
    특정 월 데이터 강제 수집 (관리자용)
    """
    logger.info(f"강제 데이터 수집 요청: {year}년 {month}월")

    # 기존 캐시 삭제
    cache_key = f"monthly_cheapest:{origin}:{year}:{month:02d}"
    redis_client.delete(cache_key)

    # 새로 수집
    return collect_monthly_cheapest_data.delay(year, month, origin)


@celery_app.task
def collect_multi_origin_data(year: int, month: int, origins: list = None):
    """
    여러 출발지에 대한 데이터 수집
    """
    if origins is None:
        origins = ["ICN"]  # 현재는 ICN만 지원

    tasks = []
    for origin in origins:
        task = collect_monthly_cheapest_data.delay(year, month, origin)
        tasks.append(task.id)

    return tasks


# Celery Beat 스케줄 설정

celery_app.conf.beat_schedule = {
    # 매일 새벽 3시 - 이번 달 데이터 수집
    "collect-current-month": {
        "task": "app.tasks.monthly_data_collection.collect_current_month_data",
        "schedule": crontab(hour=3, minute=0),
    },
    # 매주 일요일 새벽 4시 - 다음 달 데이터 수집
    "collect-next-month": {
        "task": "app.tasks.monthly_data_collection.collect_next_month_data",
        "schedule": crontab(hour=4, minute=0, day_of_week=0),
    },
    # 매월 1일 새벽 2시 - 인기 월 데이터 수집
    "collect-popular-months": {
        "task": "app.tasks.monthly_data_collection.collect_popular_months_data",
        "schedule": crontab(hour=2, minute=0, day_of_month=1),
    },
    # 매일 새벽 1시 - 만료된 캐시 정리
    "cleanup-expired-cache": {
        "task": "app.tasks.monthly_data_collection.cleanup_expired_cache",
        "schedule": crontab(hour=1, minute=0),
    },
    # 매시간 - 캐시 통계 업데이트
    "update-cache-stats": {
        "task": "app.tasks.monthly_data_collection.update_cache_statistics",
        "schedule": crontab(minute=0),
    },
}

celery_app.conf.timezone = "Asia/Seoul"


#  헬퍼 함수


def get_cached_monthly_data(
    year: int, month: int, origin: str = "ICN"
) -> Dict[str, Any]:
    """
    캐시된 월별 데이터 조회

    Returns:
        캐시된 데이터 또는 None
    """
    cache_key = f"monthly_cheapest:{origin}:{year}:{month:02d}"

    try:
        cached_data = redis_client.get(cache_key)
        if cached_data:
            return json.loads(cached_data)
    except (json.JSONDecodeError, Exception) as e:
        logger.warning(f"캐시 데이터 읽기 실패: {str(e)}")

    return None


def is_month_data_available(year: int, month: int, origin: str = "ICN") -> bool:
    """
    해당 월 데이터가 캐시에 있는지 확인
    """
    cache_key = f"monthly_cheapest:{origin}:{year}:{month:02d}"
    return redis_client.exists(cache_key) > 0


def trigger_month_collection_if_needed(
    year: int, month: int, origin: str = "ICN"
) -> str:
    """
    필요시 월별 데이터 수집 트리거

    Returns:
        작업 ID 또는 "already_exists"
    """
    if not is_month_data_available(year, month, origin):
        task = collect_monthly_cheapest_data.delay(year, month, origin)
        return task.id

    return "already_exists"
