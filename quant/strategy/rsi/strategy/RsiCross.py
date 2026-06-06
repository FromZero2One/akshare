import backtrader as bt
from quant.strategy.BaseStrategy import BaseStrategy


class RsiCross(BaseStrategy):
    strategy_name = 'RSI 相对强弱指标 (RsiCross)'
    """
    RSI 相对强弱指标策略

    买入：RSI < rsi_lower（超卖）
    卖出：RSI > rsi_upper（超买）OR 止损 OR 止盈

    下单数量由 sizer（默认 DynamicSizer）统一管理，next() 中不传 size。
    """

    params = (
        ('rsi_period', 10),    # RSI 计算周期（优化：14 → 10，更敏感）
        ('rsi_upper', 70),     # 超买阈值
        ('rsi_lower', 30),     # 超卖阈值
        ('stop_loss', 0.05),   # 固定止损百分比 5%
        ('take_profit', 0.10), # 固定止盈百分比 10%
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

        # RSI 暖机期未完成时不交易（前 rsi_period 根 rsi[0] 是 NaN）
        if len(self.rsi) < self.params.rsi_period:
            return

        if not self.position:
            if self.rsi[0] < self.params.rsi_lower:
                self.log(f'BUY CREATE, Price: {self.data.close[0]:.2f}, RSI: {self.rsi[0]:.2f}')
                self.order = self.buy()
        else:
            if self.buy_price is None:
                return
            # 三种平仓信号：RSI 超买 / 止损 / 止盈
            if self.rsi[0] > self.params.rsi_upper:
                self.log(f'SELL CREATE, Price: {self.data.close[0]:.2f}, RSI: {self.rsi[0]:.2f}')
                self.order = self.sell()
            elif self.data.close[0] < self.buy_price * (1.0 - self.params.stop_loss):
                self.log(f'STOP LOSS SELL CREATE, Price: {self.data.close[0]:.2f}')
                self.order = self.sell()
            elif self.data.close[0] > self.buy_price * (1.0 + self.params.take_profit):
                self.log(f'TAKE PROFIT SELL CREATE, Price: {self.data.close[0]:.2f}')
                self.order = self.sell()
