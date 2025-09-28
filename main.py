#!/usr/bin/env python3
"""
Entry point untuk aplikasi trading bot cerdas dengan arsitektur bersih.
Mengintegrasikan analisis teknikal dengan validasi AI dari Gemini.
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Menambahkan direktori saat ini ke path agar impor berfungsi dengan benar
sys.path.append(str(Path(__file__).parent))

from config.settings import Settings
from application.use_cases import TradingUseCase
from infrastructure.exchanges import KuCoinExchange
from infrastructure.telegram_service import TelegramService
from infrastructure.technical_analysis import TechnicalAnalysisService
from infrastructure.gemini_service import GeminiService

def setup_logging(log_level: str):
    """Mengkonfigurasi logging untuk aplikasi."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('trading_bot.log', mode='w') # 'w' untuk overwrite log setiap run
        ]
    )

async def main():
    """Titik masuk utama aplikasi."""
    trading_use_case = None
    try:
        # 1. Konfigurasi Logging terlebih dahulu
        # Ini penting agar kelas Settings bisa log warning jika ada config yang hilang
        log_level = os.getenv("LOG_LEVEL", "INFO")
        setup_logging(log_level)
        
        # 2. Muat Konfigurasi
        settings = Settings()
        logging.info("🚀 Bot Trading Cerdas Dimulai...")
        logging.info(f"Pivot Period: {settings.PIVOT_PERIOD}, Confidence Threshold: {settings.AI_CONFIDENCE_THRESHOLD}")

        # 3. Inisialisasi Layanan (Dependency Injection)
        exchange = KuCoinExchange(
            http_proxy=settings.HTTP_PROXY,
            https_proxy=settings.HTTPS_PROXY
        )
        telegram_service = TelegramService(
            token=settings.TELEGRAM_BOT_TOKEN,
            chat_id=settings.TELEGRAM_CHAT_ID
        )
        technical_analysis = TechnicalAnalysisService(
            pivot_period=settings.PIVOT_PERIOD,
            atr_factor=settings.ATR_FACTOR,
            atr_period=settings.ATR_PERIOD
        )
        # FIX: Pass the entire 'settings' object instead of just 'api_key'
        ai_service = GeminiService(
            settings=settings
        )

        # 4. Inisialisasi Use Case Utama
        trading_use_case = TradingUseCase(
            exchange=exchange,
            telegram_service=telegram_service,
            technical_analysis=technical_analysis,
            ai_service=ai_service,
            settings=settings
        )

        # 5. Jalankan Alur Kerja
        await trading_use_case.initialize_services()
        await trading_use_case.analyze_and_notify()

        logging.info("✅ Siklus analisis berhasil diselesaikan.")

    except ValueError as val_err:
        logging.critical(f"❌ Kesalahan Konfigurasi Kritis: {val_err}", exc_info=False)
        sys.exit(1)
    except Exception as e:
        logging.error(f"❌ Terjadi error tak terduga di level aplikasi: {e}", exc_info=True)
        # Kirim notifikasi error darurat jika mungkin
        try:
            # Periksa apakah notifikasi diaktifkan sebelum mengirim
            if Settings().ENABLE_NOTIFICATIONS:
                emergency_telegram = TelegramService(
                    token=Settings().TELEGRAM_BOT_TOKEN, # Muat ulang settings untuk kasus darurat
                    chat_id=Settings().TELEGRAM_CHAT_ID
                )
                await emergency_telegram.send_error_notification(f"🚨 BOT CRITICAL ERROR: {str(e)}")
        except Exception as telegram_err:
            logging.error(f"Gagal mengirim notifikasi error darurat: {telegram_err}")
        sys.exit(1)

    finally:
        # 6. Pastikan layanan ditutup dengan benar
        if trading_use_case:
            await trading_use_case.shutdown_services()
        logging.info("🔄 Bot Trading Cerdas Selesai.")

if __name__ == "__main__":
    # Menjalankan loop event asyncio
    asyncio.run(main())

