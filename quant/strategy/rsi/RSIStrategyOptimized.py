import backtrader as bt
from quant.strategy.BaseStrategy import BaseStrategy


class RSIStrategyOptimized(BaseStrategy):
    strategy_name = 'RSI相对强弱指标(优化版)'
    """
    RSI 相对强弱指标交易策略 - 优化版

    优化点:
      1. 使用更敏感的 RSI 周期（10 而非 14）
      2. 放宽超买超卖阈值（75/25 而非 70/30）
      3. 增加 SMA(20) 趋势过滤
      4. 仓位管理由 sizer（默认 DynamicSizer）统一处理，next() 中不传 size
    """

    params = (
        ('rsi_period', 10),      # RSI 周期
        ('rsi_upper', 75),       # 超买阈值
        ('rsi_lower', 25),       # 超卖阈值
        ('sma_period', 20),      # 趋势过滤均线周期
    )

    def __init__(self):
        self.order = None
        self.buy_price = None
        self.buy_comm = None

        self.rsi = bt.indicators.RSI(
            self.datas[0].close,
            period=self.params.rsi_period
        )
        self.sma_trend = bt.indicators.SimpleMovingAverage(
            self.datas[0].close,
            period=self.params.sma_period
        )

    def next(self):
        if self.order:
            return

        current_price = self.data.close[0]

        if not self.position:
            # 买入：RSI 超卖 AND 价格在趋势均线上方
            if self.rsi[0] < self.params.rsi_lower and current_price > self.sma_trend[0]:
                self.log(f'BUY CREATE, Price: {current_price:.2f}, RSI: {self.rsi[0]:.2f}')
                self.order = self.buy()
        else:
            if self.buy_price is None:
                return
            # 卖出：RSI 超买 OR 跌破趋势均线
            if self.rsi[0] > self.params.rsi_upper or current_price < self.sma_trend[0]:
                self.log(f'SELL CREATE, Price: {current_price:.2f}, RSI: {self.rsi[0]:.2f}')
                self.order = self.sell(size=self.position.size)
