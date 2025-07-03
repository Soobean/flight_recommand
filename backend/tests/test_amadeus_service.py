from unittest.mock import MagicMock, patch

import pytest
from app.services.amadeus_service import AmadeusService


class TestAmadeusService:
    """Amadeus 서비스 테스트 클래스"""

    @pytest.fixture
    def amadeus_service(self):
        """Amadeus 서비스 인스턴스 픽스처"""
        return AmadeusService()

    @patch("app.services.amadeus_service.config")
    def test_amadeus_service_initialization(self, mock_config):
        """Amadeus 서비스 초기화 테스트"""
        mock_config.side_effect = lambda key: {
            "AMADEUS_CLIENT_ID": "test_client_id",
            "AMADEUS_CLIENT_SECRET": "test_client_secret",
        }[key]

        service = AmadeusService()
        assert service.client is not None

    @pytest.mark.asyncio
    async def test_search_cheapest_dates_success(self, amadeus_service):
        """최저가 날짜 검색 성공 테스트"""
        # Mock 응답 데이터
        mock_response = MagicMock()
        mock_response.data = [
            {
                "type": "flight-date",
                "origin": "ICN",
                "destination": "NRT",
                "departureDate": "2025-08-15",
                "returnDate": "2025-08-18",
                "price": {"total": "280000", "currency": "KRW"},
            }
        ]

        with patch.object(
            amadeus_service.client.shopping.flight_dates,
            "get",
            return_value=mock_response,
        ):
            result = await amadeus_service.search_cheapest_dates(
                origin="ICN", destination="NRT", departure_date="2025-08-15", duration=4
            )

            assert result["success"] is True
            assert len(result["data"]) > 0
            assert result["data"][0]["origin"] == "ICN"
