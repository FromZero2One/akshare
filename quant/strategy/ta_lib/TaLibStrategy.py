import backtrader as bt


class TaLibStrategy(bt.Strategy):
    """
    结合 RSI 和 MACD 的交易策略

    使用 Backtrader 内置指标（bt.indicators），不再手动管理缓冲区。
    当 RSI 低于下限且 MACD 上穿信号线时买入；
    当 RSI 高于上限且 MACD 下穿信号线时卖出。
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
        if self.params.printlog or doprint:
            dt = self.datas[0].datetime.date(0)
            print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # 使用 Backtrader 内置指标 — 自动管理线路，无需手动缓冲区
        self.rsi = bt.indicators.RSI(
            self.data.close, period=self.params.rsi_period)
        self.macd = bt.indicators.MACD(
            self.data.close,
            period_me1=self.params.macd_fast,
            period_me2=self.params.macd_slow,
            period_signal=self.params.macd_signal,
        )
        self.order = None

    def next(self):
        if self.order:
            return

        if not self.position:
            # 买入条件：RSI 低于下限 且 MACD 上穿信号线
            if (self.rsi[0] < self.params.rsi_lower and
                    self.macd.macd[-1] < self.macd.signal[-1] and
                    self.macd.macd[0] > self.macd.signal[0]):
                self.log('BUY CREATE, %.2f' % self.data.close[0])
                self.order = self.buy()
        else:
            # 卖出条件：RSI 高于上限 且 MACD 下穿信号线
            if (self.rsi[0] > self.params.rsi_upper and
                    self.macd.macd[-1] > self.macd.signal[-1] and
                    self.macd.macd[0] < self.macd.signal[0]):
                self.log('SELL CREATE, %.2f' % self.data.close[0])
                self.order = self.sell()

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))
            else:
                self.log(
                    'SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))
