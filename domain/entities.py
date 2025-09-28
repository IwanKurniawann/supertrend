"""
Domain entities - Core business objects
Tidak memiliki dependencies ke layer lain
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from enum import Enum

class SignalType(Enum):
    """Tipe sinyal trading"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

class TrendDirection(Enum):
    """Arah tren pasar"""
    BULLISH = 1
    BEARISH = -1
    NEUTRAL = 0

@dataclass
class MarketData:
    """Entitas data pasar berisi informasi OHLCV"""
    symbol: str
    timeframe: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

@dataclass
class IndicatorData:
    """Hasil kalkulasi indikator teknikal"""
    symbol: str
    timestamp: datetime
    # Pivot Points & Support/Resistance
    support_level: Optional[float] = None
    resistance_level: Optional[float] = None
    # SuperTrend
    supertrend: Optional[float] = None
    trend_direction: TrendDirection = TrendDirection.NEUTRAL
    # Indikator Tambahan untuk Analisis Konfluens
    rsi: Optional[float] = None
    macd_line: Optional[float] = None
    macd_signal: Optional[float] = None

@dataclass
class TradingSignal:
    """Entitas sinyal trading yang dihasilkan"""
    symbol: str
    signal_type: SignalType
    timestamp: datetime
    price: float
    supertrend_value: float
    trend_direction: TrendDirection
    timeframe: str
    # Detail Manajemen Risiko
    entry_price: float
    stop_loss: float
    take_profit: float
    # Konteks Analisis Tambahan
    support_level: Optional[float] = None
    resistance_level: Optional[float] = None
    higher_tf_trend: Optional[TrendDirection] = None  # Added this field
    # Insight dari AI (baru)
    ai_insight: Optional[Dict[str, Any]] = None
    ai_confidence_score: Optional[int] = None
    indicator_values: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AnalysisResult:
    """Hasil analisis lengkap untuk sebuah pasangan trading"""
    symbol: str
    timeframe: str
    timestamp: datetime
    market_data: MarketData
    indicator_data: IndicatorData
    signal: Optional[TradingSignal] = None
    higher_tf_trend: Optional[TrendDirection] = None  # Added this field
    analysis_duration_ms: Optional[float] = None # Added this field

    def has_signal(self) -> bool:
        """Memeriksa apakah analisis menghasilkan sinyal trading (bukan HOLD)"""
        return (
            self.signal is not None and
            self.signal.signal_type in [SignalType.BUY, SignalType.SELL]
        )

@dataclass
class NotificationMessage:
    """Entitas pesan notifikasi"""
    recipient: str
    subject: str
    content: str
    timestamp: datetime
    message_type: str = "info"  # info, warning, error, success
    parse_mode: str = "HTML"
    disable_web_page_preview: bool = True
    
    def validate(self):
        """Basic validation for the notification message."""
        if not self.recipient or not self.subject or not self.content:
            raise ValueError("Recipient, subject, and content cannot be empty.")

    def format_telegram_message(self) -> str:
        """Memformat pesan untuk Telegram dengan format HTML"""
        emoji_map = {
            "info": "ℹ️", "warning": "⚠️", "error": "❌",
            "success": "✅", "buy": "🚀", "sell": "🔴",
        }
        emoji = emoji_map.get(self.message_type.lower(), "📊")
        wib_tz = timezone(timedelta(hours=7))
        time_str = self.timestamp.astimezone(wib_tz).strftime("%d-%m-%Y %H:%M WIB")
        formatted_message = f"{emoji} <b>{self.subject}</b>\n\n{self.content}"
        formatted_message += f"\n\n<pre>⏰ {time_str}</pre>"
        return formatted_message
