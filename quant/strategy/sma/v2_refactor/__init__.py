#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2026/6/5
Desc: 回测系统 v2.0

使用方式：
  from quant.strategy.sma.v2_refactor import run_backtest
  run_backtest(symbols=['601398'], parallel=True)
"""

from .main import run_backtest
from .stock_data_provider import StockDataProvider
from .backtest_executor import BacktestExecutor

__all__ = ['run_backtest', 'StockDataProvider', 'BacktestExecutor']
