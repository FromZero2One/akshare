#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2026/6/5
Desc: 双均线策略回测系统 v2.0 - 主入口

功能：
  1. 完整的功能测试
  2. 使用示例演示
  3. 可直接运行回测

使用方式：
  # 运行测试
  python main.py
  
  # 在代码中导入使用
  from quant.strategy.sma.data_fetch.main import run_backtest
  run_backtest(symbols=['601398', '600519'], parallel=True)
"""

import os
import sys

# 将项目根目录添加到Python路径（v2_refactor的父目录的父目录）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from quant.data_fetch.stock_data_provider import StockDataProvider
from quant.data_fetch.backtest_executor import BacktestExecutor
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)



def main():

    backtrader_symbols = ['601399']

    provider = StockDataProvider(adjust="qfq")
    executor = BacktestExecutor(re_run_result=True)
    backtrader_name_list = provider.get_stock_name_list(symbols=backtrader_symbols)

    # 将 DataFrame 转换为字典列表
    backtrader_name_list = backtrader_name_list.to_dict('records')

    for backtrader_name in backtrader_name_list:
        # 获取历史数据
        history_df = provider.get_history_data(
            symbol=backtrader_name['symbol'],
            stock_name=backtrader_name['stock_name'],
            min_days=100
        )
        
        if history_df is None:
            logger.warning(f"⊘ 跳过 {backtrader_name['symbol']}[{backtrader_name['stock_name']}]：数据不足")
            continue
        
        # 执行单只回测
        result = executor.execute_single(
            backtrader_name['symbol'], 
            backtrader_name['stock_name'], 
            history_df
        )
        logger.info(f"✓ 回测结果: {result}")




if __name__ == '__main__':
    main()
