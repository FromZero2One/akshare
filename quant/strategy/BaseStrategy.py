#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2026/5/15
Desc: 策略基类 - 封装通用的日志记录、订单通知和交易通知逻辑
"""

import backtrader as bt


class BaseStrategy(bt.Strategy):
    """
    所有自定义策略的基类
    
    特性:
    1. 统一的日志格式化输出
    2. 自动化的订单状态跟踪与日志记录
    3. 自动化的交易盈亏统计
    """
    
    params = (
        ('printlog', False),  # 是否打印详细日志
    )

    def log(self, txt, doprint=False):
        '''统一的日志记录函数'''
        if self.params.printlog or doprint:
            dt = self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()} | {txt}')

    def notify_order(self, order):
        """
        订单状态通知处理
        """
        if order.status in [order.Submitted, order.Accepted]:
            # 订单已提交/被接受，等待成交
            return

        # 检查订单是否完成
        if order.status in [order.Completed]:
            if order.isbuy():
                # 用成交价记账（而非信号日 close），便于后续止盈/止损门槛比较
                if hasattr(self, 'buy_price'):
                    self.buy_price = order.executed.price
                if hasattr(self, 'buy_comm'):
                    self.buy_comm = order.executed.comm
                self.log(
                    f'BUY EXECUTED | Price: {order.executed.price:.2f}, '
                    f'Size: {order.executed.size}, Cost: {order.executed.value:.2f}, '
                    f'Comm: {order.executed.comm:.2f}'
                )
            else:  # Sell
                if hasattr(self, 'buy_price'):
                    self.buy_price = None
                if hasattr(self, 'buy_comm'):
                    self.buy_comm = None
                self.log(
                    f'SELL EXECUTED | Price: {order.executed.price:.2f}, '
                    f'Size: {order.executed.size}, Value: {order.executed.value:.2f}, '
                    f'Comm: {order.executed.comm:.2f}'
                )

            # 记录执行时的 bar 索引（可选用于调试）
            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f'Order Status: {order.getstatusname(order.status)}')

        # 重置订单引用
        self.order = None

    def notify_trade(self, trade):
        """
        交易状态通知处理
        """
        if not trade.isclosed:
            return

        self.log(
            f'TRADE CLOSED | Gross Profit: {trade.pnl:.2f}, '
            f'Net Profit: {trade.pnlcomm:.2f}'
        )
