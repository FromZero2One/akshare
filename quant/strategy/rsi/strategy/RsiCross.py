import backtrader as bt
from quant.strategy.BaseStrategy import BaseStrategy


class RsiCross(BaseStrategy):
    strategy_name = 'RSI 相对强弱指标 (RsiCross)'
    """
    RSI 相对强弱指标策略

    当 RSI 低于超卖线（默认 30）时买入，当 RSI 高于超买线（默认 70）时卖出。
    下单数量由 sizer（默认 DynamicSizer）统一管理，next() 中不传 size。
    """

    params = (
        ('rsi_period', 10),  # RSI 计算周期（优化：14 → 10，更敏感）
        ('rsi_upper', 70),   # 超买阈值
        ('rsi_lower', 30),   # 超卖阈值
    )

    def __init__(self):
        self.order = None
        self.buy_price = None
        self.buy_comm = None

        self.rsi = bt.indicators.RSI(
            self.datas[0].close,
            period=self.params.rsi_period
        )

    def next(self):
        if self.order:
            return

        if not self.position:
            if self.rsi[0] < self.params.rsi_lower:
                self.log(f'BUY CREATE, Price: {self.data.close[0]:.2f}, RSI: {self.rsi[0]:.2f}')
                self.order = self.buy()
        else:
            if self.buy_price is None:
                return
            if self.rsi[0] > self.params.rsi_upper:
                self.log(f'SELL CREATE, Price: {self.data.close[0]:.2f}, RSI: {self.rsi[0]:.2f}')
                self.order = self.sell()
