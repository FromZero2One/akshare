import backtrader as bt
import talib
import numpy as np


class AdvancedTaLibStrategy(bt.Strategy):
    """
    高级ta_lib策略示例
    结合多个指标：布林带、RSI、MACD和随机指标
    """
    params = (
        ('bb_period', 20),
        ('bb_dev', 2),
        ('rsi_period', 14),
        ('macd_fast', 12),
        ('macd_slow', 26),
        ('macd_signal', 9),
        ('stoch_k_period', 14),
        ('stoch_d_period', 3),
        ('rsi_upper', 70),
        ('rsi_lower', 30),
        ('stoch_upper', 80),
        ('stoch_lower', 20),
        ('printlog', False),
    )

    def log(self, txt, doprint=False):
        ''' Logging function for this strategy'''
        if self.params.printlog or doprint:
            dt = self.datas[0].datetime.date(0)
            print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # 初始化指标计算所需的缓存
        self.prices = {
            'open': [],
            'high': [],
            'low': [],
            'close': [],
            'volume': []
        }
        
        # 用于跟踪订单
        self.order = None

    def next(self):
        # 收集价格数据用于ta_lib计算
        self.prices['open'].append(self.data.open[0])
        self.prices['high'].append(self.data.high[0])
        self.prices['low'].append(self.data.low[0])
        self.prices['close'].append(self.data.close[0])
        self.prices['volume'].append(self.data.volume[0])
        
        # 确保有足够的数据进行指标计算
        if len(self.prices['close']) < max(
            self.params.bb_period, 
            self.params.rsi_period, 
            self.params.macd_slow,
            self.params.stoch_k_period
        ):
            return

        # 转换为numpy数组
        close_array = np.array(self.prices['close'])
        high_array = np.array(self.prices['high'])
        low_array = np.array(self.prices['low'])

        # 使用ta_lib计算布林带
        upperband, middleband, lowerband = talib.BBANDS(
            close_array,
            timeperiod=self.params.bb_period,
            nbdevup=self.params.bb_dev,
            nbdevdn=self.params.bb_dev
        )
        current_upperband = upperband[-1]
        current_lowerband = lowerband[-1]
        current_middleband = middleband[-1]

        # 使用ta_lib计算RSI
        rsi_values = talib.RSI(close_array, timeperiod=self.params.rsi_period)
        current_rsi = rsi_values[-1]

        # 使用ta_lib计算MACD
        macd, macd_signal, macd_hist = talib.MACD(
            close_array,
            fastperiod=self.params.macd_fast,
            slowperiod=self.params.macd_slow,
            signalperiod=self.params.macd_signal
        )
        current_macd = macd[-1] if len(macd) > 0 and not np.isnan(macd[-1]) else 0
        current_macd_signal = macd_signal[-1] if len(macd_signal) > 0 and not np.isnan(macd_signal[-1]) else 0
        prev_macd = macd[-2] if len(macd) > 1 and not np.isnan(macd[-2]) else 0
        prev_macd_signal = macd_signal[-2] if len(macd_signal) > 1 and not np.isnan(macd_signal[-2]) else 0

        # 使用ta_lib计算随机指标
        slowk, slowd = talib.STOCH(
            high_array,
            low_array,
            close_array,
            fastk_period=self.params.stoch_k_period,
            slowk_period=self.params.stoch_d_period,
            slowd_period=self.params.stoch_d_period
        )
        current_slowk = slowk[-1] if len(slowk) > 0 and not np.isnan(slowk[-1]) else 0
        current_slowd = slowd[-1] if len(slowd) > 0 and not np.isnan(slowd[-1]) else 0

        # 检查是否有未完成的订单
        if self.order:
            return

        current_price = self.data.close[0]
        
        # 买入条件：
        # 1. 价格低于布林带下轨（超卖）
        # 2. RSI低于30（超卖）
        # 3. 随机指标低于20（超卖）
        # 4. MACD上穿信号线
        if (current_price < current_lowerband and
            current_rsi < self.params.rsi_lower and
            current_slowk < self.params.stoch_lower and
            prev_macd < prev_macd_signal and 
            current_macd > current_macd_signal):
            
            if not self.position:  # 如果没有持仓
                self.log('BUY CREATE, %.2f' % current_price)
                self.order = self.buy()

        # 卖出条件：
        # 1. 价格高于布林带上轨（超买）
        # 2. RSI高于70（超买）
        # 3. 随机指标高于80（超买）
        # 4. MACD下穿信号线
        elif (current_price > current_upperband and
              current_rsi > self.params.rsi_upper and
              current_slowk > self.params.stoch_upper and
              prev_macd > prev_macd_signal and
              current_macd < current_macd_signal):
            
            if self.position:  # 如果有持仓
                self.log('SELL CREATE, %.2f' % current_price)
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