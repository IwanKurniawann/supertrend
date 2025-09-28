"""
Implementasi konkret dari GenerativeAIService menggunakan Google Gemini API.
"""

import os
import logging
import re
from typing import Dict, Any
import google.generativeai as genai

from domain.entities import IndicatorData, TrendDirection, AnalysisResult
from domain.services import GenerativeAIService
from config.settings import Settings

class GeminiService(GenerativeAIService):
    """
    Layanan untuk berinteraksi dengan Google Gemini API untuk analisis konfluens.
    """
    def __init__(self, settings: Settings):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.settings = settings
        self._configure_api()
        self.model = genai.GenerativeModel('gemini-1.5-flash-latest')

    def _configure_api(self):
        """Mengonfigurasi API key Gemini dari settings."""
        api_key = self.settings.GEMINI_API_KEY
        if not api_key:
            self.logger.error("GEMINI_API_KEY tidak ditemukan di environment variables.")
            raise ValueError("API Key Gemini tidak dikonfigurasi.")
        try:
            genai.configure(api_key=api_key)
            self.logger.info("✅ Layanan Gemini AI berhasil dikonfigurasi.")
        except Exception as e:
            self.logger.error(f"❌ Gagal mengonfigurasi Gemini AI: {e}", exc_info=True)
            raise

    def _construct_prompt(
        self,
        symbol: str,
        current_price: float,
        indicator_data: IndicatorData,
        higher_tf_trend: TrendDirection,
    ) -> str:
        """Membangun prompt yang detail dan terstruktur untuk analisis AI."""

        prompt = f"""
        Anda adalah seorang analis trading profesional dengan spesialisasi pada analisis konfluens multi-indikator dan multi-timeframe. Lakukan analisis objektif untuk pasangan {symbol} berdasarkan data berikut:

        **Data Pasar & Teknikal:**
        - Harga Terkini: ${current_price:,.4f}
        - Tren Timeframe Tinggi (4 Jam): **{higher_tf_trend.name}**
        - Tren Timeframe Utama (1 Jam): **{indicator_data.trend_direction.name}**
        - RSI (14) pada 1 Jam: {indicator_data.rsi:.2f}
        - MACD Line (1 Jam): {indicator_data.macd_line:,.5f}
        - MACD Signal (1 Jam): {indicator_data.macd_signal:,.5f}
        - Level Support Kunci (dari Swing Low): ${indicator_data.support_level or 0:,.4f}
        - Level Resistance Kunci (dari Swing High): ${indicator_data.resistance_level or 0:,.4f}

        **TUGAS ANDA:**
        1.  **Analisis Konfluens Bullish:** Sebutkan semua faktor dari data di atas yang mendukung potensi pergerakan harga NAIK (BUY).
        2.  **Analisis Konfluens Bearish:** Sebutkan semua faktor dari data di atas yang mendukung potensi pergerakan harga TURUN (SELL).
        3.  **Kesimpulan & Sentimen:** Berdasarkan perbandingan antara faktor bullish dan bearish, berikan kesimpulan akhir. Tentukan apakah sentimen pasar secara keseluruhan lebih condong ke **BUY**, **SELL**, atau **NEUTRAL**.
        4.  **Skor Keyakinan:** Berikan skor keyakinan (Confidence Score) dari 1 hingga 10 untuk kesimpulan Anda.

        **FORMAT JAWABAN (HARUS DIIKUTI):**
        Insight: [Ringkasan singkat 1-2 kalimat dari analisis Anda]
        Conclusion: [BUY/SELL/NEUTRAL]
        Confidence: [Angka dari 1 sampai 10]
        """
        return prompt

    async def get_confluence_insight(
        self,
        symbol: str,
        current_price: float,
        indicator_data: IndicatorData,
        higher_tf_trend: TrendDirection,
    ) -> Dict[str, Any]:
        """Mengirim data ke Gemini dan mem-parsing hasilnya."""
        prompt = self._construct_prompt(symbol, current_price, indicator_data, higher_tf_trend)
        try:
            self.logger.debug(f"Mengirim prompt ke Gemini untuk {symbol}...")
            response = await self.model.generate_content_async(prompt)

            # Ekstrak data menggunakan regex untuk ketahanan
            insight_match = re.search(r"Insight:\s*(.*)", response.text, re.IGNORECASE | re.DOTALL)
            conclusion_match = re.search(r"Conclusion:\s*(BUY|SELL|NEUTRAL)", response.text, re.IGNORECASE)
            confidence_match = re.search(r"Confidence:\s*(\d+)", response.text, re.IGNORECASE)

            if not all([insight_match, conclusion_match, confidence_match]):
                self.logger.warning(f"Gagal mem-parsing respons Gemini untuk {symbol}. Respons: {response.text}")
                return {"summary": "Gagal mem-parsing respons AI.", "conclusion": "NEUTRAL", "confidence_score": 0}

            insight = insight_match.group(1).strip()
            conclusion = conclusion_match.group(1).upper()
            confidence = int(confidence_match.group(1))

            self.logger.info(f"Analisis AI untuk {symbol} diterima: {conclusion} (Confidence: {confidence})")
            return {"summary": insight, "conclusion": conclusion, "confidence_score": confidence}

        except Exception as e:
            self.logger.error(f"Terjadi error saat berkomunikasi dengan Gemini API: {e}", exc_info=True)
            return {"summary": "Error saat menghubungi layanan AI.", "conclusion": "NEUTRAL", "confidence_score": 0}
