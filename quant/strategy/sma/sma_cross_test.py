import datetime
from datetime import datetime
import sys

import backtrader as bt
import pandas as pd

import akshare as ak
import quant.utils.db_orm as db_orm
from quant.entity.StockHistoryDailyInfoEntity import StockHistoryDailyInfoEntity
# 导入类SmaCross 可以直接使用SmaCross策略类
from quant.strategy.sma.SmaCross import SmaCross
from quant.strategy.sma.SmaCrossEnhanced import SmaCrossEnhanced


def bt_test():
    """

    """
    symbol = "601398"
    adjust = "qfq"
    try:
        df = db_orm.get_mysql_data_to_df(orm_class=StockHistoryDailyInfoEntity, adjust=adjust, symbol=symbol)
        if df.empty:
            raise Exception("数据库中无数据")
        df = df.iloc[:, 2:8]
    except:
        print("开始从akshare获取数据并保存到数据库...")
        df = ak.stock_zh_a_hist_orm(symbol=symbol, period="daily", adjust=adjust)
        # 使用增量保存方式，避免重复插入数据
        db_orm.save_to_mysql_orm_incremental(df=df, orm_class=StockHistoryDailyInfoEntity, symbol=symbol, isDel=True)
        df = df.iloc[:, :6]

    # 设置日期为索引
    df.index = pd.to_datetime(df['date'])
    # 同一个策略 执行周期很重要 不同的周期结果可能差异很大
    start_date = datetime(2020, 1, 1)
    data = bt.feeds.PandasData(dataname=df, fromdate=start_date, todate=datetime.now())
    cerebro = bt.Cerebro()
    cerebro.adddata(data)
    cerebro.addstrategy(SmaCross, printlog=True)  # 启用日志打印 调试用
    # 设置交易手续费为 0.05%
    cerebro.broker.setcommission(commission=0.0005)
    cerebro.broker.setcash(100000)
    startcash = cerebro.broker.getvalue()
    cerebro.run()
    postvalue = cerebro.broker.getvalue()
    pnl = postvalue - startcash
    print('--------------------------------')
    print(f'策略名: {SmaCross.__name__}')
    print(f'股票代码: {symbol}')
    print(f'初始资金: {round(startcash, 2)}')
    print(f'总资金: {round(postvalue, 2)}')
    print(f'净收益: {round(pnl, 2)}')
    print(f'收益率: {round((pnl / startcash) * 100, 2)}%')
    # 绘图
    # cerebro.plot(style='candlestick')


if __name__ == '__main__':
    bt_test()
