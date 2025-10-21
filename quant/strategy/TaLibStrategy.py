import backtrader as bt
import talib
import numpy as np


class TaLibStrategy(bt.Strategy):
    """
    使用ta_lib指标的策略示例
    结合RSI和MACD指标进行交易决策
    """
    params = (
        ('rsi_period', 14),
        ('macd_fast', 12),
        ('macd_slow', 26),
        ('macd_signal', 9),
        ('rsi_upper', 70),
        ('rsi_lower', 30),
        ('printlog', False),
    )

    def log(self, txt, doprint=False):
        ''' Logging function for this strategy'''
        if self.params.printlog or doprint:
            dt = self.datas[0].datetime.date(0)
            print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # 初始化指标计算所需的缓存
        self.close_prices = []
        
        # 初始化backtrader内置指标用于比较
        self.sma = bt.indicators.SimpleMovingAverage(period=20)
        
        # 用于跟踪订单
        self.order = None

    def next(self):
        # 收集收盘价用于ta_lib计算
        self.close_prices.append(self.data.close[0])
        
        # 确保有足够的数据进行指标计算
        if len(self.close_prices) < max(self.params.rsi_period, self.params.macd_slow):
            return

        # 使用ta_lib计算RSI
        rsi_values = talib.RSI(np.array(self.close_prices), timeperiod=self.params.rsi_period)
        current_rsi = rsi_values[-1]
        
        # 使用ta_lib计算MACD
        macd, macd_signal, macd_hist = talib.MACD(
            np.array(self.close_prices),
            fastperiod=self.params.macd_fast,
            slowperiod=self.params.macd_slow,
            signalperiod=self.params.macd_signal
        )
        
        # 获取当前MACD值
        current_macd = macd[-1] if len(macd) > 0 and not np.isnan(macd[-1]) else 0
        current_macd_signal = macd_signal[-1] if len(macd_signal) > 0 and not np.isnan(macd_signal[-1]) else 0
        prev_macd = macd[-2] if len(macd) > 1 and not np.isnan(macd[-2]) else 0
        prev_macd_signal = macd_signal[-2] if len(macd_signal) > 1 and not np.isnan(macd_signal[-2]) else 0
        
        # 检查是否有未完成的订单
        if self.order:
            return

        # 交易逻辑
        # 当RSI低于下限且MACD上穿信号线时买入
        if current_rsi < self.params.rsi_lower:
            # 检查MACD是否上穿信号线
            if prev_macd < prev_macd_signal and current_macd > current_macd_signal:
                if not self.position:  # 如果没有持仓
                    self.log('BUY CREATE, %.2f' % self.data.close[0])
                    self.order = self.buy()

        # 当RSI高于上限且MACD下穿信号线时卖出
        elif current_rsi > self.params.rsi_upper:
            # 检查MACD是否下穿信号线
            if prev_macd > prev_macd_signal and current_macd < current_macd_signal:
                if self.position:  # 如果有持仓
                    self.log('SELL CREATE, %.2f' % self.data.close[0])
                    self.order = self.sell()

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # 订单已提交/已接受 - 等待成交
            return

        # 订单已完成
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))
            else:  # Sell
                self.log(
                    'SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # 重置订单
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))