"""
个人量化回测系统

功能模块：
- strategy: 交易策略（SMA/RSI/布林线/TA-Lib）
- entity:   数据库 ORM 实体
- utils:    工具集（数据库、缓存、日志、可视化等）
"""

from quant.strategy.sma import sma_cross_test
from quant.strategy import BaseStrategy

__all__ = [
    "BaseStrategy",
    "sma_cross_test",
]
