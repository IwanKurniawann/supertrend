"""
Configuration settings untuk trading bot
Menggunakan environment variables dengan fallback defaults
"""

import os
from typing import List

class Settings:
    """Manajemen konfigurasi terpusat"""

    # Konfigurasi Gemini AI
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_ANALYSIS_ENABLED: bool = os.getenv("GEMINI_ANALYSIS_ENABLED", "True").lower() == "true"

    # Konfigurasi Telegram
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")

    # Konfigurasi Proxy (Opsional, untuk lingkungan seperti GitHub Actions)
    HTTP_PROXY: str = os.getenv("HTTP_PROXY", "")
    HTTPS_PROXY: str = os.getenv("HTTPS_PROXY", "")

    # Parameter Trading
    TRADING_PAIRS: List[str] = os.getenv(
        "TRADING_PAIRS",
        "BTC/USDT,ETH/USDT,SOL/USDT,LINK/USDT,AVAX/USDT"
    ).split(",")

    PRIMARY_TIMEFRAME: str = os.getenv("PRIMARY_TIMEFRAME", "1h")
    HIGHER_TIMEFRAME: str = os.getenv("HIGHER_TIMEFRAME", "4h")

    # Pivot Period disesuaikan untuk swing yang lebih signifikan
    PIVOT_PERIOD: int = int(os.getenv("PIVOT_PERIOD", "5"))
    ATR_FACTOR: float = float(os.getenv("ATR_FACTOR", "3.0"))
    ATR_PERIOD: int = int(os.getenv("ATR_PERIOD", "10"))

    OHLCV_LIMIT: int = int(os.getenv("OHLCV_LIMIT", "200"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    ENABLE_NOTIFICATIONS: bool = os.getenv("ENABLE_NOTIFICATIONS", "True").lower() == "true"

    def __init__(self):
        """Validasi pengaturan yang diperlukan saat inisialisasi"""
        self._validate_required_settings()

    def _validate_required_settings(self) -> None:
        """Validasi bahwa variabel lingkungan yang diperlukan sudah diatur"""
        required_settings = [
            ("TELEGRAM_BOT_TOKEN", self.TELEGRAM_BOT_TOKEN),
            ("TELEGRAM_CHAT_ID", self.TELEGRAM_CHAT_ID),
        ]

        if self.GEMINI_ANALYSIS_ENABLED:
            required_settings.append(("GEMINI_API_KEY", self.GEMINI_API_KEY))

        missing_settings = [name for name, value in required_settings if not value or not value.strip()]

        if missing_settings:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_settings)}"
            )

