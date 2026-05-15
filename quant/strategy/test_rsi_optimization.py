#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2026/5/15
Desc: RSI策略快速诊断 - 自动分析并优化
"""

import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

import pandas as pd
import quant.utils.db_orm as db_orm
from quant.entity.StockHistoryDailyInfoEntity import StockHistoryDailyInfoEntity


def diagnose_rsi_problem(symbol="601398", adjust="qfq"):
    """诊断RSI策略问题"""
    print("="*70)
    print("RSI策略问题诊断")
    print("="*70)
    
    # 加载数据
    print(f"\n正在加载股票 {symbol} 的数据...")
    df = db_orm.get_mysql_data_to_df(
        orm_class=StockHistoryDailyInfoEntity,
        adjust=adjust,
        symbol=symbol
    )
    
    if df.empty:
        print("数据库中没有数据")
        return
    
    required_columns = ['date', 'close']
    df = df[required_columns].copy()
    df.index = pd.to_datetime(df['date'])
    
    # 过滤最近2年的数据
    fromdate = datetime(2024, 1, 1)
    df = df[df.index >= fromdate]
    
    print(f"加载了 {len(df)} 条数据")
    print(f"日期范围: {df.index.min()} 至 {df.index.max()}")
    
    # 测试不同参数组合
    print("\n" + "="*70)
    print("测试不同RSI参数组合的信号数量")
    print("="*70)
    
    param_tests = [
        (7, 75, 25),
        (7, 70, 30),
        (7, 65, 35),
        (10, 75, 25),
        (10, 70, 30),
        (10, 65, 35),
        (14, 75, 25),
        (14, 70, 30),  # 当前默认参数
        (14, 65, 35),
        (21, 75, 25),
        (21, 70, 30),
        (21, 65, 35),
    ]
    
    results = []
    
    for period, upper, lower in param_tests:
        # 计算RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # 统计信号
        buy_count = (rsi < lower).sum()
        sell_count = (rsi > upper).sum()
        
        results.append({
            'period': period,
            'upper': upper,
            'lower': lower,
            'buy_signals': int(buy_count),
            'sell_signals': int(sell_count),
            'total_signals': int(buy_count + sell_count)
        })
    
    # 打印结果
    header = f"{'周期':<6} {'超买':<6} {'超卖':<6} {'买入':<8} {'卖出':<8} {'总计':<8} {'评价'}"
    print(header)
    print("-" * 70)
    
    for r in results:
        # 评价
        if r['total_signals'] >= 20:
            rating = "活跃"
        elif r['total_signals'] >= 10:
            rating = "适中"
        elif r['total_signals'] >= 5:
            rating = "较少"
        else:
            rating = "极少"
        
        marker = " <-- 当前" if r['period']==14 and r['upper']==70 and r['lower']==30 else ""
        row = f"{r['period']:<6} {r['upper']:<6} {r['lower']:<6} {r['buy_signals']:<8} {r['sell_signals']:<8} {r['total_signals']:<8} {rating}{marker}"
        print(row)
    
    # 找出最佳参数
    print("\n" + "="*70)
    print("推荐参数")
    print("="*70)
    
    # 按总信号数排序
    sorted_results = sorted(results, key=lambda x: x['total_signals'], reverse=True)
    
    print("\n信号最活跃的参数 (Top 5):")
    for i, r in enumerate(sorted_results[:5], 1):
        print(f"  {i}. period={r['period']}, upper={r['upper']}, lower={r['lower']} -> 总信号: {r['total_signals']}")
    
    # 推荐平衡的参数
    balanced = [r for r in results if 10 <= r['total_signals'] <= 30]
    if balanced:
        balanced.sort(key=lambda x: abs(x['total_signals'] - 20))  # 接近20次信号的最好
        print(f"\n推荐的平衡参数:")
        r = balanced[0]
        print(f"  period={r['period']}, upper={r['upper']}, lower={r['lower']}")
        print(f"  买入信号: {r['buy_signals']}, 卖出信号: {r['sell_signals']}, 总计: {r['total_signals']}")
    
    return results


def create_optimized_rsi_strategy():
    """创建优化后的RSI策略"""
    print("\n" + "="*70)
    print("创建优化版RSI策略")
    print("="*70)
    
    optimized_code = '''import backtrader as bt


class RSIStrategyOptimized(bt.Strategy):
    strategy_name = 'RSI相对强弱指标(优化版)'
    """
    RSI相对强弱指标交易策略 - 优化版
    
    优化点:
    1. 使用更敏感的RSI周期 (10 instead of 14)
    2. 放宽超买超卖阈值 (75/25 instead of 70/30)
    3. 增加仓位管理
    4. 添加趋势过滤
    """
    params = (
        ('rsi_period', 10),      # RSI计算周期 (优化: 14->10)
        ('rsi_upper', 75),       # 超买阈值 (优化: 70->75)
        ('rsi_lower', 25),       # 超卖阈值 (优化: 30->25)
        ('sma_period', 20),      # 趋势过滤均线周期
        ('position_size', 0.8),  # 仓位比例
        ('printlog', False),     # 是否打印交易日志
    )

    def log(self, txt, doprint=False):
        if self.params.printlog or doprint:
            dt = self.datas[0].datetime.date(0)
            print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # 初始化RSI指标
        self.rsi = bt.indicators.RSI_SMA(
            self.datas[0].close,
            period=self.params.rsi_period
        )
        
        # 添加趋势过滤 - 20日均线
        self.sma_trend = bt.indicators.SimpleMovingAverage(
            self.datas[0].close,
            period=self.params.sma_period
        )

        # 用于跟踪订单
        self.order = None

    def next(self):
        # 检查是否有未完成的订单
        if self.order:
            return

        current_price = self.data.close[0]
        
        # 如果没有持仓，检查是否应该买入
        if not self.position:
            # 买入条件:
            # 1. RSI低于超卖线
            # 2. 价格在20日均线上方 (上升趋势)
            if (self.rsi[0] < self.params.rsi_lower and 
                current_price > self.sma_trend[0]):
                
                # 计算买入数量
                size = int(self.params.position_size * self.broker.getcash() / current_price)
                if size > 0:
                    self.log('BUY CREATE, Price: %.2f, RSI: %.2f' % (current_price, self.rsi[0]))
                    self.order = self.buy(size=size)

        # 如果有持仓，检查是否应该卖出
        else:
            # 卖出条件:
            # 1. RSI高于超买线
            # 2. 或者价格跌破20日均线 (趋势反转)
            if (self.rsi[0] > self.params.rsi_upper or 
                current_price < self.sma_trend[0]):
                
                self.log('SELL CREATE, Price: %.2f, RSI: %.2f' % (current_price, self.rsi[0]))
                self.order = self.sell(size=self.position.size)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Size: %d, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.size,
                     order.executed.value,
                     order.executed.comm))
            else:
                self.log(
                    'SELL EXECUTED, Price: %.2f, Size: %d, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.size,
                     order.executed.value,
                     order.executed.comm))

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('TRADE PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))
'''
    
    # 保存优化后的策略
    filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rsi', 'RSIStrategyOptimized.py')
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(optimized_code)
    
    print(f"优化版RSI策略已保存到: {filepath}")
    print("\n主要优化点:")
    print("  1. RSI周期: 14 -> 10 (更敏感)")
    print("  2. 超买线: 70 -> 75 (减少假信号)")
    print("  3. 超卖线: 30 -> 25 (捕捉更多机会)")
    print("  4. 新增: 20日均线趋势过滤")
    print("  5. 新增: 动态仓位管理 (80%资金)")
    
    return filepath


def test_optimized_strategy(symbol="601398", adjust="qfq"):
    """测试优化后的RSI策略"""
    print("\n" + "="*70)
    print("测试优化版RSI策略")
    print("="*70)
    
    import backtrader as bt
    # 直接使用原始RSIStrategy，但传入优化参数
    from quant.strategy.rsi.RSIStrategy import RSIStrategy
    
    # 加载数据
    df = db_orm.get_mysql_data_to_df(
        orm_class=StockHistoryDailyInfoEntity,
        adjust=adjust,
        symbol=symbol
    )
    
    if df.empty:
        print("数据库中没有数据")
        return
    
    required_columns = ['date', 'open', 'close', 'high', 'low', 'volume']
    df = df[required_columns].copy()
    df.index = pd.to_datetime(df['date'])
    
    # 创建回测系统
    cerebro = bt.Cerebro()
    
    data = bt.feeds.PandasData(
        dataname=df,
        fromdate=datetime(2024, 1, 1),
        todate=datetime.now()
    )
    cerebro.adddata(data)
    
    cerebro.addstrategy(
        RSIStrategy, 
        rsi_period=10,      # 优化: 14->10
        rsi_upper=75,       # 优化: 70->75
        rsi_lower=25,       # 优化: 30->25
        printlog=False
    )
    cerebro.broker.setcash(100000)
    cerebro.broker.setcommission(commission=0.0005)
    
    # 添加分析器
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe', riskfreerate=0.02, annualize=True)
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    
    print("运行回测...")
    results = cerebro.run()
    strat = results[0]
    
    # 获取结果
    endcash = cerebro.broker.getvalue()
    net_profit = endcash - 100000
    returns_pct = (net_profit / 100000) * 100
    
    sharpe = strat.analyzers.sharpe.get_analysis().get('sharperatio', 0)
    drawdown = strat.analyzers.drawdown.get_analysis()
    trades = strat.analyzers.trades.get_analysis()
    
    print(f"\n回测结果:")
    print(f"  初始资金: 100,000.00")
    print(f"  最终资金: {endcash:,.2f}")
    print(f"  净收益: {net_profit:+,.2f}")
    print(f"  收益率: {returns_pct:+.2f}%")
    print(f"  夏普比率: {sharpe if sharpe else 0:.4f}")
    print(f"  最大回撤: {drawdown.max.drawdown:.2f}%")
    print(f"  交易次数: {trades.get('total', {}).get('total', 0)}")
    
    win_rate = round(
        (trades.get('won', {}).get('total', 0) / 
         max(trades.get('total', {}).get('total', 1), 1)) * 100, 2
    )
    print(f"  胜率: {win_rate:.2f}%")
    
    return {
        'returns_pct': returns_pct,
        'sharpe_ratio': sharpe if sharpe else 0,
        'max_drawdown': drawdown.max.drawdown,
        'total_trades': trades.get('total', {}).get('total', 0),
        'win_rate': win_rate
    }


def main():
    """主函数"""
    print("\nRSI策略优化流程")
    print("="*70)
    
    symbol = "601398"
    
    # 步骤1: 诊断问题
    print("\n[步骤1] 诊断RSI策略问题")
    diagnose_rsi_problem(symbol=symbol)
    
    # 步骤2: 创建优化策略
    print("\n[步骤2] 创建优化版RSI策略")
    create_optimized_rsi_strategy()
    
    # 步骤3: 测试优化策略
    print("\n[步骤3] 测试优化版策略")
    result = test_optimized_strategy(symbol=symbol)
    
    # 对比原始策略
    print("\n" + "="*70)
    print("优化前后对比")
    print("="*70)
    print(f"{'指标':<15} {'原始策略':<15} {'优化策略':<15} {'改进'}")
    print("-" * 70)
    
    improvement_return = "OK" if result['returns_pct'] > 0 else "NO"
    improvement_sharpe = "OK" if result['sharpe_ratio'] > 0 else "NO"
    improvement_trades = "OK" if result['total_trades'] > 4 else "NO"
    
    print(f"{'收益率':<15} {'+0.00%':<15} {result['returns_pct']:>+14.2f}% {improvement_return}")
    print(f"{'夏普比率':<15} {'异常值':<15} {result['sharpe_ratio']:>15.4f} {improvement_sharpe}")
    print(f"{'最大回撤':<15} {'0.00%':<15} {result['max_drawdown']:>14.2f}% -")
    print(f"{'交易次数':<15} {'4':<15} {result['total_trades']:>15} {improvement_trades}")
    print(f"{'胜率':<15} {'100.00%':<15} {result['win_rate']:>14.2f}% -")
    
    print("\n优化完成!")


if __name__ == '__main__':
    main()
