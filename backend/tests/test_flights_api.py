"""
항공편 API 테스트
"""

from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestFlightsAPI:
    """항공편 API 테스트 클래스"""

    @pytest.fixture
    def mock_amadeus_service(self):
        """Mock Amadeus 서비스"""
        with patch("app.api.v1.flights.get_amadeus_service") as mock:
            service = Mock()
            service.search_flight_offers.return_value = {
                "success": True,
                "data": [{"id": "1", "price": {"total": "300000"}}],
                "meta": {},
                "dictionaries": {},
            }
            mock.return_value = service
            yield service

    @pytest.fixture
    def mock_cache_service(self):
        """Mock 캐시 서비스"""
        with patch("app.api.v1.flights.get_cache_service") as mock:
            service = Mock()
            service.get_cache.return_value = None
            service.set_cache.return_value = None
            mock.return_value = service
            yield service

    def test_search_flights_success(self, mock_amadeus_service, mock_cache_service):
        """항공편 검색 성공 테스트"""
        request_data = {
            "origin": "ICN",
            "destination": "NRT",
            "departure_date": "2025-08-15",
            "adults": 1,
        }

        response = client.post("/api/v1/flights/search", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "flights" in data["data"]

    def test_search_flights_invalid_date(self):
        """잘못된 날짜 형식 테스트"""
        request_data = {
            "origin": "ICN",
            "destination": "NRT",
            "departure_date": "2025-13-50",  # 잘못된 날짜
            "adults": 1,
        }

        response = client.post("/api/v1/flights/search", json=request_data)

        assert response.status_code == 422

    def test_search_by_duration_success(self, mock_amadeus_service, mock_cache_service):
        """기간별 검색 성공 테스트"""
        request_data = {
            "origin": "ICN",
            "destination": "NRT",
            "departure_date": "2025-08-15",
            "duration_days": 4,
            "adults": 1,
        }

        response = client.post("/api/v1/flights/search-by-duration", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "trip_details" in data["data"]

    def test_airport_info_success(self, mock_amadeus_service, mock_cache_service):
        """공항 정보 조회 성공 테스트"""
        mock_amadeus_service.get_airport_info.return_value = {
            "success": True,
            "data": {"iata": "ICN", "name": "인천국제공항"},
        }

        response = client.get("/api/v1/flights/airport/ICN")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_airport_info_invalid_iata(self):
        """잘못된 IATA 코드 테스트"""
        response = client.get("/api/v1/flights/airport/INVALID")

        assert response.status_code == 500  # 검증 오류

    def test_popular_routes_success(self, mock_cache_service):
        """인기 노선 조회 성공 테스트"""
        response = client.get("/api/v1/flights/popular-routes?origin=ICN&limit=5")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "popular_routes" in data["data"]
        assert len(data["data"]["popular_routes"]) <= 5

    def test_health_check(self):
        """헬스 체크 테스트"""
        response = client.get("/api/v1/flights/health")

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "flights"
        assert data["status"] == "healthy"
