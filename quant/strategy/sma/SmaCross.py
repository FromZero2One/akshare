import backtrader as bt


class SmaCross(bt.Strategy):
    strategy_name = '双均线交叉策略(SmaCross)'
    """
    双均线交叉策略
    5日线上穿20日线时买入(快速上穿慢速) 下穿时卖出
    """
    # 全局设定交易策略的参数
    params = (
        ('max', 0.8),  # 最大可以资金比例
        ('pfast', 5),  # 短期均线周期
        ('pslow', 20),  # 长期均线周期
        ('stop_loss', 0.05),  # 止损百分比 5%
        ('take_profit', 0.1),  # 止盈百分比 10%
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

        # 添加均线指标
        self.sma_fast = bt.ind.MovingAverageSimple(
            self.datas[0],
            period=self.params.pfast
        )  # fast moving average

        self.sma_slow = bt.ind.MovingAverageSimple(
            self.datas[0],
            period=self.params.pslow
        )  # slow moving average

        self.crossover = bt.ind.CrossOver(
            self.sma_fast,
            self.sma_slow
        )  # crossover signal

    def next(self):
        """
        主逻辑执行函数，每个K线周期执行一次
        """
        # 检查是否有未完成的订单
        if self.order:
            return

        # 检查是否持有仓位
        if not self.position:
            # 没有仓位时，检查是否出现金叉买入信号
            if self.crossover > 0:
                # 计算买入数量 - 使用可用资金的一定比例买入
                close_price = self.data.close[0]
                size = int(self.params.max * self.broker.getcash() / close_price)

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

            # 检查是否需要止损
            elif self.data.close[0] < self.buy_price * (1.0 - self.params.stop_loss):
                self.log('STOP LOSS SELL CREATE, %.2f' % self.data.close[0])
                # 卖出当前所有持仓
                self.order = self.sell(size=self.position.size)

            # 检查是否需要止盈
            elif self.data.close[0] > self.buy_price * (1.0 + self.params.take_profit):
                self.log('TAKE PROFIT SELL CREATE, %.2f' % self.data.close[0])
                # 卖出当前所有持仓
                self.order = self.sell(size=self.position.size)

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

            # 修复错误：使用正确的属性来记录订单执行的bar
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
