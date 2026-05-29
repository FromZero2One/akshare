import backtrader as bt


class RSIStrategyOptimized(bt.Strategy):
    strategy_name = 'RSI相对强弱指标(优化版)'
    """
    RSI相对强弱指标交易策略 - 优化版
    
    优化点:
    1. 使用更敏感的RSI周期 (10 instead of 14)
    2. 放宽超买超卖阈值 (75/25 instead of 70/30)
    3. 增加仓位管理
    4. 添加趋势过滤
    """
    params = (
        ('rsi_period', 10),      # RSI计算周期 (优化: 14->10)
        ('rsi_upper', 75),       # 超买阈值 (优化: 70->75)
        ('rsi_lower', 25),       # 超卖阈值 (优化: 30->25)
        ('sma_period', 20),      # 趋势过滤均线周期
        ('position_size', 0.8),  # 仓位比例
        ('printlog', False),     # 是否打印交易日志
    )

    def log(self, txt, doprint=False):
        if self.params.printlog or doprint:
            dt = self.datas[0].datetime.date(0)
            print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # 初始化RSI指标（使用默认的 EMA/SMMA 方式，避免 RSI_SMA 的除零问题）
        self.rsi = bt.indicators.RSI(
            self.datas[0].close,
            period=self.params.rsi_period
        )
        
        # 添加趋势过滤 - 20日均线
        self.sma_trend = bt.indicators.SimpleMovingAverage(
            self.datas[0].close,
            period=self.params.sma_period
        )

        # 用于跟踪订单
        self.order = None

    def next(self):
        # 检查是否有未完成的订单
        if self.order:
            return

        current_price = self.data.close[0]
        
        # 如果没有持仓，检查是否应该买入
        if not self.position:
            # 买入条件:
            # 1. RSI低于超卖线
            # 2. 价格在20日均线上方 (上升趋势)
            if (self.rsi[0] < self.params.rsi_lower and 
                current_price > self.sma_trend[0]):
                
                # 计算买入数量
                size = int(self.params.position_size * self.broker.getcash() / current_price)
                if size > 0:
                    self.log('BUY CREATE, Price: %.2f, RSI: %.2f' % (current_price, self.rsi[0]))
                    self.order = self.buy(size=size)

        # 如果有持仓，检查是否应该卖出
        else:
            # 卖出条件:
            # 1. RSI高于超买线
            # 2. 或者价格跌破20日均线 (趋势反转)
            if (self.rsi[0] > self.params.rsi_upper or 
                current_price < self.sma_trend[0]):
                
                self.log('SELL CREATE, Price: %.2f, RSI: %.2f' % (current_price, self.rsi[0]))
                self.order = self.sell(size=self.position.size)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Size: %d, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.size,
                     order.executed.value,
                     order.executed.comm))
            else:
                self.log(
                    'SELL EXECUTED, Price: %.2f, Size: %d, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.size,
                     order.executed.value,
                     order.executed.comm))

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('TRADE PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))
