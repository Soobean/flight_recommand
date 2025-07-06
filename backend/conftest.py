"""
pytest 설정 파일
"""
import os
from unittest.mock import patch

import pytest


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """테스트 환경 설정"""
    # 테스트용 환경변수 설정
    os.environ[
        "SECRET_KEY"
    ] = "test-secret-key-minimum-32-characters-for-testing-purposes-only"
    os.environ["DEBUG"] = "true"
    os.environ["ENVIRONMENT"] = "test"
    os.environ["USE_REAL_AMADEUS"] = "false"
    os.environ["ENABLE_DUMMY_FALLBACK"] = "true"
    os.environ["REDIS_URL"] = "redis://localhost:6379/15"
    os.environ["CELERY_BROKER_URL"] = "redis://localhost:6379/14"
    os.environ["CELERY_RESULT_BACKEND"] = "redis://localhost:6379/13"


@pytest.fixture
def mock_settings():
    """테스트용 설정 목킹"""
    with patch("app.config.settings.settings") as mock:
        mock.SECRET_KEY = (
            "test-secret-key-minimum-32-characters-for-testing-purposes-only"
        )
        mock.DEBUG = True
        mock.ENVIRONMENT = "test"
        mock.USE_REAL_AMADEUS = False
        mock.ENABLE_DUMMY_FALLBACK = True
        yield mock
