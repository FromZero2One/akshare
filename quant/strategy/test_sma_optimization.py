#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2026/5/15
Desc: SMA策略参数快速优化测试
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
from quant.strategy.sma.strategy.SmaCross import SmaCross


def optimize_sma_quick():
    """快速优化SMA策略参数"""
    print("\n" + "="*70)
    print("🔧 SMA双均线策略参数优化")
    print("="*70)
    
    # 配置
    symbol = "601398"
    adjust = "qfq"
    fromdate = datetime(2024, 1, 1)
    todate = datetime.now()
    startcash = 100000
    commission = 0.0005
    
    # 加载数据
    print(f"\n📊 正在加载股票 {symbol} 的数据...")
    df = db_orm.get_mysql_data_to_df(
        orm_class=StockHistoryDailyInfoEntity,
        adjust=adjust,
        symbol=symbol
    )
    
    if df.empty:
        print("❌ 数据库中没有数据")
        return
    
    required_columns = ['date', 'open', 'close', 'high', 'low', 'volume']
    df = df[required_columns].copy()
    df.index = pd.to_datetime(df['date'])
    
    print(f"✅ 成功加载 {len(df)} 条数据")
    print(f"   日期范围: {df.index.min()} 至 {df.index.max()}")
    
    # 定义参数范围（精简版，减少测试时间）
    param_ranges = {
        'pfast': [5, 7, 10],           # 短期均线周期
        'pslow': [20, 30, 50],         # 长期均线周期
        'stop_loss': [0.05, 0.08],     # 止损比例
        'take_profit': [0.10, 0.15],   # 止盈比例
        'max': [0.8, 1.0]              # 资金使用比例
    }
    
    # 生成所有参数组合
    param_names = list(param_ranges.keys())
    param_values = list(param_ranges.values())
    all_combinations = list(product(*param_values))
    
    print(f"\n📋 总共需要测试 {len(all_combinations)} 种参数组合\n")
    
    results = []
    
    for i, combo in enumerate(all_combinations, 1):
        params = dict(zip(param_names, combo))
        
        try:
            # 创建回测系统
            cerebro = bt.Cerebro()
            
            data = bt.feeds.PandasData(
                dataname=df,
                fromdate=fromdate,
                todate=todate
            )
            cerebro.adddata(data)
            
            # 添加策略和参数
            cerebro.addstrategy(
                SmaCross,
                pfast=params['pfast'],
                pslow=params['pslow'],
                stop_loss=params['stop_loss'],
                take_profit=params['take_profit'],
                max=params['max'],
                printlog=False
            )
            
            cerebro.broker.setcash(startcash)
            cerebro.broker.setcommission(commission=commission)
            
            # 运行回测
            cerebro.run()
            
            endcash = cerebro.broker.getvalue()
            net_profit = endcash - startcash
            returns_pct = (net_profit / startcash) * 100
            
            results.append({
                'params': params.copy(),
                'endcash': endcash,
                'net_profit': net_profit,
                'returns_pct': returns_pct
            })
            
            # 显示进度
            if i % 5 == 0 or i == len(all_combinations):
                print(f"   进度: {i}/{len(all_combinations)} ({i/len(all_combinations)*100:.1f}%)")
                
        except Exception as e:
            print(f"   ⚠️  参数组合 {i} 测试失败: {e}")
            continue
    
    # 排序并显示最佳结果
    if results:
        results.sort(key=lambda x: x['returns_pct'], reverse=True)
        
        print("\n" + "="*70)
        print("🏆 SMA策略参数优化结果 - Top 10")
        print("="*70)
        
        for rank, result in enumerate(results[:10], 1):
            params = result['params']
            print(f"\n排名 #{rank}:")
            print(f"  收益率: {result['returns_pct']:+.2f}%")
            print(f"  净收益: {result['net_profit']:+.2f}元")
            print(f"  最终资金: {result['endcash']:.2f}元")
            print(f"  参数配置:")
            print(f"    - pfast (短期均线): {params['pfast']}")
            print(f"    - pslow (长期均线): {params['pslow']}")
            print(f"    - stop_loss (止损): {params['stop_loss']*100:.1f}%")
            print(f"    - take_profit (止盈): {params['take_profit']*100:.1f}%")
            print(f"    - max (资金比例): {params['max']*100:.0f}%")
        
        # 对比原始参数
        print("\n" + "="*70)
        print("📊 与原始参数对比")
        print("="*70)
        
        original_params = {
            'pfast': 5,
            'pslow': 20,
            'stop_loss': 0.05,
            'take_profit': 0.10,
            'max': 0.8
        }
        
        # 找到原始参数的结果
        original_result = None
        for r in results:
            if r['params'] == original_params:
                original_result = r
                break
        
        if original_result:
            best_result = results[0]
            print(f"\n原始参数收益率: {original_result['returns_pct']:+.2f}%")
            print(f"最优参数收益率: {best_result['returns_pct']:+.2f}%")
            improvement = best_result['returns_pct'] - original_result['returns_pct']
            print(f"提升幅度: {improvement:+.2f}%")
            
            if improvement > 0:
                print(f"\n✅ 建议采用最优参数配置！")
            else:
                print(f"\n⚠️  原始参数已经是较好的配置")
        
        return results[0]
    else:
        print("❌ 没有找到有效的参数组合")
        return None


if __name__ == '__main__':
    optimize_sma_quick()
