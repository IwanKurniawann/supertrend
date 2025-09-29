"""
Use cases - Application business logic
Orchestrates domain services and infrastructure services to perform trading analysis.
"""

import logging
import asyncio
from typing import List, Optional, Dict, Any

from domain.entities import AnalysisResult, TradingSignal, SignalType
from domain.services import (
    MarketDataService, 
    TradingAnalysisService, 
    NotificationService, 
    GenerativeAIService,
    ExchangeService,
)
from config.settings import Settings

class TradingUseCase:
    """
    Use case utama untuk menganalisis, memvalidasi sinyal dengan AI, dan mengirim notifikasi.
    Mengkoordinasikan semua layanan untuk alur kerja trading yang lengkap dan cerdas.
    """

    def __init__(
        self,
        exchange: MarketDataService and ExchangeService,
        telegram_service: NotificationService,
        technical_analysis: TradingAnalysisService,
        ai_service: GenerativeAIService,
        settings: Settings,
    ):
        self.exchange = exchange
        self.telegram_service = telegram_service
        self.technical_analysis = technical_analysis
        self.ai_service = ai_service
        self.settings = settings
        self.logger = logging.getLogger(self.__class__.__name__)

    async def initialize_services(self) -> None:
        """Inisialisasi semua layanan eksternal yang diperlukan."""
        self.logger.info("🔌 Menginisialisasi layanan eksternal...")
        await self.exchange.initialize()
        self.logger.info("✅ Semua layanan berhasil diinisialisasi.")

    async def shutdown_services(self) -> None:
        """Menutup koneksi layanan eksternal dengan aman."""
        self.logger.info("🔌 Menutup layanan eksternal...")
        await self.exchange.close()
        self.logger.info("✅ Semua layanan berhasil ditutup.")

    async def _is_signal_ai_validated(self, signal: TradingSignal, ai_insight: Dict[str, Any]) -> bool:
        """Memvalidasi sinyal teknikal dengan hasil analisis AI."""
        if not ai_insight or ai_insight.get('conclusion') == "NEUTRAL":
            self.logger.warning(f"Tidak ada insight AI atau netral untuk {signal.symbol}, validasi gagal.")
            return False

        ai_conclusion = ai_insight.get('conclusion', '').upper()
        ai_confidence = ai_insight.get('confidence', 0)
        
        required_confidence = self.settings.AI_CONFIDENCE_THRESHOLD

        signal_matches_conclusion = (signal.signal_type.value == ai_conclusion)
        is_confident = (ai_confidence >= required_confidence)

        if signal_matches_conclusion and is_confident:
            self.logger.info(f"✅ Sinyal {signal.symbol} divalidasi oleh AI (Confidence: {ai_confidence}/{required_confidence}).")
            return True
        else:
            self.logger.info(
                f"❌ Sinyal {signal.symbol} DITOLAK oleh AI. "
                f"Sinyal: {signal.signal_type.value}, Kesimpulan AI: {ai_conclusion}, "
                f"Confidence: {ai_confidence}/{required_confidence}"
            )
            return False

    async def _analyze_and_notify_single_pair(self, pair: str) -> None:
        """Menganalisis satu pasangan, memvalidasi dengan AI, dan mengirim notifikasi jika valid."""
        self.logger.info(f"📊 Menganalisis {pair}...")
        
        analysis_result = await self._run_technical_analysis(pair)
        if not analysis_result or not analysis_result.has_signal():
            self.logger.info(f"➡️ {pair}: Tidak ada sinyal teknikal awal (HOLD).")
            return

        if not self.settings.GEMINI_ANALYSIS_ENABLED:
            self.logger.info(f"Analisis AI dinonaktifkan. Sinyal untuk {pair} tidak divalidasi.")
            return

        self.logger.info(f"🧠 Meminta validasi AI untuk sinyal {analysis_result.signal.signal_type.value} pada {pair}...")
        
        ai_insight = await self.ai_service.get_confluence_insight(
            symbol=analysis_result.symbol,
            current_price=analysis_result.market_data.close,
            indicator_data=analysis_result.indicator_data,
            higher_tf_trend=analysis_result.higher_tf_trend
        )
        
        # SOLUSI: Menambahkan 'await' yang hilang untuk menjalankan validasi AI dengan benar.
        if await self._is_signal_ai_validated(analysis_result.signal, ai_insight):
            # Perkaya sinyal dengan semua data yang diperlukan SEBELUM mengirim notifikasi.
            analysis_result.signal.ai_insight = ai_insight
            analysis_result.signal.ai_confidence_score = ai_insight.get('confidence', 0)
            analysis_result.signal.higher_tf_trend = analysis_result.higher_tf_trend
            
            self.logger.info(
                f"🚨 SINYAL TERVALIDASI AI: {analysis_result.signal.signal_type.value} "
                f"untuk {pair} @ {analysis_result.signal.price:.4f}"
            )
            
            if self.settings.ENABLE_NOTIFICATIONS:
                await self.telegram_service.send_signal_notification(analysis_result.signal)

    async def _run_technical_analysis(self, symbol: str) -> Optional[AnalysisResult]:
        """Menjalankan analisis teknikal untuk satu pasangan."""
        try:
            primary_data_task = self.exchange.get_ohlcv_data(
                symbol=symbol,
                timeframe=self.settings.PRIMARY_TIMEFRAME,
                limit=self.settings.OHLCV_LIMIT
            )
            higher_data_task = self.exchange.get_ohlcv_data(
                symbol=symbol,
                timeframe=self.settings.HIGHER_TIMEFRAME,
                limit=self.settings.OHLCV_LIMIT
            )
            
            primary_market_data, higher_market_data = await asyncio.gather(primary_data_task, higher_data_task)

            if not primary_market_data or len(primary_market_data) < 50:
                self.logger.warning(f"Data timeframe utama untuk {symbol} tidak cukup.")
                return None
            if not higher_market_data or len(higher_market_data) < 20:
                self.logger.warning(f"Data timeframe tinggi untuk {symbol} tidak cukup.")
                return None

            return await self.technical_analysis.analyze_market(
                symbol=symbol,
                primary_market_data=primary_market_data,
                higher_market_data=higher_market_data
            )
        except Exception as e:
            self.logger.error(f"Gagal menjalankan analisis teknikal untuk {symbol}: {e}", exc_info=True)
            return None

    async def analyze_and_notify(self) -> None:
        """
        Alur kerja utama: menganalisis semua pasangan, memvalidasi dengan AI, dan mengirim notifikasi.
        """
        self.logger.info("🔍 Memulai siklus analisis trading...")
        
        tasks = []
        for pair in self.settings.TRADING_PAIRS:
            tasks.append(self._analyze_and_notify_single_pair(pair.strip()))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                pair = self.settings.TRADING_PAIRS[i].strip()
                self.logger.error(f"Error saat memproses {pair}: {result}", exc_info=False)
                if self.settings.ENABLE_NOTIFICATIONS:
                    await self.telegram_service.send_error_notification(f"Gagal memproses {pair}: {result}")
        
        self.logger.info("✅ Siklus analisis trading selesai.")

