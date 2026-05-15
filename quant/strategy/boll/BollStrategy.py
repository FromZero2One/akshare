import backtrader as bt


class BollStrategy(bt.Strategy):
    strategy_name = '布林线交易策略(BollStrategy)'
    """
    布林线交易策略
    1. 当价格跌破下轨时买入
    2. 当价格突破上轨时卖出
    3. 配合 DynamicSizer 实现动态仓位管理
    """
    params = (
        ('period', 20),       # 布林线周期
        ('devfactor', 2.0),   # 标准差倍数
    )

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None
        
        # 初始化布林线指标
        bb = bt.indicators.BollingerBands(
            self.datas[0], 
            period=self.params.period, 
            devfactor=self.params.devfactor
        )
        self.top = bb.top
        self.bot = bb.bot

    def next(self):
        if self.order:
            return

        if not self.position:
            # 价格跌破下轨，产生买入信号
            if self.dataclose <= self.bot[0]:
                self.order = self.buy()
        else:
            # 价格突破上轨，产生卖出信号
            if self.dataclose >= self.top[0]:
                self.order = self.sell(size=self.position.size)


