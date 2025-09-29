"""
Implementasi layanan analisis teknikal menggunakan pandas-ta.
Bertugas menghitung semua indikator yang diperlukan untuk analisis.
"""

import pandas as pd
import logging
from typing import List, Dict, Optional
import pandas_ta as ta

from domain.entities import (
    MarketData,
    IndicatorData,
    TradingSignal,
    AnalysisResult,
    SignalType,
    TrendDirection,
)
from domain.services import TradingAnalysisService

class TechnicalAnalysisService(TradingAnalysisService):
    """
    Implementasi analisis teknis menggunakan pandas-ta dengan konfirmasi multi-timeframe.
    """

    def __init__(
        self,
        pivot_period: int = 6,
        atr_factor: float = 3.0,
        atr_period: int = 1,
    ):
        self.pivot_period = pivot_period
        self.atr_factor = atr_factor
        self.atr_period = atr_period
        self.logger = logging.getLogger(self.__class__.__name__)

    def _market_data_to_dataframe(self, market_data: List[MarketData]) -> pd.DataFrame:
        """Mengonversi daftar MarketData menjadi pandas DataFrame."""
        data = [
            {
                "timestamp": md.timestamp,
                "open": md.open,
                "high": md.high,
                "low": md.low,
                "close": md.close,
                "volume": md.volume,
            }
            for md in market_data
        ]
        df = pd.DataFrame(data)
        df.set_index("timestamp", inplace=True)
        df.sort_index(inplace=True)
        return df

    async def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Menghitung semua indikator teknikal yang diperlukan."""
        # SuperTrend
        supertrend_df = df.ta.supertrend(length=self.atr_period, multiplier=self.atr_factor)
        df["supertrend"] = supertrend_df[f"SUPERT_{self.atr_period}_{self.atr_factor}"]
        df["supertrend_direction"] = supertrend_df[f"SUPERTd_{self.atr_period}_{self.atr_factor}"]
        
        # RSI
        df["rsi"] = df.ta.rsi(length=14)
        
        # MACD
        macd_df = df.ta.macd(fast=12, slow=26, signal=9)
        df["macd_line"] = macd_df["MACD_12_26_9"]
        df["macd_signal"] = macd_df["MACDs_12_26_9"]
        
        # Pivot Points (Swing High/Low)
        df["pivot_high"] = df["high"].rolling(window=self.pivot_period * 2 + 1, center=True).max()
        df["pivot_low"] = df["low"].rolling(window=self.pivot_period * 2 + 1, center=True).min()
        
        # Isi nilai NaN yang mungkin muncul di awal data
        df.bfill(inplace=True)
        df.ffill(inplace=True)
        
        return df

    async def _calculate_dynamic_sr(
        self, df: pd.DataFrame
    ) -> Dict[str, Optional[float]]:
        """Menghitung level Support dan Resistance dinamis dari pivot points."""
        recent_pivots = df.tail(100) # Melihat 100 candle terakhir untuk S/R
        recent_highs = recent_pivots["pivot_high"].dropna().unique()
        recent_lows = recent_pivots["pivot_low"].dropna().unique()
        current_price = df.iloc[-1]["close"]

        resistance = min([p for p in recent_highs if p > current_price], default=None)
        support = max([p for p in recent_lows if p < current_price], default=None)
        
        return {"support": support, "resistance": resistance}

    async def _generate_signal(
        self,
        symbol: str,
        current_data: pd.Series,
        previous_data: pd.Series,
        sr_levels: Dict[str, Optional[float]],
        higher_timeframe_trend: TrendDirection,
    ) -> Optional[TradingSignal]:
        """Menghasilkan sinyal trading awal berdasarkan crossover SuperTrend dan konfirmasi tren."""
        
        current_price = current_data["close"]
        current_trend_val = current_data["supertrend_direction"]
        prev_trend_val = previous_data["supertrend_direction"]
        primary_trend = TrendDirection.BULLISH if current_trend_val == 1 else TrendDirection.BEARISH
        
        signal_type = None
        # Crossover BUY
        if current_trend_val == 1 and prev_trend_val == -1:
            if higher_timeframe_trend == TrendDirection.BULLISH:
                signal_type = SignalType.BUY
            else:
                self.logger.info(f"Sinyal BUY untuk {symbol} diabaikan karena konflik dengan tren 4 jam ({higher_timeframe_trend.name}).")

        # Crossover SELL
        elif current_trend_val == -1 and prev_trend_val == 1:
            if higher_timeframe_trend == TrendDirection.BEARISH:
                signal_type = SignalType.SELL
            else:
                 self.logger.info(f"Sinyal SELL untuk {symbol} diabaikan karena konflik dengan tren 4 jam ({higher_timeframe_trend.name}).")
        
        if not signal_type:
            return None

        # Kalkulasi Manajemen Risiko
        risk_reward_ratio = 2.0
        stop_loss = current_data["supertrend"]
        risk = abs(current_price - stop_loss)
        
        take_profit = 0.0
        if signal_type == SignalType.BUY:
            potential_tp = current_price + (risk * risk_reward_ratio)
            # TP disesuaikan dengan resistance terdekat jika lebih konservatif
            if sr_levels["resistance"] and sr_levels["resistance"] > current_price:
                 take_profit = min(potential_tp, sr_levels["resistance"])
            else:
                 take_profit = potential_tp
        else: # SELL
            potential_tp = current_price - (risk * risk_reward_ratio)
            # TP disesuaikan dengan support terdekat jika lebih konservatif
            if sr_levels["support"] and sr_levels["support"] < current_price:
                take_profit = max(potential_tp, sr_levels["support"])
            else:
                take_profit = potential_tp
        
        self.logger.info(f"Sinyal {signal_type.value} terkonfirmasi untuk {symbol} pada harga {current_price:.4f}")

        return TradingSignal(
            symbol=symbol, signal_type=signal_type, timestamp=current_data.name.to_pydatetime(),
            price=current_price, supertrend_value=current_data["supertrend"], trend_direction=primary_trend,
            entry_price=current_price, stop_loss=stop_loss, take_profit=take_profit,
            support_level=sr_levels["support"], resistance_level=sr_levels["resistance"],
            timeframe="1h/4h"
        )

    async def analyze_market(
        self,
        symbol: str,
        primary_market_data: List[MarketData],
        higher_market_data: List[MarketData],
    ) -> AnalysisResult:
        """Melakukan analisis pasar lengkap dan mengemas semua data indikator."""
        start_time = pd.Timestamp.now()
        
        try:
            # 1. Proses Timeframe Tinggi (4h) untuk menentukan tren utama
            df_higher = self._market_data_to_dataframe(higher_market_data)
            df_higher = await self._calculate_indicators(df_higher)
            higher_trend_val = df_higher.iloc[-1]["supertrend_direction"]
            higher_timeframe_trend = TrendDirection.BULLISH if higher_trend_val == 1 else TrendDirection.BEARISH

            # 2. Proses Timeframe Utama (1h) untuk sinyal dan data AI
            df_primary = self._market_data_to_dataframe(primary_market_data)
            df_primary = await self._calculate_indicators(df_primary)
            
            sr_levels = await self._calculate_dynamic_sr(df_primary)

            latest_data = df_primary.iloc[-1]
            previous_data = df_primary.iloc[-2]

            # 3. Hasilkan sinyal awal (pre-AI confirmation)
            signal = await self._generate_signal(
                symbol, latest_data, previous_data, sr_levels, higher_timeframe_trend
            )
            
            # 4. Kemas semua data indikator untuk diserahkan ke AI
            indicator_data = IndicatorData(
                symbol=symbol, timestamp=latest_data.name.to_pydatetime(),
                supertrend=latest_data.get("supertrend"),
                trend_direction=TrendDirection.BULLISH if latest_data.get("supertrend_direction") == 1 else TrendDirection.BEARISH,
                support_level=sr_levels["support"],
                resistance_level=sr_levels["resistance"],
                rsi=latest_data.get("rsi"),
                macd_line=latest_data.get("macd_line"),
                macd_signal=latest_data.get("macd_signal")
            )

        except Exception as e:
            self.logger.error(f"Error saat analisis teknikal untuk {symbol}: {e}", exc_info=True)
            return None

        return AnalysisResult(
            symbol=symbol, timeframe="1h/4h", timestamp=pd.Timestamp.now(tz='UTC'),
            market_data=primary_market_data[-1], indicator_data=indicator_data,
            signal=signal, higher_tf_trend=higher_timeframe_trend,
            analysis_duration_ms=(pd.Timestamp.now() - start_time).total_seconds() * 1000,
        )

