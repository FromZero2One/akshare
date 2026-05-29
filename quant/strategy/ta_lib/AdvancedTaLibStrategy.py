import backtrader as bt


class AdvancedTaLibStrategy(bt.Strategy):
    """
    多指标组合策略（布林带 + RSI + MACD + 随机指标）

    使用 Backtrader 内置指标，消除手动缓冲区管理。
    买入需要同时满足：价格低于布林带下轨 + RSI 超卖 + 随机指标超卖 + MACD 金叉
    卖出需要同时满足：价格高于布林带上轨 + RSI 超买 + 随机指标超买 + MACD 死叉
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
        if self.params.printlog or doprint:
            dt = self.datas[0].datetime.date(0)
            print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # 布林带 — Backtrader 内置指标，自动管线管理
        self.bb = bt.indicators.BollingerBands(
            self.data.close,
            period=self.params.bb_period,
            devfactor=self.params.bb_dev,
        )
        # RSI
        self.rsi = bt.indicators.RSI(
            self.data.close, period=self.params.rsi_period)
        # MACD
        self.macd = bt.indicators.MACD(
            self.data.close,
            period_me1=self.params.macd_fast,
            period_me2=self.params.macd_slow,
            period_signal=self.params.macd_signal,
        )
        # 随机指标
        self.stoch = bt.indicators.Stochastic(
            self.data,
            period=self.params.stoch_k_period,
            period_dfast=self.params.stoch_d_period,
        )
        self.order = None

    def next(self):
        if self.order:
            return

        current_price = self.data.close[0]
        buy_signals = 0
        sell_signals = 0

        # 条件 1：布林带位置
        if current_price < self.bb.lines.bot[0]:
            buy_signals += 1
        if current_price > self.bb.lines.top[0]:
            sell_signals += 1

        # 条件 2：RSI
        if self.rsi[0] < self.params.rsi_lower:
            buy_signals += 1
        if self.rsi[0] > self.params.rsi_upper:
            sell_signals += 1

        # 条件 3：随机指标
        if self.stoch.percK[0] < self.params.stoch_lower:
            buy_signals += 1
        if self.stoch.percK[0] > self.params.stoch_upper:
            sell_signals += 1

        # 条件 4：MACD 交叉
        if (self.macd.macd[-1] < self.macd.signal[-1] and
                self.macd.macd[0] > self.macd.signal[0]):
            buy_signals += 1
        if (self.macd.macd[-1] > self.macd.signal[-1] and
                self.macd.macd[0] < self.macd.signal[0]):
            sell_signals += 1

        if not self.position and buy_signals >= 4:
            self.log('BUY CREATE, %.2f' % current_price)
            self.order = self.buy()
        elif self.position and sell_signals >= 4:
            self.log('SELL CREATE, %.2f' % current_price)
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
