import datetime
from datetime import datetime

import backtrader as bt
import pandas as pd

import akshare as ak
import quant.utils.db_orm as db_orm
from quant.entity.StockHistoryDailyInfoEntity import StockHistoryDailyInfoEntity
# 导入类SmaCross 可以直接使用SmaCross策略类
from quant.strategy.sma.SmaCross import SmaCross
from quant.strategy.sma.SmaCrossEnhanced import SmaCrossEnhanced


def bt_test():
    symbol = "601398"
    adjust = "qfq"

    try:
        df = db_orm.get_mysql_data_to_df(orm_class=StockHistoryDailyInfoEntity, adjust=adjust, symbol=symbol)
        df = df.iloc[:, 2:8]
    except:
        df = ak.stock_zh_a_hist(symbol=symbol, period="daily", adjust=adjust)
        # 如果需要保存到数据库，取消下面的注释
        # db_orm.save_to_mysql_orm(df=df, orm_class=StockHistoryDailyInfoEntity, reBuild=False)
        df = df.iloc[:, :6]

    df.index = pd.to_datetime(df['date'])
    # 同一个策略 执行周期很重要 不同的周期结果可能差异很大
    start_date = datetime(2020, 1, 1)
    now = datetime.now()
    data = bt.feeds.PandasData(dataname=df, fromdate=start_date, todate=now)
    cerebro = bt.Cerebro()
    cerebro.adddata(data)
    cerebro.addstrategy(SmaCrossEnhanced, printlog=True)  # 启用日志打印
    startcash = 100000
    cerebro.broker.setcash(startcash)
    # 设置交易手续费为 0.1%
    cerebro.broker.setcommission(commission=0.001)
    print('初始资金: %.2f' % startcash)
    cerebro.run()
    postvalue = cerebro.broker.getvalue()
    pnl = postvalue - startcash
    print('--------------------------------')
    print(f'净收益: {round(pnl, 2)}')
    print(f'总资金: {round(postvalue, 2)}')
    print(f'收益率: {round(100 * pnl / startcash, 2)}%')
    # 绘图
    cerebro.plot(style='candlestick')


if __name__ == '__main__':
    bt_test()