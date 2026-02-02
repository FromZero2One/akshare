import backtrader as bt


class SmaCrossEnhanced(bt.Strategy):
    strategy_name = '增强版双均线交叉策略(SmaCrossEnhanced)'
    """
    增强版双均线交叉策略
    在基础策略上增加了动态仓位管理、趋势过滤、冷却期等优化
    """
    # 全局设定交易策略的参数
    params = (
        ('max', 0.8),  # 最大可使用资金比例
        ('pfast', 5),  # 短期均线周期
        ('pslow', 20),  # 长期均线周期
        ('stop_loss', 0.05),  # 固定止损百分比 5%
        ('take_profit', 0.1),  # 固定止盈百分比 10%
        ('cool_down', 3),  # 交易冷却期(天)
        ('printlog', False),  # 是否打印日志
    )

    def log(self, txt, doprint=False):
        ''' Logging function for this strategy'''
        if self.params.printlog or doprint:
            dt = self.datas[0].datetime.date(0)
            print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        """
        初始化策略所需的各种变量和指标
        """
        # 记录交易订单
        self.order = None
        # 记录买入价格
        self.buy_price = None
        # 记录手续费
        self.buy_comm = None
        # 记录上次交易的bar
        self.last_trade_bar = 0

        # 添加均线指标
        self.sma_fast = bt.ind.MovingAverageSimple(
            self.datas[0],
            period=self.params.pfast
        )  # fast moving average

        self.sma_slow = bt.ind.MovingAverageSimple(
            self.datas[0],
            period=self.params.pslow
        )  # slow moving average

        # 添加长期趋势判断指标
        self.sma_trend = bt.ind.MovingAverageSimple(
            self.datas[0],
            period=self.params.pslow * 2
        )  # 更长期的趋势判断均线

        self.crossover = bt.ind.CrossOver(
            self.sma_fast,
            self.sma_slow
        )  # crossover signal

        # 添加ATR指标用于动态仓位管理
        self.atr = bt.indicators.ATR(self.datas[0], period=14)

    def next(self):
        """
        主逻辑执行函数，每个K线周期执行一次
        """
        # 检查是否有未完成的订单
        if self.order:
            return

        # 检查是否处于冷却期
        if len(self) - self.last_trade_bar < self.params.cool_down:
            return

        # 检查是否持有仓位
        if not self.position:
            # 没有仓位时，检查是否出现金叉买入信号
            # 增加趋势过滤：只有在长期趋势向上时才买入
            if self.crossover > 0 and self.data.close[0] > self.sma_trend[0]:
                # 计算买入数量 - 使用可用资金的一定比例买入
                close_price = self.data.close[0]
                # 根据价格波动性调整仓位大小（简化版ATR）
                position_ratio = self.params.max
                if self.atr[0] > 0:
                    # 波动大时减少仓位
                    position_ratio = max(0.1, self.params.max * (close_price / (close_price + self.atr[0])))

                size = int(position_ratio * self.broker.getcash() / close_price)

                if size > 0:
                    self.log('BUY CREATE, %.2f' % self.data.close[0])
                    self.order = self.buy(size=size)
        else:
            # 有仓位时，检查是否需要平仓
            # 检查是否出现死叉卖出信号
            if self.crossover < 0:
                self.log('DEAD CROSS SELL CREATE, %.2f' % self.data.close[0])
                # 卖出当前所有持仓
                self.order = self.sell(size=self.position.size)
                self.last_trade_bar = len(self)

            # 检查是否需要止损
            elif self.data.close[0] < self.buy_price * (1.0 - self.params.stop_loss):
                self.log('STOP LOSS SELL CREATE, %.2f' % self.data.close[0])
                # 卖出当前所有持仓
                self.order = self.sell(size=self.position.size)
                self.last_trade_bar = len(self)

            # 检查是否需要止盈
            elif self.data.close[0] > self.buy_price * (1.0 + self.params.take_profit):
                self.log('TAKE PROFIT SELL CREATE, %.2f' % self.data.close[0])
                # 卖出当前所有持仓
                self.order = self.sell(size=self.position.size)
                self.last_trade_bar = len(self)

    def notify_order(self, order):
        """
        订单状态通知
        """
        if order.status in [order.Submitted, order.Accepted]:
            # 订单已提交/已接受 - 等待成交
            return

        # 订单已完成
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Size: %d, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.size,
                     order.executed.value,
                     order.executed.comm))

                self.buy_price = order.executed.price
                self.buy_comm = order.executed.comm
            else:  # Sell
                self.log(
                    'SELL EXECUTED, Price: %.2f, Size: %d, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.size,
                     order.executed.value,
                     order.executed.comm))

            # 记录订单执行的bar
            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # 重置订单
        self.order = None

    def notify_trade(self, trade):
        """
        交易状态通知
        """
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))
