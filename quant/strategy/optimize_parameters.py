#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2026/5/15
Desc: 策略参数优化工具 - 使用网格搜索找到最优参数组合
"""

import sys
import os
from datetime import datetime
from itertools import product

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

import backtrader as bt
import pandas as pd
import quant.utils.db_orm as db_orm
from quant.entity.StockHistoryDailyInfoEntity import StockHistoryDailyInfoEntity
from quant.utils.parallel_optimizer import ParallelOptimizer


class ParameterOptimizer:
    """策略参数优化器"""
    
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
        print(f"📊 正在加载股票 {self.symbol} 的数据...")
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
            print(f"✅ 成功加载 {len(df)} 条数据")
            print(f"   日期范围: {df.index.min()} 至 {df.index.max()}")
            
        except Exception as e:
            print(f"❌ 加载数据失败: {e}")
            raise
    
    def optimize_sma_strategy(self):
        """优化SMA双均线策略参数（并行版）"""
        print("\n" + "="*70)
        print("🔧 优化SMA双均线策略参数 (Parallel Mode)")
        print("="*70)
        
        from quant.strategy.sma.strategy.SmaCross import SmaCross
        
        # 定义参数范围
        param_ranges = {
            'pfast': [3, 5, 7, 10],           # 短期均线周期
            'pslow': [15, 20, 30, 50],         # 长期均线周期
            'stop_loss': [0.03, 0.05, 0.08],   # 止损比例
            'take_profit': [0.08, 0.10, 0.15], # 止盈比例
            'max': [0.5, 0.8, 1.0]             # 资金使用比例
        }
        
        # 使用并行优化器
        optimizer = ParallelOptimizer()
        results = optimizer.optimize(
            strategy_class=SmaCross,
            data_df=self.data,
            param_ranges=param_ranges,
            fromdate=self.fromdate,
            todate=self.todate,
            startcash=self.startcash,
            commission=self.commission
        )
        
        # 显示最佳结果
        if results:
            print("\n" + "="*70)
            print("🏆 SMA策略参数优化结果 - Top 5")
            print("="*70)
            
            for rank, result in enumerate(results[:5], 1):
                params = result['params']
                print(f"\n排名 #{rank}:")
                print(f"  收益率: {result['returns_pct']:+.2f}%")
                print(f"  净收益: {result['net_profit']:+.2f}元")
                print(f"  最终资金: {result['endcash']:.2f}元")
                print(f"  参数配置: pfast={params['pfast']}, pslow={params['pslow']}, "
                      f"stop_loss={params['stop_loss']*100:.1f}%, take_profit={params['take_profit']*100:.1f}%")
            
            return results[0]
        else:
            print("❌ 没有找到有效的参数组合")
            return None
    
    def optimize_boll_strategy(self):
        """优化布林线策略参数"""
        print("\n" + "="*70)
        print("🔧 优化布林线策略参数")
        print("="*70)
        
        from quant.strategy.boll.BollStrategy import BollStrategy
        
        # 定义参数范围
        param_ranges = {
            'period': [15, 20, 25, 30],     # 布林线周期
            'devfactor': [1.5, 2.0, 2.5],   # 标准差倍数
            'size_pct': [0.3, 0.5, 0.8],    # 每次交易资金比例
        }
        
        # 生成所有参数组合
        param_names = list(param_ranges.keys())
        param_values = list(param_ranges.values())
        all_combinations = list(product(*param_values))
        
        print(f"📋 总共需要测试 {len(all_combinations)} 种参数组合\n")
        
        results = []
        
        for i, combo in enumerate(all_combinations, 1):
            period, devfactor, size_pct = combo
            
            try:
                # 创建自定义布林线策略类
                class OptimizedBollStrategy(BollStrategy):
                    params = (
                        ('period', period),
                        ('devfactor', devfactor),
                        ('size_pct', size_pct),
                    )
                    
                    def __init__(self):
                        self.dataclose = self.datas[0].close
                        self.order = None
                        # 动态计算仓位大小
                        self.size_pct = self.params.size_pct
                        
                        # 使用自定义参数的布林线
                        bb = bt.indicators.BollingerBands(
                            self.datas[0],
                            period=self.params.period,
                            devfactor=self.params.devfactor
                        )
                        self.lines.top = bb.top
                        self.lines.bot = bb.bot
                    
                    def next(self):
                        if not self.position:
                            if self.dataclose <= self.lines.bot[0]:
                                # 根据资金比例计算买入数量
                                close_price = self.dataclose[0]
                                size = int(self.size_pct * self.broker.getcash() / close_price)
                                if size > 0:
                                    self.order = self.buy(size=size)
                        else:
                            if self.dataclose >= self.lines.top[0]:
                                self.order = self.sell(size=self.position.size)
                
                # 创建回测系统
                cerebro = bt.Cerebro()
                
                data = bt.feeds.PandasData(
                    dataname=self.data,
                    fromdate=self.fromdate,
                    todate=self.todate
                )
                cerebro.adddata(data)
                cerebro.addstrategy(OptimizedBollStrategy)
                
                cerebro.broker.setcash(self.startcash)
                cerebro.broker.setcommission(commission=self.commission)
                
                # 运行回测
                cerebro.run()
                
                endcash = cerebro.broker.getvalue()
                net_profit = endcash - self.startcash
                returns_pct = (net_profit / self.startcash) * 100
                
                results.append({
                    'params': {
                        'period': period,
                        'devfactor': devfactor,
                        'size_pct': size_pct
                    },
                    'endcash': endcash,
                    'net_profit': net_profit,
                    'returns_pct': returns_pct
                })
                
                if i % 5 == 0:
                    print(f"   进度: {i}/{len(all_combinations)} ({i/len(all_combinations)*100:.1f}%)")
                    
            except Exception as e:
                print(f"   ⚠️  参数组合 {i} 测试失败: {e}")
                continue
        
        # 排序并显示最佳结果
        if results:
            results.sort(key=lambda x: x['returns_pct'], reverse=True)
            
            print("\n" + "="*70)
            print("🏆 布林线策略参数优化结果 - Top 10")
            print("="*70)
            
            for rank, result in enumerate(results[:10], 1):
                params = result['params']
                print(f"\n排名 #{rank}:")
                print(f"  收益率: {result['returns_pct']:+.2f}%")
                print(f"  净收益: {result['net_profit']:+.2f}元")
                print(f"  最终资金: {result['endcash']:.2f}元")
                print(f"  参数配置:")
                print(f"    - period (周期): {params['period']}")
                print(f"    - devfactor (标准差倍数): {params['devfactor']}")
                print(f"    - size_pct (资金比例): {params['size_pct']*100:.0f}%")
            
            return results[0]
        else:
            print("❌ 没有找到有效的参数组合")
            return None
    
    def optimize_rsi_strategy(self):
        """优化RSI策略参数"""
        print("\n" + "="*70)
        print("🔧 优化RSI策略参数")
        print("="*70)
        
        from quant.strategy.rsi.RSIStrategy import RSIStrategy
        
        # 定义参数范围
        param_ranges = {
            'rsi_period': [7, 10, 14, 21],      # RSI周期
            'rsi_upper': [65, 70, 75, 80],      # 超买线
            'rsi_lower': [20, 25, 30, 35],      # 超卖线
            'stake': [50, 100, 200],            # 每次交易股数
        }
        
        # 生成所有参数组合
        param_names = list(param_ranges.keys())
        param_values = list(param_ranges.values())
        all_combinations = list(product(*param_values))
        
        print(f"📋 总共需要测试 {len(all_combinations)} 种参数组合\n")
        
        results = []
        
        for i, combo in enumerate(all_combinations, 1):
            rsi_period, rsi_upper, rsi_lower, stake = combo
            
            try:
                # 创建回测系统
                cerebro = bt.Cerebro()
                
                data = bt.feeds.PandasData(
                    dataname=self.data,
                    fromdate=self.fromdate,
                    todate=self.todate
                )
                cerebro.adddata(data)
                
                # 添加策略和参数
                cerebro.addstrategy(
                    RSIStrategy,
                    rsi_period=rsi_period,
                    rsi_upper=rsi_upper,
                    rsi_lower=rsi_lower,
                    printlog=False
                )
                
                cerebro.broker.setcash(self.startcash)
                cerebro.broker.setcommission(commission=self.commission)
                cerebro.addsizer(bt.sizers.FixedSize, stake=stake)
                
                # 运行回测
                cerebro.run()
                
                endcash = cerebro.broker.getvalue()
                net_profit = endcash - self.startcash
                returns_pct = (net_profit / self.startcash) * 100
                
                results.append({
                    'params': {
                        'rsi_period': rsi_period,
                        'rsi_upper': rsi_upper,
                        'rsi_lower': rsi_lower,
                        'stake': stake
                    },
                    'endcash': endcash,
                    'net_profit': net_profit,
                    'returns_pct': returns_pct
                })
                
                if i % 10 == 0:
                    print(f"   进度: {i}/{len(all_combinations)} ({i/len(all_combinations)*100:.1f}%)")
                    
            except Exception as e:
                print(f"   ⚠️  参数组合 {i} 测试失败: {e}")
                continue
        
        # 排序并显示最佳结果
        if results:
            results.sort(key=lambda x: x['returns_pct'], reverse=True)
            
            print("\n" + "="*70)
            print("🏆 RSI策略参数优化结果 - Top 10")
            print("="*70)
            
            for rank, result in enumerate(results[:10], 1):
                params = result['params']
                print(f"\n排名 #{rank}:")
                print(f"  收益率: {result['returns_pct']:+.2f}%")
                print(f"  净收益: {result['net_profit']:+.2f}元")
                print(f"  最终资金: {result['endcash']:.2f}元")
                print(f"  参数配置:")
                print(f"    - rsi_period (RSI周期): {params['rsi_period']}")
                print(f"    - rsi_upper (超买线): {params['rsi_upper']}")
                print(f"    - rsi_lower (超卖线): {params['rsi_lower']}")
                print(f"    - stake (交易股数): {params['stake']}")
            
            return results[0]
        else:
            print("❌ 没有找到有效的参数组合")
            return None


def main():
    """主函数"""
    print("\n" + "="*70)
    print("🚀 策略参数优化系统")
    print("="*70)
    
    # 创建优化器
    optimizer = ParameterOptimizer(
        symbol="601398",
        adjust="qfq",
        fromdate=datetime(2024, 1, 1),
        todate=datetime.now(),
        startcash=100000,
        commission=0.0005
    )
    
    # 加载数据
    optimizer.load_data()
    
    # 选择要优化的策略
    print("\n请选择要优化的策略:")
    print("1. SMA双均线策略")
    print("2. 布林线策略")
    print("3. RSI策略")
    print("4. 全部优化")
    
    choice = input("\n请输入选项 (1-4): ").strip()
    
    if choice == '1':
        optimizer.optimize_sma_strategy()
    elif choice == '2':
        optimizer.optimize_boll_strategy()
    elif choice == '3':
        optimizer.optimize_rsi_strategy()
    elif choice == '4':
        print("\n开始优化所有策略...\n")
        best_sma = optimizer.optimize_sma_strategy()
        best_boll = optimizer.optimize_boll_strategy()
        best_rsi = optimizer.optimize_rsi_strategy()
        
        print("\n" + "="*70)
        print("📊 所有策略优化总结")
        print("="*70)
        print(f"SMA策略最佳收益率: {best_sma['returns_pct']:+.2f}%" if best_sma else "SMA策略: 无有效结果")
        print(f"布林线策略最佳收益率: {best_boll['returns_pct']:+.2f}%" if best_boll else "布林线策略: 无有效结果")
        print(f"RSI策略最佳收益率: {best_rsi['returns_pct']:+.2f}%" if best_rsi else "RSI策略: 无有效结果")
    else:
        print("无效的选项")


if __name__ == '__main__':
    main()
