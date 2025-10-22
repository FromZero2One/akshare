import backtrader as bt


class Boll_strategy(bt.Strategy):
    """
    布林线交易策略
    1. 当价格跌破下轨时买入
    2. 当价格突破上轨时卖出
    3. 每次买入或卖出1800手
    4. 使用默认的20日布林线周期
    """
    params = (('size', 1800),)

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None
        self.buyprice = None
        self.buycomm = None
        # 使用自带的indicators中自带的函数计算出支撑线和压力线，period设置周期，默认是20
        self.lines.top = bt.indicators.BollingerBands(self.datas[0], period=20).top
        self.lines.bot = bt.indicators.BollingerBands(self.datas[0], period=20).bot

    def next(self):
        if not self.position:
            if self.dataclose <= self.lines.bot[0]:
                # 执行买入
                self.order = self.buy(size=self.params.size)
            else:
                if self.dataclose >= self.lines.top[0]:
                    # 执行卖出
                    self.order = self.sell(size=self.params.size)


