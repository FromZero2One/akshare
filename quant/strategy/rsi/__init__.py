"""
RSI 策略模块

公开 API:
    RsiCross / RsiCrossEnhanced: 策略类
    strategy_back_trader: 回测入口（参照 SmaStrategyScript 风格）

向量化版本（vectorized_rsi）保留为快速批量回测用途，与事件循环版行为一致。
"""
from quant.strategy.rsi.RsiStrategyScript import strategy_back_trader
from quant.strategy.rsi.strategy.RsiCross import RsiCross
from quant.strategy.rsi.strategy.RsiCrossEnhanced import RsiCrossEnhanced

__all__ = ['RsiCross', 'RsiCrossEnhanced', 'strategy_back_trader']
