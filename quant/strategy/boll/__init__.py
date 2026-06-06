"""
BOLL 布林线策略模块

公开 API:
    BollCross: 策略类
    strategy_back_trader: 回测入口（参照 RsiStrategyScript 风格）

向量化版本（vectorized_boll）保留为快速批量回测用途，与事件循环版行为一致。
"""
from quant.strategy.boll.BollStrategyScript import strategy_back_trader
from quant.strategy.boll.strategy.BollCross import BollCross

__all__ = ['BollCross', 'strategy_back_trader']
