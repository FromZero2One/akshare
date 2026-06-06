"""
数据获取与回测执行模块

包含从 akshare/数据库/缓存拉取股票数据，
并对单只或多只股票执行回测的核心组件。

提供：
  - StockDataProvider: 股票数据提供者（拉取+缓存+完整性检查）
  - BacktestExecutor: 回测执行器（向量化策略调度）
"""

from .stock_data_provider import StockDataProvider
from .backtest_executor import BacktestExecutor

__all__ = ['StockDataProvider', 'BacktestExecutor']
