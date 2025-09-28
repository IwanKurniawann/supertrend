"""
Implementasi layanan bursa menggunakan CCXT (versi Live-Only yang Ditingkatkan)
"""

import ccxt.async_support as ccxt
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from domain.entities import MarketData
from domain.services import MarketDataService, ExchangeService

class KuCoinExchange(MarketDataService, ExchangeService):
    """
    Implementasi KuCoin exchange untuk data publik saja.
    Fokus pada penanganan error yang tangguh, koneksi yang stabil, dan dukungan proxy.
    """

    def __init__(self, http_proxy: Optional[str] = None, https_proxy: Optional[str] = None):
        self.http_proxy = http_proxy
        self.https_proxy = https_proxy
        self.exchange: Optional[ccxt.kucoin] = None
        self.logger = logging.getLogger(self.__class__.__name__)

    async def initialize(self) -> None:
        """Inisialisasi instance bursa CCXT untuk mode publik dengan penanganan error dan proxy."""
        try:
            config = {
                'enableRateLimit': True,
                'timeout': 30000,
                'options': {
                    'defaultHeaders': {
                        'KC-API-REMARK': '9527',
                    },
                },
            }
            
            # Tambahkan konfigurasi proxy jika tersedia
            proxies = {}
            if self.http_proxy:
                proxies['http'] = self.http_proxy
            if self.https_proxy:
                proxies['https'] = self.https_proxy
            
            if proxies:
                config['proxies'] = proxies
                self.logger.info(f"🔌 Menggunakan proxy untuk koneksi bursa: {proxies}")

            self.exchange = ccxt.kucoin(config)
            await self.exchange.load_markets()
            self.logger.info("✅ Bursa KuCoin berhasil diinisialisasi dalam Mode Publik.")

        except ccxt.ExchangeError as e:
            if "unavailable in the U.S." in str(e):
                self.logger.error("❌ Error geo-restriction dari KuCoin. Diperlukan proxy.", exc_info=False)
            else:
                self.logger.error(f"❌ Gagal menginisialisasi bursa KuCoin: {e}", exc_info=True)
            if self.exchange:
                await self.exchange.close()
            self.exchange = None
            raise
        except Exception as e:
            self.logger.error(f"❌ Error tak terduga saat inisialisasi KuCoin: {e}", exc_info=True)
            if self.exchange:
                await self.exchange.close()
            self.exchange = None
            raise

    async def close(self) -> None:
        """Menutup koneksi bursa dengan aman."""
        try:
            if self.exchange:
                await self.exchange.close()
                self.logger.info("🔒 Koneksi bursa ditutup")
        except Exception as e:
            self.logger.error(f"Error saat menutup koneksi bursa: {e}")

    async def test_connection(self) -> bool:
        """Tes konektivitas bursa."""
        if not self.exchange:
            self.logger.error("Tidak dapat mengetes koneksi, bursa belum diinisialisasi.")
            return False
        try:
            await self.exchange.fetch_status()
            return True
        except Exception as e:
            self.logger.error(f"Tes koneksi bursa gagal: {e}")
            return False

    async def get_ohlcv_data(self, symbol: str, timeframe: str, limit: int = 100) -> List[MarketData]:
        if not self.exchange:
            raise ConnectionError("Bursa KuCoin belum diinisialisasi.")
        try:
            if not self.exchange.markets:
                await self.exchange.load_markets(True)
            
            if symbol not in self.exchange.markets:
                raise ValueError(f"Simbol {symbol} tidak ditemukan di pasar KuCoin.")
            
            ohlcv = await self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            if not ohlcv: return []
            return [
                MarketData(
                    symbol=symbol, 
                    timeframe=timeframe, 
                    timestamp=datetime.fromtimestamp(i[0]/1000, tz=timezone.utc), 
                    open=i[1], 
                    high=i[2], 
                    low=i[3], 
                    close=i[4], 
                    volume=i[5]
                ) for i in ohlcv
            ]
        except Exception as e:
            self.logger.error(f"Gagal mengambil data OHLCV untuk {symbol}: {e}")
            raise

    async def validate_symbol(self, symbol: str) -> bool:
        """Memvalidasi simbol."""
        if not self.exchange:
            self.logger.warning("Bursa belum diinisialisasi, tidak dapat memvalidasi simbol.")
            return False
        try:
            if not self.exchange.markets:
                await self.exchange.load_markets(True)
            return symbol in self.exchange.markets
        except Exception as e:
            self.logger.error(f"Gagal memvalidasi simbol {symbol}: {e}")
            return False
            
    async def get_latest_price(self, symbol: str) -> float:
        if not self.exchange: raise ConnectionError("Bursa belum diinisialisasi.")
        ticker = await self.exchange.fetch_ticker(symbol)
        return float(ticker['last'])

    async def get_exchange_info(self) -> Dict[str, Any]:
        if not self.exchange: raise ConnectionError("Bursa belum diinisialisasi.")
        return {
            "name": "KuCoin", 
            "live": True, 
            "markets": len(self.exchange.markets) if self.exchange.markets else 0
        }

