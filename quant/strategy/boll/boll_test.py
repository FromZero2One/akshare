import datetime
from datetime import datetime

import backtrader as bt
import pandas as pd

import akshare as ak
import quant.utils.db_orm as db_orm
from quant.entity.StockHistoryDailyInfoEntity import StockHistoryDailyInfoEntity
# 导入类SmaCross 可以直接使用SmaCross策略类
# 导入模块则需要使用模块名.类名  SingleSma.SingleSma
from quant.strategy.boll.BollStrategy import BollStrategy


def bt_test():
    symbol = "601398"
    adjust = "qfq"

    # 从数据库获取数据，如果没有则从 akshare 获取并保存到数据库
    try:
        df = db_orm.get_mysql_data_to_df(orm_class=StockHistoryDailyInfoEntity, adjust=adjust, symbol=symbol)
        df = df.iloc[:, 2:8]
    except:
        df = ak.stock_zh_a_hist_orm(symbol=symbol, adjust=adjust)
        db_orm.save_to_mysql_orm(df=df, orm_class=StockHistoryDailyInfoEntity, reBuild=False)
        df = df.iloc[:, :6]
        print("---------从akshare获取数据------------")
    print(df.head())
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
    start_date = datetime(2025, 1, 1)
    now = datetime.now()
    print(f'------------now----- {now.strftime("%Y-%m-%d %H:%M:%S")}')
    data = bt.feeds.PandasData(dataname=df, fromdate=start_date, todate=now)
    # 初始化cerebro回测系统设置
    cerebro = bt.Cerebro()
    # 将数据传入回测系统
    cerebro.adddata(data)
    # 将交易策略加载到回测系统中
    cerebro.addstrategy(BollStrategy)
    # 设置初始资本为10,000
    startcash = 10000
    cerebro.broker.setcash(startcash)
    # 设置交易手续费为 0.1%
    cerebro.broker.setcommission(commission=0.001)
    # 运行回测系统
    cerebro.run()
    # 获取回测结束后的总资金
    postvalue = cerebro.broker.getvalue()
    pnl = postvalue - startcash
    print(f'净收益: {round(pnl, 2)}')
    # 打印结果
    print(f'总资金: {round(postvalue, 2)}')
    # 绘图
    # cerebro.plot(style='candlestick')


if __name__ == '__main__':
    bt_test()
