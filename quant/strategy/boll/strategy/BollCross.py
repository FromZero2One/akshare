import backtrader as bt
from quant.strategy.BaseStrategy import BaseStrategy


class BollCross(BaseStrategy):
    strategy_name = '布林线交易策略 (BollCross)'
    """
    布林线交易策略

      1. 当价格跌破下轨时买入
      2. 当价格突破上轨时卖出
      3. 仓位管理由 sizer（默认 DynamicSizer）统一处理，next() 中不传 size
    """

    params = (
        ('period', 20),       # 布林线周期
        ('devfactor', 2.0),   # 标准差倍数
    )

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None
        self.buy_price = None
        self.buy_comm = None

        bb = bt.indicators.BollingerBands(
            self.datas[0],
            period=self.params.period,
            devfactor=self.params.devfactor
        )
        self.top = bb.top
        self.bot = bb.bot
        self.mid = bb.mid

    def next(self):
        if self.order:
            return

        if not self.position:
            if self.dataclose[0] <= self.bot[0]:
                self.log(f'BUY CREATE, Price: {self.dataclose[0]:.2f}, Bot: {self.bot[0]:.2f}')
                self.order = self.buy()
        else:
            if self.buy_price is None:
                return
            if self.dataclose[0] >= self.top[0]:
                self.log(f'SELL CREATE, Price: {self.dataclose[0]:.2f}, Top: {self.top[0]:.2f}')
                self.order = self.sell(size=self.position.size)
