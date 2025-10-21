import backtrader as bt


class SmaCross(bt.Strategy):
    """
    5日线上穿20日线时买入[快速上穿慢速] 下穿时卖出
    """
    # 全局设定交易策略的参数
    params = (('pfast', 5), ('pslow', 20),)

    def __init__(self):

        smaFast = bt.ind.MovingAverageSimple(period=self.p.pfast)  # fast moving average
        smaLow = bt.ind.SMA(period=self.p.pslow)  # slow moving average
        self.crossover = bt.ind.CrossOver(smaFast, smaLow)  # crossover signal

    def next(self):

        if self.crossover > 0:  # 快线上穿慢线，产生买入信号
            self.close()  # 先执行self.close()平掉可能的空头仓位
            print("---- buy前仓位情况=={}", self.position)
            self.buy(size=1000)  # 建立多头仓位
            print("Buy {} shares".format(self.data.close[0]))
            print("----buy后仓位情况=={}", self.position)

        elif self.crossover < 0:  # 快线下穿慢线，产生卖出信号

            self.close()  # 平掉多头仓位
            print("---- sell前仓位情况=={}", self.position)
            self.sell(size=1000)  # 建立空头仓位
            print("Sale {} shares".format(self.data.close[0]))
            print("----sell后仓位情况=={}", self.position)
