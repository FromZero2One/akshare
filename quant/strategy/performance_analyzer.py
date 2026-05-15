#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2026/5/15
Desc: 回测性能分析器 - 计算夏普比率、最大回撤等专业指标
"""

import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

import backtrader as bt
import pandas as pd
import quant.utils.db_orm as db_orm
from quant.entity.StockHistoryDailyInfoEntity import StockHistoryDailyInfoEntity


class PerformanceAnalyzer:
    """回测性能分析器"""
    
    def __init__(self, symbol="601398", adjust="qfq",
                 fromdate=datetime(2024, 1, 1),
                 todate=datetime.now(),
                 startcash=100000,
                 commission=0.0005):
        self.symbol = symbol
        self.adjust = adjust
        self.fromdate = fromdate
        self.todate = todate
        self.startcash = startcash
        self.commission = commission
        self.data = None
        
    def load_data(self):
        """加载股票数据"""
        print(f"[DATA] 正在加载股票 {self.symbol} 的数据...")
        try:
            df = db_orm.get_mysql_data_to_df(
                orm_class=StockHistoryDailyInfoEntity,
                adjust=self.adjust,
                symbol=self.symbol
            )
            
            if df.empty:
                raise ValueError("数据库中没有数据")
            
            # 提取需要的列
            required_columns = ['date', 'open', 'close', 'high', 'low', 'volume']
            df = df[required_columns].copy()
            df.index = pd.to_datetime(df['date'])
            
            self.data = df
            print(f"[OK] 成功加载 {len(df)} 条数据")
            print(f"   日期范围: {df.index.min()} 至 {df.index.max()}")
            
        except Exception as e:
            print(f"[ERROR] 加载数据失败: {e}")
            raise
    
    def analyze_strategy(self, strategy_class, strategy_name, **strategy_params):
        """
        分析单个策略的性能
        
        Args:
            strategy_class: 策略类
            strategy_name: 策略名称
            **strategy_params: 策略参数
            
        Returns:
            dict: 性能指标字典
        """
        print(f"\n{'='*70}")
        print(f"分析策略: {strategy_name}")
        print(f"{'='*70}")
        
        # 创建回测系统
        cerebro = bt.Cerebro()
        
        data = bt.feeds.PandasData(
            dataname=self.data,
            fromdate=self.fromdate,
            todate=self.todate
        )
        cerebro.adddata(data)
        
        # 添加策略
        cerebro.addstrategy(strategy_class, **strategy_params)
        
        # 设置资金和手续费
        cerebro.broker.setcash(self.startcash)
        cerebro.broker.setcommission(commission=self.commission)
        
        # 添加性能分析器
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe', 
                           riskfreerate=0.02, annualize=True)
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
        cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
        cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name='annual_return')
        cerebro.addanalyzer(bt.analyzers.VWR, _name='vwr')  # 变异系数收益比
        
        # 运行回测
        print("[WAIT] 正在运行回测...")
        results = cerebro.run()
        strat = results[0]
        
        # 获取基本指标
        endcash = cerebro.broker.getvalue()
        net_profit = endcash - self.startcash
        returns_pct = (net_profit / self.startcash) * 100
        
        # 获取分析器结果
        sharpe_ratio = strat.analyzers.sharpe.get_analysis()
        drawdown = strat.analyzers.drawdown.get_analysis()
        trades = strat.analyzers.trades.get_analysis()
        returns = strat.analyzers.returns.get_analysis()
        vwr = strat.analyzers.vwr.get_analysis()
        
        # 提取关键指标
        performance = {
            'strategy_name': strategy_name,
            'symbol': self.symbol,
            'period': f"{self.fromdate.strftime('%Y-%m-%d')} 至 {self.todate.strftime('%Y-%m-%d')}",
            
            # 收益指标
            'initial_cash': self.startcash,
            'final_value': round(endcash, 2),
            'net_profit': round(net_profit, 2),
            'returns_pct': round(returns_pct, 2),
            
            # 风险指标
            'sharpe_ratio': round(sharpe_ratio.get('sharperatio', 0), 4),
            'max_drawdown_pct': round(drawdown.max.drawdown, 2),
            'max_drawdown_money': round(drawdown.max.moneydown, 2),
            'vwr': round(vwr.get('vwr', 0), 4),
            
            # 交易统计
            'total_trades': trades.get('total', {}).get('total', 0),
            'won_trades': trades.get('won', {}).get('total', 0),
            'lost_trades': trades.get('lost', {}).get('total', 0),
            'win_rate': round(
                (trades.get('won', {}).get('total', 0) / trades.get('total', {}).get('total', 1) * 100), 2
            ),
            
            # 盈亏统计
            'avg_profit': round(trades.get('pnl', {}).get('net', {}).get('average', 0), 2),
            'max_profit': round(trades.get('pnl', {}).get('net', {}).get('max', 0), 2),
            'max_loss': round(trades.get('pnl', {}).get('net', {}).get('min', 0), 2),
            
            # 年化收益
            'annual_returns': strat.analyzers.annual_return.get_analysis(),
        }
        
        # 打印详细报告
        self._print_performance_report(performance)
        
        return performance
    
    def _print_performance_report(self, perf):
        """打印性能报告"""
        print(f"\n{'='*70}")
        print(f"[DATA] {perf['strategy_name']} - 性能分析报告")
        print(f"{'='*70}")
        
        print(f"\n📈 基本信息:")
        print(f"   股票代码: {perf['symbol']}")
        print(f"   回测周期: {perf['period']}")
        
        print(f"\n[MONEY] 收益指标:")
        print(f"   初始资金:     ¥{perf['initial_cash']:,.2f}")
        print(f"   最终资金:     ¥{perf['final_value']:,.2f}")
        print(f"   净收益:       ¥{perf['net_profit']:+,.2f}")
        print(f"   收益率:       {perf['returns_pct']:+.2f}%")
        
        print(f"\n[RISK]  风险指标:")
        print(f"   夏普比率:     {perf['sharpe_ratio']:.4f}")
        print(f"   最大回撤:     {perf['max_drawdown_pct']:.2f}% (¥{perf['max_drawdown_money']:,.2f})")
        print(f"   VWR指标:      {perf['vwr']:.4f}")
        
        print(f"\n[DATA] 交易统计:")
        print(f"   总交易次数:   {perf['total_trades']}")
        print(f"   盈利次数:     {perf['won_trades']}")
        print(f"   亏损次数:     {perf['lost_trades']}")
        print(f"   胜率:         {perf['win_rate']:.2f}%")
        
        print(f"\n💵 盈亏分析:")
        print(f"   平均盈亏:     ¥{perf['avg_profit']:+,.2f}")
        print(f"   最大单笔盈利: ¥{perf['max_profit']:+,.2f}")
        print(f"   最大单笔亏损: ¥{perf['max_loss']:+,.2f}")
        
        # 评级
        rating = self._calculate_rating(perf)
        print(f"\n{'='*70}")
        print(f"[STAR] 综合评级: {rating}")
        print(f"{'='*70}")
    
    def _calculate_rating(self, perf):
        """计算策略评级"""
        score = 0
        
        # 收益率评分 (0-30分)
        if perf['returns_pct'] > 30:
            score += 30
        elif perf['returns_pct'] > 20:
            score += 25
        elif perf['returns_pct'] > 10:
            score += 20
        elif perf['returns_pct'] > 0:
            score += 15
        else:
            score += 5
        
        # 夏普比率评分 (0-25分)
        if perf['sharpe_ratio'] > 2:
            score += 25
        elif perf['sharpe_ratio'] > 1:
            score += 20
        elif perf['sharpe_ratio'] > 0.5:
            score += 15
        elif perf['sharpe_ratio'] > 0:
            score += 10
        else:
            score += 5
        
        # 最大回撤评分 (0-20分)
        if perf['max_drawdown_pct'] < 10:
            score += 20
        elif perf['max_drawdown_pct'] < 20:
            score += 15
        elif perf['max_drawdown_pct'] < 30:
            score += 10
        else:
            score += 5
        
        # 胜率评分 (0-15分)
        if perf['win_rate'] > 60:
            score += 15
        elif perf['win_rate'] > 50:
            score += 12
        elif perf['win_rate'] > 40:
            score += 8
        else:
            score += 5
        
        # 交易次数评分 (0-10分)
        if 10 <= perf['total_trades'] <= 100:
            score += 10
        elif perf['total_trades'] > 100:
            score += 8
        elif perf['total_trades'] > 0:
            score += 5
        else:
            score += 0
        
        # 根据分数给出评级
        if score >= 85:
            return "S级 (卓越)"
        elif score >= 70:
            return "A级 (优秀)"
        elif score >= 55:
            return "B级 (良好)"
        elif score >= 40:
            return "C级 (一般)"
        else:
            return "D级 (较差)"
    
    def compare_strategies(self, strategies_config):
        """
        对比多个策略的性能
        
        Args:
            strategies_config: 策略配置列表
                [
                    {
                        'class': StrategyClass,
                        'name': '策略名称',
                        'params': {...}
                    },
                    ...
                ]
        """
        print("\n" + "="*70)
        print("[COMPARE] 多策略性能对比分析")
        print("="*70)
        
        performances = []
        
        for config in strategies_config:
            try:
                perf = self.analyze_strategy(
                    config['class'],
                    config['name'],
                    **config.get('params', {})
                )
                performances.append(perf)
            except Exception as e:
                print(f"[ERROR] 策略 {config['name']} 分析失败: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        if not performances:
            print("[ERROR] 没有成功的策略分析结果")
            return
        
        # 打印对比表格
        self._print_comparison_table(performances)
        
        return performances
    
    def _print_comparison_table(self, performances):
        """打印策略对比表格"""
        print("\n" + "="*70)
        print("[DATA] 策略性能对比表")
        print("="*70)
        
        # 表头
        header = f"{'策略名称':<25} {'收益率':>8} {'夏普比率':>10} {'最大回撤':>10} {'胜率':>8} {'交易次数':>8} {'评级':<10}"
        print(header)
        print("-" * 70)
        
        # 按收益率排序
        performances.sort(key=lambda x: x['returns_pct'], reverse=True)
        
        for perf in performances:
            row = (
                f"{perf['strategy_name']:<25} "
                f"{perf['returns_pct']:>+7.2f}% "
                f"{perf['sharpe_ratio']:>10.4f} "
                f"{perf['max_drawdown_pct']:>9.2f}% "
                f"{perf['win_rate']:>7.2f}% "
                f"{perf['total_trades']:>8} "
                f"{self._calculate_rating(perf):<10}"
            )
            print(row)
        
        print("-" * 70)
        
        # 找出最佳策略
        best_by_return = max(performances, key=lambda x: x['returns_pct'])
        best_by_sharpe = max(performances, key=lambda x: x['sharpe_ratio'])
        best_by_winrate = max(performances, key=lambda x: x['win_rate'])
        lowest_drawdown = min(performances, key=lambda x: x['max_drawdown_pct'])
        
        print(f"\n[BEST] 各项最佳:")
        print(f"   最高收益率:   {best_by_return['strategy_name']} ({best_by_return['returns_pct']:+.2f}%)")
        print(f"   最佳夏普比率: {best_by_sharpe['strategy_name']} ({best_by_sharpe['sharpe_ratio']:.4f})")
        print(f"   最高胜率:     {best_by_winrate['strategy_name']} ({best_by_winrate['win_rate']:.2f}%)")
        print(f"   最小回撤:     {lowest_drawdown['strategy_name']} ({lowest_drawdown['max_drawdown_pct']:.2f}%)")


def main():
    """主函数 - 演示性能分析器"""
    print("\n" + "="*70)
    print("回测性能分析器")
    print("="*70)
    
    # 创建分析器
    analyzer = PerformanceAnalyzer(
        symbol="601398",
        adjust="qfq",
        fromdate=datetime(2024, 1, 1),
        todate=datetime.now(),
        startcash=100000,
        commission=0.0005
    )
    
    # 加载数据
    analyzer.load_data()
    
    # 导入策略
    from quant.strategy.sma.strategy.SmaCross import SmaCross
    from quant.strategy.boll.BollStrategy import BollStrategy
    from quant.strategy.rsi.RSIStrategy import RSIStrategy
    
    # 配置要分析的策略
    strategies = [
        {
            'class': SmaCross,
            'name': 'SMA双均线策略(优化版)',
            'params': {
                'pfast': 7,
                'pslow': 30,
                'stop_loss': 0.05,
                'take_profit': 0.15,
                'max': 0.8
            }
        },
        {
            'class': BollStrategy,
            'name': '布林线策略',
            'params': {}
        },
        {
            'class': RSIStrategy,
            'name': 'RSI策略',
            'params': {
                'rsi_period': 14,
                'rsi_upper': 70,
                'rsi_lower': 30
            }
        },
    ]
    
    # 执行对比分析
    analyzer.compare_strategies(strategies)


if __name__ == '__main__':
    main()
