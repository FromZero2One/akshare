import datetime
from datetime import datetime

import backtrader as bt
import pandas as pd

import akshare as ak
import quant.utils.db_orm as db_orm
from quant.entity.StockHistoryDailyInfoEntity import StockHistoryDailyInfoEntity
# 导入使用ta_lib的策略
from quant.strategy.ta_lib.TaLibStrategy import TaLibStrategy


def bt_ta_lib_test():
    """
    使用ta_lib指标的backtrader回测示例
    """
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

    start_date = datetime(2023, 1, 1)
    end_date = datetime(2023, 12, 31)
    data = bt.feeds.PandasData(dataname=df, fromdate=start_date, todate=end_date)

    # 初始化cerebro回测系统设置
    cerebro = bt.Cerebro()

    # 将数据传入回测系统
    cerebro.adddata(data)

    # 将交易策略加载到回测系统中
    cerebro.addstrategy(TaLibStrategy)

    # 设置初始资本为10,000
    startcash = 10000
    cerebro.broker.setcash(startcash)

    # 设置交易手续费为 0.1%
    cerebro.broker.setcommission(commission=0.001)

    # 添加绩效分析器
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')

    # 打印初始资金
    print('初始投资组合价值: %.2f' % cerebro.broker.getvalue())

    # 运行回测系统
    results = cerebro.run()
    
    # 获取回测结束后的总资金
    postvalue = cerebro.broker.getvalue()
    pnl = postvalue - startcash
    
    print('最终投资组合价值: %.2f' % cerebro.broker.getvalue())
    print('净收益: %.2f' % pnl)
    
    # 获取分析器结果
    strat = results[0]
    sharpe = strat.analyzers.sharpe.get_analysis()
    drawdown = strat.analyzers.drawdown.get_analysis()
    trades = strat.analyzers.trades.get_analysis()
    
    print('夏普比率:', sharpe)
    print('最大回撤: %.2f%%' % drawdown.max.drawdown)
    print('交易次数:', trades.total.total if 'total' in trades else 0)

    # 绘图
    cerebro.plot(style='candlestick')


if __name__ == '__main__':
    bt_ta_lib_test()