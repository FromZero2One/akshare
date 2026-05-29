#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2026/5/29
Desc: 离线测试脚本 - 使用模拟数据测试回测逻辑
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_mock_stock_data(symbol: str = "601398", days: int = 500) -> pd.DataFrame:
    """
    生成模拟股票数据用于测试
    
    Args:
        symbol: 股票代码
        days: 天数
        
    Returns:
        pd.DataFrame: 模拟的股票历史数据
    """
    logger.info(f"生成 {symbol} 的模拟数据 ({days}天)...")
    
    # 生成日期序列
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    dates = pd.date_range(start=start_date, end=end_date, freq='B')  # 工作日
    
    # 生成随机价格数据（模拟股票走势）
    np.random.seed(42)  # 固定种子以便复现
    base_price = 10.0
    prices = []
    current_price = base_price
    
    for _ in range(len(dates)):
        # 随机涨跌 (-3% 到 +3%)
        change = np.random.uniform(-0.03, 0.03)
        current_price = current_price * (1 + change)
        prices.append(current_price)
    
    # 创建DataFrame
    df = pd.DataFrame({
        'date': dates,
        'open': [p * (1 + np.random.uniform(-0.01, 0.01)) for p in prices],
        'close': prices,
        'high': [p * (1 + abs(np.random.uniform(0, 0.02))) for p in prices],
        'low': [p * (1 - abs(np.random.uniform(0, 0.02))) for p in prices],
        'volume': np.random.randint(1000000, 10000000, len(dates)),
    })
    
    logger.info(f"✅ 成功生成 {len(df)} 条模拟数据")
    logger.info(f"数据日期范围: {df['date'].min().strftime('%Y-%m-%d')} 至 {df['date'].max().strftime('%Y-%m-%d')}")
    logger.info(f"价格范围: {df['close'].min():.2f} - {df['close'].max():.2f}")
    
    return df


def test_strategy_logic():
    """
    测试策略核心逻辑（不依赖网络和数据库）
    """
    logger.info("="*60)
    logger.info("开始测试双均线策略逻辑")
    logger.info("="*60)
    
    try:
        # 1. 生成模拟数据
        mock_data = generate_mock_stock_data(symbol="601398", days=500)
        
        # 2. 导入backtrader和策略
        import backtrader as bt
        from quant.strategy.sma.strategy.SmaCross import SmaCross
        from quant.utils.sizer import DynamicSizer
        
        logger.info("\n初始化Backtrader回测引擎...")
        
        # 3. 设置数据源
        mock_data.index = pd.to_datetime(mock_data['date'])
        data = bt.feeds.PandasData(
            dataname=mock_data,
            fromdate=datetime(2024, 1, 1),
            todate=datetime.now()
        )
        
        # 4. 创建Cerebro引擎
        cerebro = bt.Cerebro()
        cerebro.adddata(data)
        cerebro.addstrategy(SmaCross, printlog=False)
        
        # 5. 设置初始资金和手续费
        startcash = 100000
        cerebro.broker.setcommission(commission=0.0005)
        cerebro.broker.setcash(startcash)
        
        # 6. 添加动态仓位管理器
        cerebro.addsizer(DynamicSizer, position_pct=0.8)
        
        # 7. 添加观察器
        cerebro.addobserver(bt.observers.Value)
        
        logger.info(f"初始资金: {startcash:.2f}")
        logger.info("开始回测...\n")
        
        # 8. 运行回测
        results = cerebro.run()
        endcash = cerebro.broker.getvalue()
        net_profit = endcash - startcash
        returns_pct = (net_profit / startcash) * 100
        
        # 9. 输出结果
        logger.info("="*60)
        logger.info("回测结果:")
        logger.info("="*60)
        logger.info(f"策略名称: {SmaCross.strategy_name}")
        logger.info(f"初始资金: {startcash:.2f}")
        logger.info(f"最终资金: {endcash:.2f}")
        logger.info(f"净收益: {net_profit:.2f}")
        logger.info(f"收益率: {returns_pct:.2f}%")
        logger.info("="*60)
        
        # 10. 获取交易统计
        strat = results[0]
        trades = strat.broker.get_trades_history()
        logger.info(f"\n总交易次数: {len(trades)}")
        
        if trades:
            winning_trades = [t for t in trades if t.pnl > 0]
            losing_trades = [t for t in trades if t.pnl < 0]
            
            logger.info(f"盈利交易: {len(winning_trades)}")
            logger.info(f"亏损交易: {len(losing_trades)}")
            
            if trades:
                win_rate = len(winning_trades) / len(trades) * 100
                logger.info(f"胜率: {win_rate:.2f}%")
                
                avg_profit = sum(t.pnl for t in winning_trades) / len(winning_trades) if winning_trades else 0
                avg_loss = sum(t.pnl for t in losing_trades) / len(losing_trades) if losing_trades else 0
                logger.info(f"平均盈利: {avg_profit:.2f}")
                logger.info(f"平均亏损: {avg_loss:.2f}")
        
        logger.info("\n✅ 策略逻辑测试成功！")
        return True
        
    except Exception as e:
        logger.error(f"❌ 策略测试失败: {e}", exc_info=True)
        return False


if __name__ == '__main__':
    success = test_strategy_logic()
    
    if success:
        logger.info("\n" + "="*60)
        logger.info("🎉 所有测试通过！")
        logger.info("="*60)
    else:
        logger.error("\n" + "="*60)
        logger.error("⚠️  测试失败，请检查错误信息")
        logger.error("="*60)
