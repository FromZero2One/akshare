import datetime

import backtrader as bt
import pandas as pd
import quant.utils.db_orm as db_orm
from quant.entity.StockHistoryDailyInfoEntity import StockHistoryDailyInfoEntity

import akshare as ak
# 导入我们创建的RSI策略
from quant.strategy.rsi.RSIStrategy import RSIStrategy


def rsi_strategy_test():
    """
    RSI (Relative Strength Index) 相对强弱指数是一个动量指标，用于衡量价格变动的速度和变化。它在0到100之间波动：
    """
    symbol = "600519"  # 贵州茅台
    adjust = "qfq"  # 前复权

    try:
        df = db_orm.get_mysql_data_to_df(orm_class=StockHistoryDailyInfoEntity, adjust=adjust, symbol=symbol)
        if len(df) == 0:
            raise Exception("没有数据")
        df = df.iloc[:, 2:8]
    except:
        df = ak.stock_zh_a_hist_orm(symbol=symbol, adjust=adjust)
        db_orm.save_to_mysql_orm(df=df, orm_class=StockHistoryDailyInfoEntity, reBuild=False)
        df = df.iloc[:, :6]
        print("---------从akshare获取数据------------")

    df['date'] = pd.to_datetime(df['date'])
    # 把 date 作为日期索引，以符合 Backtrader 的要求
    df.set_index('date', inplace=True)
    print(df.head())

    # 创建 cerebro 引擎
    cerebro = bt.Cerebro()
    # 添加策略
    cerebro.addstrategy(RSIStrategy, printlog=True)
    # 添加数据
    start_date = datetime.datetime(2025, 1, 1)
    data = bt.feeds.PandasData(dataname=df, fromdate=start_date, todate=datetime.datetime.now())
    cerebro.adddata(data)
    # 设置初始资金
    cerebro.broker.setcash(100000.0)
    # 设置交易手续费
    cerebro.broker.setcommission(commission=0.001)
    # 设置每笔交易的股数
    cerebro.addsizer(bt.sizers.FixedSize, stake=100)
    # 输出初始资金
    print('初始资金: %.2f' % cerebro.broker.getvalue())
    # 运行回测
    cerebro.run()
    # 输出最终资金
    print('最终资金: %.2f' % cerebro.broker.getvalue())

    # 绘制结果
    cerebro.plot()


if __name__ == "__main__":
    rsi_strategy_test()
