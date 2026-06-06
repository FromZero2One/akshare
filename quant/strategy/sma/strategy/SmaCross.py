import backtrader as bt
from quant.strategy.BaseStrategy import BaseStrategy


class SmaCross(BaseStrategy):
    strategy_name = '双均线交叉策略 (SmaCross)'
    """
    双均线交叉策略
    5 日线上穿 20 日线时买入 (快速上穿慢速) 下穿时卖出
    """
    # 全局设定交易策略的参数（经优化后的最佳配置）
    params = (
        # 注: 下单数量由 DynamicSizer 统一管理（脚本中 add_sizer），
        #     此处 max 仅作参数文档参考，不再在 next() 中使用。
        ('max', 0.8),  # 参考最大资金比例（实际由 sizer.position_pct 控制）
        ('pfast', 7),  # 短期均线周期（优化：5→7）
        ('pslow', 30),  # 长期均线周期（优化：20→30）
        ('stop_loss', 0.05),  # 止损百分比 5%
        ('take_profit', 0.15),  # 止盈百分比（优化：10%→15%）
    )

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
        主逻辑执行函数，每个 K 线周期执行一次
        """
        # 检查是否有未完成的订单
        if self.order:
            return

        # 检查是否持有仓位
        if not self.position:
            # 没有仓位时，检查是否出现金叉买入信号
            if self.crossover > 0:
                # 不传 size：由 cerebro 注册的 sizer（DynamicSizer）按 position_pct 计算
                self.log(f'BUY CREATE, Price: {self.data.close[0]:.2f}')
                self.order = self.buy()
        else:
            # 有仓位时，检查是否需要平仓
            # buy_price 在 BaseStrategy.notify_order 中以成交价写入
            if self.buy_price is None:
                return

            # 检查是否出现死叉卖出信号
            if self.crossover < 0:
                self.log(f'DEAD CROSS SELL CREATE, Price: {self.data.close[0]:.2f}')
                self.order = self.sell(size=self.position.size)

            # 检查是否需要止损
            elif self.data.close[0] < self.buy_price * (1.0 - self.params.stop_loss):
                self.log(f'STOP LOSS SELL CREATE, Price: {self.data.close[0]:.2f}')
                self.order = self.sell(size=self.position.size)

            # 检查是否需要止盈
            elif self.data.close[0] > self.buy_price * (1.0 + self.params.take_profit):
                self.log(f'TAKE PROFIT SELL CREATE, Price: {self.data.close[0]:.2f}')
                self.order = self.sell(size=self.position.size)
