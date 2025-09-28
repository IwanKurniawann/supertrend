"""
Domain services - Abstract interfaces (contracts)
This layer defines the contracts that infrastructure services must implement.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from .entities import MarketData, TradingSignal, NotificationMessage, AnalysisResult, TrendDirection, IndicatorData


class ExchangeService(ABC):
    """Abstract interface for exchange operations."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the exchange connection."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close the exchange connection."""
        pass

    @abstractmethod
    async def test_connection(self) -> bool:
        """Test the connection to the exchange."""
        pass

    @abstractmethod
    async def get_latest_price(self, symbol: str) -> float:
        """Get the latest price for a symbol."""
        pass

    @abstractmethod
    async def validate_symbol(self, symbol: str) -> bool:
        """Validate if a symbol exists on the exchange."""
        pass

    @abstractmethod
    async def get_exchange_info(self) -> Dict[str, Any]:
        """Get information about the exchange."""
        pass


class MarketDataService(ABC):
    """Abstract interface for market data services."""

    @abstractmethod
    async def get_ohlcv_data(self, symbol: str, timeframe: str, limit: int) -> List[MarketData]:
        """Fetch OHLCV data."""
        pass


class TradingAnalysisService(ABC):
    """Abstract interface for technical analysis services."""

    @abstractmethod
    async def analyze_market(
        self,
        symbol: str,
        primary_market_data: List[MarketData],
        higher_market_data: List[MarketData],
    ) -> Optional[AnalysisResult]:
        """Analyze market data and produce an analysis result."""
        pass


class GenerativeAIService(ABC):
    """Abstract interface for generative AI services."""

    @abstractmethod
    async def get_confluence_insight(
        self,
        symbol: str,
        current_price: float,
        indicator_data: IndicatorData,
        higher_tf_trend: TrendDirection,
    ) -> Dict[str, Any]:
        """Get confluence insight from the AI model."""
        pass


class NotificationService(ABC):
    """Abstract interface for notification services."""

    @abstractmethod
    async def send_signal_notification(self, signal: TradingSignal) -> bool:
        """Send a trading signal notification."""
        pass

    @abstractmethod
    async def send_custom_message(self, message: NotificationMessage) -> bool:
        """Send a custom notification message."""
        pass

    @abstractmethod
    async def send_error_notification(self, error_message: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """Send an error notification."""
        pass

    @abstractmethod
    async def test_connection(self) -> bool:
        """Test the notification service connection."""
        pass
