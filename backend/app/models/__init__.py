"""데이터베이스 모델"""
from app.models.base import Base
from app.models.user import User
from app.models.flight import Flight
from app.models.flight_search import FlightSearch
from app.models.recommendation import Recommendation
from app.models.user_preference import UserPreference
from app.models.price_history import PriceHistory

__all__ = [
    "Base",
    "User",
    "Flight",
    "FlightSearch",
    "Recommendation",
    "UserPreference",
    "PriceHistory",
]
