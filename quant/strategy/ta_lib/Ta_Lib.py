import pandas as pd
from talib import *

import akshare as ak
import quant.utils.db_orm as db_orm
from quant.entity.StockHistoryDailyInfoEntity import StockHistoryDailyInfoEntity


def test_ta_lib():
    """
    测试 TA-Lib 技术指标计算功能。
    https://ta-lib.github.io/ta-lib-python/

    """
    symbol = "601398"
    adjust = "qfq"

    try:
        df = db_orm.get_mysql_data_to_df(orm_class=StockHistoryDailyInfoEntity, adjust=adjust, symbol=symbol)
        df = df.iloc[:, 2:8]
    except:
        df = ak.stock_zh_a_hist_orm(symbol=symbol, adjust=adjust)
        db_orm.save_to_mysql_orm(df=df, orm_class=StockHistoryDailyInfoEntity, reBuild=False)
        df = df.iloc[:, :6]
        print("---------从akshare获取数据------------")
    print(df.head())
    # 重命名字段命名，以符合Backtrader的要求
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

    # 计算简单移动平均线（SMA）
    sma = SMA(df['close'], timeperiod=20)
    print("SMA:", sma)

    # 计算相对强弱指数（RSI）
    rsi = RSI(df['close'], timeperiod=14)
    print("RSI:", rsi)

    # 计算布林带（Bollinger Bands）
    upperband, middleband, lowerband = BBANDS(df['close'], timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)
    print("Upper Band:", upperband)
    print("Middle Band:", middleband)
    print("Lower Band:", lowerband)
    # 计算移动平均收敛散度指标（MACD）
    macd, macdsignal, macdhist = MACD(df['close'], fastperiod=12, slowperiod=26, signalperiod=9)
    print("MACD:", macd)
    print("MACD Signal:", macdsignal)
    print("MACD Hist:", macdhist)

    import matplotlib
    matplotlib.use('TkAgg')  # 或 'Qt5Agg'
    import matplotlib.pyplot as plt

    # 指定图形大小 12英寸，高度为10英寸
    plt.figure(figsize=(12, 10))

    # 绘制收盘价和SMA 3行1列的第1个子图
    plt.subplot(3, 1, 1)
    plt.plot(df['date'], df['close'], label='Close Price')
    plt.plot(df['date'], sma, label='SMA 20')
    plt.title('Stock Price with SMA')
    plt.legend()

    """
       第一个参数 3: 表示图形被划分为3行
       第二个参数 2: 表示图形被划分为2列
       第三个参数 2: 表示当前操作的是第2个子图区域（按从左到右、从上到下的顺序编号）
       [1] [2]
       [3] [4]
       [5] [6]

       """
    plt.subplot(3, 2, 2)
    plt.plot(df['date'], rsi, label='RSI')
    plt.title('RSI Indicator')
    plt.legend()

    # 绘制MACD 3行1列的第3个子图
    plt.subplot(3, 1, 3)
    plt.plot(df['date'], macd, label='macd')
    plt.title('macd ')
    plt.legend()

    # 最后使用tight_layout自动调整子图间距
    plt.tight_layout()
    plt.show()


if __name__ == '__main__':
    test_ta_lib()
