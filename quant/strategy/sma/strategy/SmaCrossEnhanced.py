import backtrader as bt
from quant.strategy.BaseStrategy import BaseStrategy


class SmaCrossEnhanced(BaseStrategy):
    strategy_name = '增强版双均线交叉策略 (SmaCrossEnhanced)'
    """
    增强版双均线交叉策略
    在基础策略上增加了动态仓位管理、趋势过滤、冷却期等优化

    下单数量由 sizer（默认 DynamicSizer）统一管理，next() 中不传 size。
    """

    params = (
        ('max', 0.8),          # 最大可使用资金比例（参考用，实际由 sizer.position_pct 控制）
        ('pfast', 5),          # 短期均线周期
        ('pslow', 20),         # 长期均线周期
        ('stop_loss', 0.05),   # 固定止损百分比 5%
        ('take_profit', 0.1),  # 固定止盈百分比 10%
        ('cool_down', 3),      # 交易冷却期（天）
    )

    def __init__(self):
        self.order = None
        self.buy_price = None
        self.buy_comm = None
        self.last_trade_bar = 0

        self.sma_fast = bt.ind.MovingAverageSimple(
            self.datas[0], period=self.params.pfast
        )
        self.sma_trend = bt.ind.MovingAverageSimple(
            self.datas[0], period=self.params.pslow * 2
        )
        self.crossover = bt.ind.CrossOver(self.sma_fast, self.sma_trend)
        self.atr = bt.indicators.ATR(self.datas[0], period=14)

    def next(self):
        if self.order:
            return

        # 冷却期
        if len(self) - self.last_trade_bar < self.params.cool_down:
            return

        if not self.position:
            # 趋势过滤：长期趋势向上时才买入
            if self.crossover > 0 and self.data.close[0] > self.sma_trend[0]:
                self.log(f'BUY CREATE, Price: {self.data.close[0]:.2f}')
                self.order = self.buy()
        else:
            if self.buy_price is None:
                return
            # 三种平仓信号：死叉 / 止损 / 止盈
            if self.crossover < 0:
                self.log(f'DEAD CROSS SELL CREATE, Price: {self.data.close[0]:.2f}')
                self.order = self.sell(size=self.position.size)
                self.last_trade_bar = len(self)
            elif self.data.close[0] < self.buy_price * (1.0 - self.params.stop_loss):
                self.log(f'STOP LOSS SELL CREATE, Price: {self.data.close[0]:.2f}')
                self.order = self.sell(size=self.position.size)
                self.last_trade_bar = len(self)
            elif self.data.close[0] > self.buy_price * (1.0 + self.params.take_profit):
                self.log(f'TAKE PROFIT SELL CREATE, Price: {self.data.close[0]:.2f}')
                self.order = self.sell(size=self.position.size)
                self.last_trade_bar = len(self)
