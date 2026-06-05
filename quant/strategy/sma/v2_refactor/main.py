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
  from quant.strategy.sma.v2_refactor.main import run_backtest
  run_backtest(symbols=['601398', '600519'], parallel=True)
"""

import sys
import os

# 将项目根目录添加到Python路径（v2_refactor的父目录的父目录）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from quant.strategy.sma.v2_refactor.stock_data_provider import StockDataProvider
from quant.strategy.sma.v2_refactor.backtest_executor import BacktestExecutor
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_data_provider():
    """测试数据提供者"""
    logger.info("=" * 60)
    logger.info("测试1: StockDataProvider")
    logger.info("=" * 60)
    

    # 初始化
    provider = StockDataProvider(adjust="qfq")
    logger.info("✓ 数据提供者初始化成功")
    
    # 获取股票列表
    df_all = provider.get_stock_list()
    logger.info(f"✓ 获取全部股票列表: {len(df_all)} 只")
    
    # 获取指定股票
    df_selected = provider.get_stock_list(symbols=['601398', '600519'])
    logger.info(f"✓ 获取指定股票列表: {len(df_selected)} 只")
    
    # 获取历史数据（自动确保完整）
    df_hist = provider.get_history_data('601398', '工商银行', min_days=100)
    if df_hist is not None:
        logger.info(f"✓ 获取历史数据: {len(df_hist)} 天")
    else:
        logger.warning("⚠ 历史数据为空或不足")
    
    logger.info("✅ 数据提供者测试通过\n")
    return provider


def test_executor_single(provider):
    """测试单只股票回测"""
    logger.info("=" * 60)
    logger.info("测试2: BacktestExecutor (单只股票)")
    logger.info("=" * 60)

    # 初始化执行器
    executor = BacktestExecutor(re_run_result=False)
    logger.info("✓ 回测执行器初始化成功")

    # 获取测试数据
    df = provider.get_history_data('601398', min_days=100)
    if df is None:
        logger.error("✗ 无法获取测试数据，跳过单只回测测试")
        return executor

    # 执行单只回测
    result = executor.execute_single('601398', '工商银行', df)
    logger.info(f"✓ 回测结果: {result}")

    if result['success']:
        logger.info(f"  - 收益率: {result['result']['returns_pct']:.2f}%")
        logger.info(f"  - 耗时: {result['duration_ms']:.2f}ms")

    logger.info("✅ 单只股票回测测试通过\n")
    return executor



def run_backtest(
    symbols=None,
    adjust='qfq',
    re_run_result=False,
    parallel=False,
    max_workers=None
):
    """
    运行回测（便捷函数）
    
    Args:
        symbols: 股票代码列表，None则全部
        adjust: 复权类型
        re_run_result: 是否重新回测
        parallel: 是否并行
        max_workers: 线程数
    """
    logger.info("=" * 60)
    logger.info("启动双均线策略回测 v2.0")
    logger.info("=" * 60)
    
    # 初始化
    provider = StockDataProvider(adjust=adjust)
    executor = BacktestExecutor(re_run_result=re_run_result)
    
    # 获取股票列表
    stock_list = provider.get_stock_list(symbols=symbols)
    if stock_list.empty:
        logger.warning("没有可回测的股票")
        return
    
    logger.info(f"待回测股票数: {len(stock_list)}")
    
    # 执行回测
    if parallel:
        results = executor.execute_batch_parallel(
            stock_list=stock_list,
            data_provider=provider,
            max_workers=max_workers
        )
    else:
        results = executor.execute_batch_serial(
            stock_list=stock_list,
            data_provider=provider
        )
    
    logger.info("回测完成")
    return results


def main():

    try:
        # ========== 测试部分 ==========
        logger.info("📋 开始功能测试\n")
        
        # 测试1: 数据提供者
        provider = test_data_provider()

        # 测试2: 单只股票回测
        test_executor_single(provider)
        


    except Exception as e:
        logger.error(f"✗ 测试失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
