#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2026/5/29
Desc: 简化版测试脚本 - 直接从akshare获取数据进行回测测试
"""

import logging
import pandas as pd
from datetime import datetime
import akshare as ak
from quant.strategy.sma.strategy.SmaCross import SmaCross
from quant.strategy.sma.SmaStrategyScript import strategy_back_trader

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_single_stock_backtest(symbol: str = "601398", stock_name: str = "工商银行"):
    """
    测试单只股票的回测
    
    Args:
        symbol: 股票代码
        stock_name: 股票名称
    """
    logger.info(f"开始测试股票 {symbol}[{stock_name}]")
    
    try:
        # 从akshare直接获取数据
        logger.info(f"从akshare获取股票 {symbol} 的历史数据...")
        df = ak.stock_zh_a_hist(symbol=symbol, period="daily", adjust="qfq")
        
        if df.empty:
            logger.warning(f"股票 {symbol} 没有获取到数据")
            return False
        
        logger.info(f"成功获取 {len(df)} 条历史数据")
        logger.info(f"数据日期范围: {df['日期'].min()} 至 {df['日期'].max()}")
        
        # 准备数据格式（与数据库查询结果保持一致）
        tb_df = df[['日期', '开盘', '收盘', '最高', '最低', '成交量']].copy()
        tb_df.columns = ['date', 'open', 'close', 'high', 'low', 'volume']
        
        # 执行回测
        logger.info("开始执行双均线策略回测...")
        strategy_back_trader(
            symbol=symbol,
            stock_name=stock_name,
            adjust="qfq",
            tb_df=tb_df,
            fromdate=datetime(2023, 1, 1),
            todate=datetime.now(),
            startcash=100000,
            commission=0.0005,
            strategy=SmaCross,
            printlog=False,
            is_plot=False,
            is_save_result=True
        )
        
        logger.info(f"✅ 股票 {symbol} 回测完成")
        return True
        
    except Exception as e:
        logger.error(f"❌ 股票 {symbol} 回测失败: {e}", exc_info=True)
        return False


def test_multiple_stocks():
    """
    测试多只股票的回测
    """
    # 测试股票列表
    test_stocks = [
        ("601398", "工商银行"),
        ("600519", "贵州茅台"),
        ("000001", "平安银行"),
    ]
    
    results = []
    for symbol, name in test_stocks:
        logger.info("="*60)
        success = test_single_stock_backtest(symbol, name)
        results.append((symbol, name, success))
        logger.info("="*60)
    
    # 打印测试结果汇总
    logger.info("\n" + "="*60)
    logger.info("测试结果汇总:")
    logger.info("="*60)
    for symbol, name, success in results:
        status = "✅ 成功" if success else "❌ 失败"
        logger.info(f"{symbol}[{name}]: {status}")
    
    success_count = sum(1 for _, _, s in results if s)
    logger.info(f"\n总计: {success_count}/{len(results)} 只股票回测成功")


if __name__ == '__main__':
    logger.info("="*60)
    logger.info("开始测试双均线策略回测脚本")
    logger.info("="*60)
    
    # 测试单只股票
    # test_single_stock_backtest("601398", "工商银行")
    
    # 测试多只股票
    test_multiple_stocks()
    
    logger.info("="*60)
    logger.info("测试完成")
    logger.info("="*60)
