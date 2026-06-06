"""
个人量化回测系统

功能模块：
- strategy: 交易策略（SMA/RSI/布林线/TA-Lib）
- entity:   数据库 ORM 实体
- utils:    工具集（数据库、缓存、日志、可视化等）
- data_fetch: 数据获取与回测执行（StockDataProvider + BacktestExecutor）

API 推荐：
  ★ 推荐：基于向量化回测
    from quant import StockDataProvider, BacktestExecutor
    provider = StockDataProvider(adjust='qfq')
    executor = BacktestExecutor()
    df = provider.get_history_data('601398', '工商银行')
    result = executor.execute_single('601398', '工商银行', df)

  ◇ 旧 API（保留）：基于 Backtrader 事件循环，支持完整可视化。
    from quant.strategy.sma.SmaStrategyScript import strategy_back_trader
    from quant.strategy.sma.strategy.SmaCross import SmaCross
    仍可通过完整模块路径访问，用于特殊场景（自定义指标、详细订单簿等）。
"""

from quant.data_fetch import StockDataProvider, BacktestExecutor
from quant.strategy import BaseStrategy

__all__ = [
    "BaseStrategy",
    "StockDataProvider",
    "BacktestExecutor",
]
