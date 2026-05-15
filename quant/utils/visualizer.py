#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2026/5/15
Desc: 回测结果可视化工具
支持绘制 K 线图、买卖信号、资金曲线及回撤图
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np


class BacktestVisualizer:
    """
    回测结果可视化器
    
    特性:
    1. 自动对齐交易记录与行情数据
    2. 绘制专业的 K 线与技术指标图
    3. 展示资金增长与最大回撤
    """

    def __init__(self, style='seaborn-v0_8-darkgrid'):
        plt.style.use(style)
        self.figures = []

    def plot_strategy_performance(self, df_data, trades, portfolio_value, title="Strategy Performance"):
        """
        绘制策略综合表现图
        
        Args:
            df_data: 包含 OHLCV 数据的 DataFrame，索引为日期
            trades: 交易记录列表 (from backtrader)
            portfolio_value: 每日资产总值列表 (from backtrader)
        """
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), gridspec_kw={'height_ratios': [3, 1]})
        
        # --- 上图：K线与买卖点 ---
        ax1.set_title(title, fontsize=14)
        
        # 绘制收盘价曲线
        ax1.plot(df_data.index, df_data['close'], label='Close Price', color='blue', alpha=0.6)
        
        # 标记买卖点
        buy_dates, buy_prices = [], []
        sell_dates, sell_prices = [], []
        
        for trade in trades:
            if trade.status == trade.Completed:
                dt = trade.datetime.date()
                if trade.isbuy():
                    buy_dates.append(dt)
                    buy_prices.append(trade.price)
                else:
                    sell_dates.append(dt)
                    sell_prices.append(trade.price)
                    
        ax1.scatter(buy_dates, buy_prices, marker='^', color='red', s=100, label='Buy Signal', zorder=5)
        ax1.scatter(sell_dates, sell_prices, marker='v', color='green', s=100, label='Sell Signal', zorder=5)
        
        ax1.legend(loc='upper left')
        ax1.grid(True, linestyle='--', alpha=0.5)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax1.tick_params(axis='x', rotation=45)

        # --- 下图：资金曲线 ---
        if portfolio_value:
            dates = [dt.date() for dt in portfolio_value.index]
            values = portfolio_value.values
            
            ax2.plot(dates, values, label='Portfolio Value', color='purple', linewidth=2)
            ax2.fill_between(dates, values, alpha=0.1, color='purple')
            
            ax2.set_ylabel("Value ($)")
            ax2.legend(loc='upper left')
            ax2.grid(True, linestyle='--', alpha=0.5)
            ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            ax2.tick_params(axis='x', rotation=45)

        plt.tight_layout()
        plt.savefig('backtest_report.png', dpi=300, bbox_inches='tight')
        plt.show()
        print("📊 回测报告图已保存为 backtest_report.png")

    def plot_drawdown(self, drawdown_info):
        """
        绘制最大回撤图
        """
        if not drawdown_info:
            return
            
        plt.figure(figsize=(12, 6))
        plt.plot(drawdown_info.index, drawdown_info.drawdown, color='red', label='Drawdown %')
        plt.fill_between(drawdown_info.index, drawdown_info.drawdown, color='red', alpha=0.2)
        plt.title('Strategy Drawdown Analysis')
        plt.ylabel('Drawdown (%)')
        plt.grid(True, linestyle='--', alpha=0.5)
        plt.legend()
        plt.tight_layout()
        plt.savefig('drawdown_report.png', dpi=300, bbox_inches='tight')
        plt.show()
