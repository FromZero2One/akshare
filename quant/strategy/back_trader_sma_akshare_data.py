import datetime

import pandas as pd

import backtrader as bt
from datetime import datetime
import akshare as ak
from quant.utils.db_orm import get_mysql_data_to_df
from quant.entity.StockHistoryDailyInfoEntity import StockHistoryDailyInfoEntity


class SmaCross(bt.Strategy):
    """
    5日线上穿20日线时买入[快速上穿慢速] 下穿时卖出
    """
    # 全局设定交易策略的参数

    params = (('pfast', 5), ('pslow', 20),)

    def __init__(self):

        sma1 = bt.ind.SMA(period=self.p.pfast)  # fast moving average

        sma2 = bt.ind.SMA(period=self.p.pslow)  # slow moving average

        self.crossover = bt.ind.CrossOver(sma1, sma2)  # crossover signal

    def next(self):

        if self.crossover > 0:  # if fast crosses slow to the upside

            self.close()

            print(self.position)

            self.buy(size=1500)  # enter long

            print("Buy {} shares".format(self.data.close[0]))

            print(self.position)

        elif self.crossover < 0:  # in the market & cross to the downside

            self.close()  # close long position

            print(self.position)

            self.sell(size=1500)

            print("Sale {} shares".format(self.data.close[0]))

            print(self.position)


def bt1():
    # 利用 AKShare 获取股票的后复权数据，这里只获取前 6 列
    symbol = "601398"
    adjust = ""

    # 测试
    # df = get_mysql_data_to_df(orm_class=StockHistoryDailyInfoEntity, adjust="qfq", Ticker=symbol)
    # df = df.iloc[:, 2:8]
    try:
        df = ak.stock_zh_a_hist(symbol=symbol, adjust=adjust)
        df = df.iloc[:, :6]
    except:
        df = get_mysql_data_to_df(orm_class=StockHistoryDailyInfoEntity, adjust=adjust, Ticker=symbol)
        df = df.iloc[:, 2:8]
    print(df.head())  # 打印数据前5行，检查数据格式
    # 处理字段命名，以符合 Backtrader 的要求
    df.columns = [
        'date',
        'open',
        'close',
        'high',
        'low',
        'volume',
    ]
    # 把 date 作为日期索引，以符合 Backtrader 的要求
    df.index = pd.to_datetime(df['date'])
    start_date = datetime(1991, 4, 3)  # 回测开始时间
    end_date = datetime(2022, 6, 16)  # 回测结束时间
    data = bt.feeds.PandasData(dataname=df,
                               fromdate=start_date,
                               todate=end_date)  # 加载数据

    # 初始化cerebro回测系统设置

    cerebro = bt.Cerebro()

    # 将数据传入回测系统

    cerebro.adddata(data)

    # 将交易策略加载到回测系统中

    cerebro.addstrategy(SmaCross)

    # 设置初始资本为10,000

    startcash = 10000

    cerebro.broker.setcash(startcash)

    # 设置交易手续费为 0.1%

    cerebro.broker.setcommission(commission=0.001)

    # 运行回测系统

    cerebro.run()

    # 获取回测结束后的总资金

    portvalue = cerebro.broker.getvalue()

    pnl = portvalue - startcash

    print(f'净收益: {round(pnl, 2)}')

    # 打印结果

    print(f'总资金: {round(portvalue, 2)}')

    cerebro.plot(style='candlestick')


if __name__ == '__main__':
    bt1()
