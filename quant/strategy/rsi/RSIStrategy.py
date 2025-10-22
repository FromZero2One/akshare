import backtrader as bt


class RSIStrategy(bt.Strategy):
    """
    RSI相对强弱指标交易策略
    
    当RSI低于超卖线(默认30)时买入，当RSI高于超买线(默认70)时卖出
    """
    params = (
        ('rsi_period', 14),  # RSI计算周期 默认参数：周期14天，超买线70，超卖线30
        ('rsi_upper', 70),  # 超买阈值
        ('rsi_lower', 30),  # 超卖阈值
        ('printlog', False),  # 是否打印交易日志
    )

    def log(self, txt, doprint=False):
        ''' Logging function for this strategy'''
        if self.params.printlog or doprint:
            dt = self.datas[0].datetime.date(0)
            print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # 初始化RSI指标
        self.rsi = bt.indicators.RSI_SMA(
            self.datas[0].close,
            period=self.params.rsi_period
        )

        # 用于跟踪订单
        self.order = None

    def next(self):
        # 检查是否有未完成的订单
        if self.order:
            return

        # 如果没有持仓，检查是否应该买入
        if not self.position:
            # 当RSI低于超卖线时买入
            if self.rsi[0] < self.params.rsi_lower:
                self.log('BUY CREATE, %.2f' % self.data.close[0])
                self.order = self.buy()

        # 如果有持仓，检查是否应该卖出
        else:
            # 当RSI高于超买线时卖出
            if self.rsi[0] > self.params.rsi_upper:
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
