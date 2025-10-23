from datetime import datetime

import backtrader as bt
import pandas as pd

import akshare as ak
import quant.utils.db_orm as db_orm
from quant.entity.StockHistoryDailyInfoEntity import StockHistoryDailyInfoEntity
from quant.strategy.sma.SmaCross import SmaCross


def strategy_back_trader(symbol: str = "601398", adjust: str = "qfq",
                         fromdate: datetime = datetime(2020, 1, 1),
                         todate: datetime = datetime.now(),
                         startcash: float = 100000,
                         commission: float = 0.0005,
                         strategy=SmaCross, printlog=False, is_plot: bool = False):
    """
     symbol: 股票代码
     fromdate: 回测开始日期
     todate: 回测结束日期
     startcash: 初始资金
     commission: 交易手续费 百分比 0.0005 = 0.05%
     adjust: 复权方式 'qfq' 前复权 'hfq' 后复权 None 不复权
     strategy: 策略类 SmaCross 或 SmaCrossEnhanced
     printlog: 是否打印日志
     is_plot: 是否绘图
    """
    try:
        df = db_orm.get_mysql_data_to_df(orm_class=StockHistoryDailyInfoEntity, adjust=adjust, symbol=symbol)
        if df.empty:
            raise Exception("数据库中无数据")
        df = df.iloc[:, 2:8]
    except:
        print("开始从akshare获取数据并保存到数据库...")
        df = ak.stock_zh_a_hist_orm(symbol=symbol, period="daily", adjust=adjust)
        db_orm.save_to_mysql_orm_incremental(df=df, orm_class=StockHistoryDailyInfoEntity, symbol=symbol, isDel=True)
        df = df.iloc[:, :6]

    # 设置日期为索引
    df.index = pd.to_datetime(df['date'])
    # 同一个策略 执行周期很重要 不同的周期结果可能差异很大
    data = bt.feeds.PandasData(dataname=df, fromdate=fromdate, todate=todate)
    cerebro = bt.Cerebro()
    cerebro.adddata(data)
    cerebro.addstrategy(strategy, printlog=printlog)  # 启用日志打印 调试用
    cerebro.broker.setcommission(commission=commission)
    cerebro.broker.setcash(startcash)
    cerebro.run()
    endcash = cerebro.broker.getvalue()
    pnl = endcash - startcash
    print('--------------------------------')
    print(f'策略名: {strategy.__name__}')
    print(f'股票代码: {symbol}')
    print(f'初始资金: {round(startcash, 2)}')
    print(f'总资金: {round(endcash, 2)}')
    print(f'净收益: {round(pnl, 2)}')
    print(f'收益率: {round((pnl / startcash) * 100, 2)}%')
    if is_plot:
        cerebro.plot(style='candlestick')


if __name__ == '__main__':
    """
    测试均线交叉策略
    """
    strategy_back_trader(strategy=SmaCross)
