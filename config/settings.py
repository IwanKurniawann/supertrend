"""
Configuration settings untuk trading bot
Menggunakan environment variables dengan fallback defaults
"""

import os
import logging
from typing import List
from dotenv import load_dotenv

# Muat variabel dari file .env jika ada (berguna untuk pengembangan lokal)
# Di GitHub Actions, variabel akan diambil dari Secrets.
load_dotenv()

class Settings:
    """Manajemen konfigurasi terpusat"""

    # --- Pengambilan Variabel Lingkungan ---
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")
    HTTP_PROXY: str = os.getenv("HTTP_PROXY", "")
    HTTPS_PROXY: str = os.getenv("HTTPS_PROXY", "")

    # --- Flag Fitur & Parameter Trading ---
    # Flag ini akan di-override di __init__ jika key yang relevan tidak ditemukan
    GEMINI_ANALYSIS_ENABLED: bool = os.getenv("GEMINI_ANALYSIS_ENABLED", "True").lower() == "true"
    ENABLE_NOTIFICATIONS: bool = os.getenv("ENABLE_NOTIFICATIONS", "True").lower() == "true"

    TRADING_PAIRS: List[str] = os.getenv(
        "TRADING_PAIRS",
        "BTC/USDT,ETH/USDT,SOL/USDT,ADA/USDT,LINK/USDT," \
        "XRP/USDT,DOGE/USDT,AVAX/USDT,DOT/USDT,LINK/USDT," \
        "SHIB/USDT,TRX/USDT,LTC/USDT,BCH/USDT,UNI/USDT," \
        "ATOM/USDT,NEAR/USDT,INJ/USDT,MANA/USDT,SAND/USDT," \
        "APE/USDT,ETC/USDT,XLM/USDT,ALGO/USDT,KAITO/USDT"
    ).split(",")

    PRIMARY_TIMEFRAME: str = os.getenv("PRIMARY_TIMEFRAME", "1m")
    HIGHER_TIMEFRAME: str = os.getenv("HIGHER_TIMEFRAME", "5m")
    PIVOT_PERIOD: int = int(os.getenv("PIVOT_PERIOD", "6"))
    ATR_FACTOR: float = float(os.getenv("ATR_FACTOR", "3.0"))
    ATR_PERIOD: int = int(os.getenv("ATR_PERIOD", "1"))
    OHLCV_LIMIT: int = int(os.getenv("OHLCV_LIMIT", "200"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    AI_CONFIDENCE_THRESHOLD: int = int(os.getenv("AI_CONFIDENCE_THRESHOLD", "6"))


    def __init__(self):
        """Validasi pengaturan dan menonaktifkan fitur secara dinamis jika kunci API hilang."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self._validate_and_configure_features()

    def _validate_and_configure_features(self) -> None:
        """
        Memeriksa kunci API yang diperlukan.
        Jika kunci hilang, log peringatan dan nonaktifkan fitur terkait.
        """
        # Validasi Analisis Gemini
        if self.GEMINI_ANALYSIS_ENABLED and not self.GEMINI_API_KEY:
            self.logger.warning(
                "GEMINI_API_KEY tidak ditemukan. Menonaktifkan analisis AI. "
                "Untuk mengaktifkan, atur GEMINI_API_KEY di environment variables atau GitHub Secrets."
            )
            self.GEMINI_ANALYSIS_ENABLED = False

        # Validasi Notifikasi Telegram
        if self.ENABLE_NOTIFICATIONS:
            if not self.TELEGRAM_BOT_TOKEN or not self.TELEGRAM_CHAT_ID:
                self.logger.warning(
                    "TELEGRAM_BOT_TOKEN atau TELEGRAM_CHAT_ID tidak ditemukan. Menonaktifkan notifikasi. "
                    "Untuk mengaktifkan, atur kedua variabel di environment variables atau GitHub Secrets."
                )
                self.ENABLE_NOTIFICATIONS = False

        self.logger.info(f"Status Fitur: Analisis AI -> {self.GEMINI_ANALYSIS_ENABLED}, Notifikasi -> {self.ENABLE_NOTIFICATIONS}")
