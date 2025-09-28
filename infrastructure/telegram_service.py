"""
Implementasi layanan notifikasi menggunakan Telegram Bot API.
Bertugas memformat dan mengirim semua jenis pesan kepada pengguna.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any

from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError

from domain.entities import TradingSignal, NotificationMessage, SignalType, TrendDirection
from domain.services import NotificationService

class TelegramService(NotificationService):
    """
    Implementasi layanan notifikasi Telegram.
    Mengirim sinyal trading, pesan kustom, dan notifikasi error.
    """

    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = chat_id
        self.bot: Optional[Bot] = None
        self.logger = logging.getLogger(self.__class__.__name__)
        self._initialize_bot()

    def _initialize_bot(self) -> None:
        """Inisialisasi instance Telegram bot."""
        try:
            self.bot = Bot(token=self.token)
            self.logger.info("✅ Bot Telegram berhasil diinisialisasi.")
        except Exception as e:
            self.logger.error(f"❌ Gagal menginisialisasi bot Telegram: {e}")
            raise

    async def test_connection(self) -> bool:
        """Tes koneksi bot Telegram."""
        try:
            if not self.bot: self._initialize_bot()
            bot_info = await self.bot.get_me()
            self.logger.debug(f"Info Bot: @{bot_info.username}")
            return True
        except Exception as e:
            self.logger.error(f"Tes koneksi Telegram gagal: {e}")
            return False

    async def send_signal_notification(self, signal: TradingSignal) -> bool:
        """Mengirim notifikasi sinyal trading yang telah diformat."""
        try:
            message_content = self._format_signal_message(signal)
            subject = f"AI VALIDATED SIGNAL | {signal.symbol}"

            message = NotificationMessage(
                recipient=self.chat_id,
                subject=subject,
                content=message_content,
                timestamp=signal.timestamp,
                message_type=signal.signal_type.value.lower()
            )
            return await self.send_custom_message(message)
        except Exception as e:
            self.logger.error(f"Gagal mengirim notifikasi sinyal: {e}")
            return False

    async def send_custom_message(self, message: NotificationMessage) -> bool:
        """Mengirim pesan kustom yang sudah diformat."""
        try:
            if not self.bot: self._initialize_bot()
            message.validate()
            formatted_text = message.format_telegram_message()

            await self.bot.send_message(
                chat_id=message.recipient,
                text=formatted_text,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=message.disable_web_page_preview
            )
            self.logger.debug(f"📱 Pesan terkirim ke Telegram: {message.subject}")
            return True
        except TelegramError as e:
            self.logger.error(f"Telegram API error: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Gagal mengirim pesan kustom: {e}")
            return False

    async def send_error_notification(
        self, error_message: str, context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Mengirim notifikasi error."""
        try:
            content = f"🚨 <b>Error Terjadi</b>\n\n<code>{error_message}</code>"
            if context:
                content += "\n\n<b>Konteks:</b>\n"
                for key, value in context.items():
                    content += f"• <b>{key}:</b> {value}\n"

            error_notification = NotificationMessage(
                recipient=self.chat_id, subject="Bot Error", content=content,
                timestamp=datetime.now(timezone.utc), message_type="error"
            )
            return await self.send_custom_message(error_notification)
        except Exception as e:
            self.logger.error(f"Gagal mengirim notifikasi error: {e}")
            return False

    def _format_signal_message(self, signal: TradingSignal) -> str:
        """Memformat sinyal trading menjadi pesan yang kaya informasi dengan insight AI."""
        
        signal_icon = "🚀" if signal.signal_type == SignalType.BUY else "🔴"
        trend_icon = "📈" if signal.trend_direction == TrendDirection.BULLISH else "📉"
        
        # --- Header ---
        message = f"<b>{signal.symbol} | {signal.timeframe} | {signal.signal_type.value} SIGNAL</b> {signal_icon}\n\n"
        
        # --- Gemini AI Confluence ---
        if signal.ai_insight:
            message += "<b>🤖 Gemini AI Confluence:</b>\n"
            message += f"<i>{signal.ai_insight.get('summary', 'N/A')}</i>\n"
            message += f"Confidence Score: <b>{signal.ai_insight.get('confidence_score', 'N/A')}/10</b>\n\n"

        # --- Manajemen Risiko ---
        message += "<b>Manajemen Risiko:</b>\n"
        message += f" Zona Entri: <code>${signal.entry_price:,.4f}</code>\n"
        message += f" 🎯 Target Profit: <code>${signal.take_profit:,.4f}</code>\n"
        message += f" 🛡️ Stop Loss: <code>${signal.stop_loss:,.4f}</code>\n\n"
        
        # --- Detail Analisis Teknikal ---
        message += "<b>Detail Analisis Teknikal:</b>\n"
        message += f" {trend_icon} Tren (1h/4h): <b>{signal.trend_direction.name} / {signal.higher_tf_trend.name}</b>\n"
        message += f" 📊 SuperTrend: <code>${signal.supertrend_value:,.4f}</code>\n"
        if signal.indicator_values:
            rsi = signal.indicator_values.get('rsi')
            message += f" ⚡️ RSI (14): <code>{rsi:.2f}</code>\n" if rsi else ""
        if signal.resistance_level:
            message += f" 📈 Resistance: <code>${signal.resistance_level:,.4f}</code>\n"
        if signal.support_level:
            message += f" 📉 Support: <code>${signal.support_level:,.4f}</code>\n"
            
        # --- Disclaimer ---
        message += "\n<i>*DYOR. Sinyal ini adalah hasil analisis otomatis yang divalidasi oleh AI.</i>"

        return message

