#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2026/5/15
Desc: RSI策略诊断工具 - 分析RSI指标和交易信号
"""

import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['SimHei']
matplotlib.rcParams['axes.unicode_minus'] = False

import quant.utils.db_orm as db_orm
from quant.entity.StockHistoryDailyInfoEntity import StockHistoryDailyInfoEntity


def analyze_rsi_signals(symbol="601398", adjust="qfq", 
                        rsi_period=14, rsi_upper=70, rsi_lower=30,
                        fromdate=datetime(2024, 1, 1),
                        todate=datetime.now()):
    """
    分析RSI信号生成情况
    
    Args:
        symbol: 股票代码
        adjust: 复权类型
        rsi_period: RSI周期
        rsi_upper: 超买线
        rsi_lower: 超卖线
    """
    print("="*70)
    print("RSI策略诊断分析")
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
    
    required_columns = ['date', 'open', 'close', 'high', 'low', 'volume']
    df = df[required_columns].copy()
    df.index = pd.to_datetime(df['date'])
    
    # 过滤时间范围
    df = df[(df.index >= fromdate) & (df.index <= todate)]
    
    print(f"加载了 {len(df)} 条数据")
    print(f"日期范围: {df.index.min()} 至 {df.index.max()}")
    
    # 计算RSI
    print(f"\n计算RSI指标 (周期={rsi_period}, 超买={rsi_upper}, 超卖={rsi_lower})...")
    
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    df['rsi'] = rsi
    
    # 识别买卖信号
    df['buy_signal'] = df['rsi'] < rsi_lower
    df['sell_signal'] = df['rsi'] > rsi_upper
    
    buy_signals = df[df['buy_signal']]
    sell_signals = df[df['sell_signal']]
    
    print(f"\n信号统计:")
    print(f"  买入信号次数: {len(buy_signals)}")
    print(f"  卖出信号次数: {len(sell_signals)}")
    print(f"  总信号数: {len(buy_signals) + len(sell_signals)}")
    
    if len(buy_signals) > 0:
        print(f"\n前5个买入信号:")
        for idx, row in buy_signals.head().iterrows():
            print(f"  {idx.strftime('%Y-%m-%d')}: 收盘价={row['close']:.2f}, RSI={row['rsi']:.2f}")
    
    if len(sell_signals) > 0:
        print(f"\n前5个卖出信号:")
        for idx, row in sell_signals.head().iterrows():
            print(f"  {idx.strftime('%Y-%m-%d')}: 收盘价={row['close']:.2f}, RSI={row['rsi']:.2f}")
    
    # RSI统计
    print(f"\nRSI统计:")
    print(f"  最小值: {df['rsi'].min():.2f}")
    print(f"  最大值: {df['rsi'].max():.2f}")
    print(f"  平均值: {df['rsi'].mean():.2f}")
    print(f"  中位数: {df['rsi'].median():.2f}")
    print(f"  低于{rsi_lower}的次数: {(df['rsi'] < rsi_lower).sum()}")
    print(f"  高于{rsi_upper}的次数: {(df['rsi'] > rsi_upper).sum()}")
    
    # 价格统计
    print(f"\n价格统计:")
    print(f"  最低价: {df['low'].min():.2f}")
    print(f"  最高价: {df['high'].max():.2f}")
    print(f"  平均价: {df['close'].mean():.2f}")
    print(f"  涨跌幅: {(df['close'].iloc[-1] / df['close'].iloc[0] - 1) * 100:.2f}%")
    
    # 可视化
    print("\n生成RSI分析图表...")
    plot_rsi_analysis(df, rsi_upper, rsi_lower, symbol)
    
    return df


def test_different_rsi_params(symbol="601398", adjust="qfq"):
    """测试不同的RSI参数组合"""
    print("\n" + "="*70)
    print("测试不同RSI参数组合")
    print("="*70)
    
    # 加载数据
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
    
    # 定义参数组合
    param_combinations = [
        (7, 75, 25),   # 短周期，宽阈值
        (10, 70, 30),  # 中短周期，标准阈值
        (14, 70, 30),  # 标准参数
        (14, 65, 35),  # 标准周期，窄阈值
        (14, 75, 25),  # 标准周期，宽阈值
        (21, 70, 30),  # 长周期，标准阈值
        (21, 65, 35),  # 长周期，窄阈值
    ]
    
    results = []
    
    for period, upper, lower in param_combinations:
        # 计算RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # 统计信号
        buy_count = (rsi < lower).sum()
        sell_count = (rsi > upper).sum()
        total_signals = buy_count + sell_count
        
        results.append({
            'period': period,
            'upper': upper,
            'lower': lower,
            'buy_signals': buy_count,
            'sell_signals': sell_count,
            'total_signals': total_signals
        })
        
        print(f"\n参数: period={period}, upper={upper}, lower={lower}")
        print(f"  买入信号: {buy_count}, 卖出信号: {sell_count}, 总计: {total_signals}")
    
    # 找出最佳参数
    print("\n" + "="*70)
    print("参数对比总结")
    print("="*70)
    
    header = f"{'周期':<8} {'超买线':<8} {'超卖线':<8} {'买入信号':<10} {'卖出信号':<10} {'总信号':<10}"
    print(header)
    print("-" * 70)
    
    for r in results:
        row = f"{r['period']:<8} {r['upper']:<8} {r['lower']:<8} {r['buy_signals']:<10} {r['sell_signals']:<10} {r['total_signals']:<10}"
        print(row)
    
    # 推荐参数
    best_for_active = max(results, key=lambda x: x['total_signals'])
    print(f"\n最活跃的参数 (信号最多): period={best_for_active['period']}, upper={best_for_active['upper']}, lower={best_for_active['lower']}")
    print(f"  总信号数: {best_for_active['total_signals']}")


def plot_rsi_analysis(df, rsi_upper, rsi_lower, symbol):
    """绘制RSI分析图表"""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), gridspec_kw={'height_ratios': [3, 1]})
    
    # 上图：价格和RSI
    ax1.plot(df.index, df['close'], label='收盘价', color='blue', linewidth=1)
    
    # 标记买入信号
    buy_signals = df[df['rsi'] < rsi_lower]
    if len(buy_signals) > 0:
        ax1.scatter(buy_signals.index, buy_signals['close'], 
                   marker='^', color='green', s=100, label=f'买入信号 (RSI<{rsi_lower})', zorder=5)
    
    # 标记卖出信号
    sell_signals = df[df['rsi'] > rsi_upper]
    if len(sell_signals) > 0:
        ax1.scatter(sell_signals.index, sell_signals['close'], 
                   marker='v', color='red', s=100, label=f'卖出信号 (RSI>{rsi_upper})', zorder=5)
    
    ax1.set_ylabel('价格')
    ax1.set_title(f'{symbol} RSI策略信号分析')
    ax1.legend(loc='best')
    ax1.grid(True, alpha=0.3)
    
    # 下图：RSI指标
    ax2.plot(df.index, df['rsi'], label='RSI', color='purple', linewidth=1)
    ax2.axhline(y=rsi_upper, color='red', linestyle='--', linewidth=1, label=f'超买线 ({rsi_upper})')
    ax2.axhline(y=rsi_lower, color='green', linestyle='--', linewidth=1, label=f'超卖线 ({rsi_lower})')
    ax2.axhline(y=50, color='gray', linestyle='-', linewidth=0.5, alpha=0.5)
    ax2.fill_between(df.index, rsi_upper, 100, alpha=0.1, color='red', label='超买区')
    ax2.fill_between(df.index, 0, rsi_lower, alpha=0.1, color='green', label='超卖区')
    
    ax2.set_xlabel('日期')
    ax2.set_ylabel('RSI')
    ax2.set_ylim(0, 100)
    ax2.legend(loc='best')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # 保存图表
    filename = f'rsi_diagnosis_{symbol}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
    filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    print(f"图表已保存: {filepath}")
    
    plt.show()


def main():
    """主函数"""
    print("\nRSI策略诊断工具")
    print("="*70)
    
    # 选择股票
    symbol = input("请输入股票代码 (默认601398): ").strip() or "601398"
    
    # 分析当前参数
    print("\n[1] 分析当前参数 (14, 70, 30)")
    print("[2] 测试不同参数组合")
    print("[3] 两者都执行")
    
    choice = input("\n请选择 (1-3, 默认3): ").strip() or "3"
    
    if choice in ['1', '3']:
        analyze_rsi_signals(
            symbol=symbol,
            rsi_period=14,
            rsi_upper=70,
            rsi_lower=30
        )
    
    if choice in ['2', '3']:
        test_different_rsi_params(symbol=symbol)
    
    print("\n诊断完成!")


if __name__ == '__main__':
    main()
