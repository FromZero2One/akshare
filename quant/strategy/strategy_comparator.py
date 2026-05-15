#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2026/5/15
Desc: 策略对比工具 - 可视化对比多个策略的性能
"""

import sys
import os
from datetime import datetime
from typing import List, Dict

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

import backtrader as bt
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
matplotlib.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

import quant.utils.db_orm as db_orm
from quant.entity.StockHistoryDailyInfoEntity import StockHistoryDailyInfoEntity


class StrategyComparator:
    """策略对比工具"""
    
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
        self.results = {}
        
    def load_data(self):
        """加载股票数据"""
        print(f"正在加载股票 {self.symbol} 的数据...")
        try:
            df = db_orm.get_mysql_data_to_df(
                orm_class=StockHistoryDailyInfoEntity,
                adjust=self.adjust,
                symbol=self.symbol
            )
            
            if df.empty:
                raise ValueError("数据库中没有数据")
            
            required_columns = ['date', 'open', 'close', 'high', 'low', 'volume']
            df = df[required_columns].copy()
            df.index = pd.to_datetime(df['date'])
            
            self.data = df
            print(f"成功加载 {len(df)} 条数据")
            print(f"日期范围: {df.index.min()} 至 {df.index.max()}")
            
        except Exception as e:
            print(f"加载数据失败: {e}")
            raise
    
    def run_strategy(self, strategy_class, strategy_name, **strategy_params):
        """运行单个策略并记录结果"""
        print(f"\n运行策略: {strategy_name}")
        
        cerebro = bt.Cerebro()
        
        data = bt.feeds.PandasData(
            dataname=self.data,
            fromdate=self.fromdate,
            todate=self.todate
        )
        cerebro.adddata(data)
        
        cerebro.addstrategy(strategy_class, **strategy_params)
        cerebro.broker.setcash(self.startcash)
        cerebro.broker.setcommission(commission=self.commission)
        
        # 添加观察器来记录每日资产价值
        cerebro.addobserver(bt.observers.Value)
        
        # 添加分析器
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe', 
                           riskfreerate=0.02, annualize=True)
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
        
        # 运行回测
        results = cerebro.run()
        strat = results[0]
        
        # 获取结果
        endcash = cerebro.broker.getvalue()
        net_profit = endcash - self.startcash
        returns_pct = (net_profit / self.startcash) * 100
        
        # 获取分析器结果
        sharpe_ratio = strat.analyzers.sharpe.get_analysis().get('sharperatio', 0)
        drawdown = strat.analyzers.drawdown.get_analysis()
        trades = strat.analyzers.trades.get_analysis()
        
        result = {
            'strategy_name': strategy_name,
            'endcash': endcash,
            'net_profit': net_profit,
            'returns_pct': returns_pct,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': drawdown.max.drawdown,
            'total_trades': trades.get('total', {}).get('total', 0),
            'win_rate': round(
                (trades.get('won', {}).get('total', 0) / 
                 max(trades.get('total', {}).get('total', 1), 1)) * 100, 2
            ),
        }
        
        self.results[strategy_name] = result
        print(f"  收益率: {returns_pct:+.2f}%")
        print(f"  夏普比率: {sharpe_ratio:.4f}")
        print(f"  最大回撤: {drawdown.max.drawdown:.2f}%")
        
        return result
    
    def compare_strategies(self, strategies_config):
        """
        对比多个策略
        
        Args:
            strategies_config: 策略配置列表
        """
        print("\n" + "="*70)
        print("开始策略对比分析")
        print("="*70)
        
        # 运行所有策略
        for config in strategies_config:
            try:
                self.run_strategy(
                    config['class'],
                    config['name'],
                    **config.get('params', {})
                )
            except Exception as e:
                print(f"策略 {config['name']} 运行失败: {e}")
                import traceback
                traceback.print_exc()
        
        if not self.results:
            print("没有成功的策略结果")
            return
        
        # 生成对比报告
        self._print_comparison_report()
        
        # 生成可视化图表
        self._plot_comparison()
        
        return self.results
    
    def _print_comparison_report(self):
        """打印对比报告"""
        print("\n" + "="*70)
        print("策略性能对比报告")
        print("="*70)
        
        # 按收益率排序
        sorted_results = sorted(
            self.results.values(), 
            key=lambda x: x['returns_pct'], 
            reverse=True
        )
        
        # 表头
        header = f"{'排名':<6} {'策略名称':<25} {'收益率':>10} {'夏普比率':>10} {'最大回撤':>10} {'胜率':>8} {'交易次数':>8}"
        print(header)
        print("-" * 70)
        
        for rank, result in enumerate(sorted_results, 1):
            row = (
                f"{rank:<6} "
                f"{result['strategy_name']:<25} "
                f"{result['returns_pct']:>+9.2f}% "
                f"{result['sharpe_ratio']:>10.4f} "
                f"{result['max_drawdown']:>9.2f}% "
                f"{result['win_rate']:>7.2f}% "
                f"{result['total_trades']:>8}"
            )
            print(row)
        
        print("-" * 70)
        
        # 详细分析
        print("\n详细分析:")
        print("="*70)
        
        best_return = max(self.results.values(), key=lambda x: x['returns_pct'])
        best_sharpe = max(self.results.values(), key=lambda x: x['sharpe_ratio'])
        lowest_dd = min(self.results.values(), key=lambda x: x['max_drawdown'])
        highest_winrate = max(self.results.values(), key=lambda x: x['win_rate'])
        
        print(f"最高收益率:   {best_return['strategy_name']} ({best_return['returns_pct']:+.2f}%)")
        print(f"最佳夏普比率: {best_sharpe['strategy_name']} ({best_sharpe['sharpe_ratio']:.4f})")
        print(f"最小回撤:     {lowest_dd['strategy_name']} ({lowest_dd['max_drawdown']:.2f}%)")
        print(f"最高胜率:     {highest_winrate['strategy_name']} ({highest_winrate['win_rate']:.2f}%)")
        
        # 综合评分
        print("\n综合评分:")
        print("-"*70)
        
        scores = {}
        for name, result in self.results.items():
            # 归一化评分 (0-100)
            return_score = min(max((result['returns_pct'] + 20) / 60 * 30, 0), 30)  # 收益率权重30%
            sharpe_score = min(max((result['sharpe_ratio'] + 2) / 4 * 25, 0), 25)  # 夏普比率权重25%
            dd_score = max(0, (20 - result['max_drawdown']) / 20 * 25)  # 回撤权重25%
            winrate_score = result['win_rate'] / 100 * 20  # 胜率权重20%
            
            total_score = return_score + sharpe_score + dd_score + winrate_score
            scores[name] = total_score
        
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        for rank, (name, score) in enumerate(sorted_scores, 1):
            grade = "S" if score >= 85 else "A" if score >= 70 else "B" if score >= 55 else "C" if score >= 40 else "D"
            print(f"{rank}. {name:<25} 得分: {score:>6.2f}  等级: {grade}")
    
    def _plot_comparison(self):
        """生成对比图表"""
        print("\n生成对比图表...")
        
        # 创建画布
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle(f'策略对比分析 - {self.symbol}', fontsize=16, fontweight='bold')
        
        colors = ['#2ecc71', '#e74c3c', '#3498db', '#f39c12', '#9b59b6']
        
        # 1. 收益率对比柱状图
        ax1 = axes[0, 0]
        strategies = list(self.results.keys())
        returns = [self.results[s]['returns_pct'] for s in strategies]
        bars = ax1.barh(strategies, returns, color=colors[:len(strategies)])
        ax1.set_xlabel('收益率 (%)')
        ax1.set_title('收益率对比')
        ax1.axvline(x=0, color='black', linewidth=0.5)
        
        # 在柱子上添加数值标签
        for bar, ret in zip(bars, returns):
            ax1.text(ret + 1 if ret >= 0 else ret - 3, bar.get_y() + bar.get_height()/2, 
                    f'{ret:+.2f}%', va='center', fontsize=9)
        
        # 2. 夏普比率和最大回撤对比
        ax2 = axes[0, 1]
        sharpe_values = [self.results[s]['sharpe_ratio'] for s in strategies]
        x = range(len(strategies))
        width = 0.35
        
        bars1 = ax2.bar([i - width/2 for i in x], sharpe_values, width, label='夏普比率', color='#3498db')
        ax2_twin = ax2.twinx()
        dd_values = [self.results[s]['max_drawdown'] for s in strategies]
        bars2 = ax2_twin.bar([i + width/2 for i in x], dd_values, width, label='最大回撤 (%)', color='#e74c3c')
        
        ax2.set_xlabel('策略')
        ax2.set_ylabel('夏普比率', color='#3498db')
        ax2_twin.set_ylabel('最大回撤 (%)', color='#e74c3c')
        ax2.set_title('风险收益对比')
        ax2.set_xticks(list(x))
        ax2.set_xticklabels(strategies, rotation=15, ha='right')
        ax2.tick_params(axis='y', labelcolor='#3498db')
        ax2_twin.tick_params(axis='y', labelcolor='#e74c3c')
        
        # 合并图例
        lines1, labels1 = ax2.get_legend_handles_labels()
        lines2, labels2 = ax2_twin.get_legend_handles_labels()
        ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
        
        # 3. 胜率对比
        ax3 = axes[1, 0]
        winrates = [self.results[s]['win_rate'] for s in strategies]
        bars = ax3.bar(strategies, winrates, color=colors[:len(strategies)])
        ax3.set_ylabel('胜率 (%)')
        ax3.set_title('胜率对比')
        ax3.set_ylim(0, 100)
        ax3.axhline(y=50, color='gray', linestyle='--', linewidth=0.5, label='50%基准线')
        ax3.legend()
        
        # 在柱子上添加数值标签
        for bar, wr in zip(bars, winrates):
            ax3.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 2,
                    f'{wr:.1f}%', ha='center', va='bottom', fontsize=9)
        
        # 4. 交易次数对比
        ax4 = axes[1, 1]
        trade_counts = [self.results[s]['total_trades'] for s in strategies]
        bars = ax4.bar(strategies, trade_counts, color=colors[:len(strategies)])
        ax4.set_ylabel('交易次数')
        ax4.set_title('交易频率对比')
        
        # 在柱子上添加数值标签
        for bar, tc in zip(bars, trade_counts):
            ax4.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.2,
                    f'{int(tc)}', ha='center', va='bottom', fontsize=9)
        
        plt.tight_layout()
        
        # 保存图表
        filename = f'strategy_comparison_{self.symbol}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
        filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        print(f"图表已保存: {filepath}")
        
        plt.show()


def main():
    """主函数"""
    print("\n" + "="*70)
    print("策略对比工具")
    print("="*70)
    
    # 创建对比器
    comparator = StrategyComparator(
        symbol="601398",
        adjust="qfq",
        fromdate=datetime(2024, 1, 1),
        todate=datetime.now(),
        startcash=100000,
        commission=0.0005
    )
    
    # 加载数据
    comparator.load_data()
    
    # 导入策略
    from quant.strategy.sma.strategy.SmaCross import SmaCross
    from quant.strategy.boll.BollStrategy import BollStrategy
    from quant.strategy.rsi.RSIStrategy import RSIStrategy
    
    # 配置要对比的策略
    strategies = [
        {
            'class': SmaCross,
            'name': 'SMA双均线(优化版)',
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
    
    # 执行对比
    comparator.compare_strategies(strategies)
    
    print("\n对比分析完成!")


if __name__ == '__main__':
    main()
