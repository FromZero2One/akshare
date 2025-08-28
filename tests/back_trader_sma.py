# -*- coding:utf-8 -*-
# 导入所需库
from datetime import datetime  # 用于处理日期时间
import backtrader as bt  # Backtrader量化回测框架
import matplotlib.pyplot as plt  # 用于绘图
import akshare as ak  # AKShare金融数据接口库
import pandas as pd  # 数据处理库

# 设置matplotlib支持中文显示
plt.rcParams["axes.unicode_minus"] = False

"""
# 利用 AKShare 获取工商银行(601398)股票的历史后复权数据，这里只获取前7列数据
中石油 601857

"""
stock_hfq_df = ak.stock_zh_a_hist(symbol="601857", adjust="").iloc[:, :7]
print(stock_hfq_df.head())  # 打印数据前5行，检查数据格式
# 删除 `股票代码` 列，因为该列在后续处理中不需要
del stock_hfq_df['股票代码']
# 处理字段命名，以符合 Backtrader 的要求
stock_hfq_df.columns = [
    'date',  # 日期
    'open',  # 开盘价
    'close',  # 收盘价
    'high',  # 最高价
    'low',  # 最低价
    'volume',  # 成交量
]
# 把 date 作为日期索引，以符合 Backtrader 的要求
stock_hfq_df.index = pd.to_datetime(stock_hfq_df['date'])


class MyStrategy(bt.Strategy):
    """
    主策略程序
    """
    params = (("maperiod", 20),)  # 全局设定交易策略的参数

    # 日志输出
    def log(self, close, sma, datatime=None):
        ''' 
        Logging function for this strategy
        记录策略运行日志
        
        Parameters:
        txt (str): 需要记录的日志文本信息
        dt (datetime, optional): 时间戳，默认为None时使用数据源中的当前日期
        '''
        datatime = datatime or self.datas[0].datetime.date(0)
        print('%s, %s, %s' % (datatime, close, sma))

    def __init__(self):
        """
        初始化函数
        初始化策略所需的各种变量和指标
        """
        # 指定价格序列，用于访问收盘价数据  todo 开盘价回测
        self.data_close = self.datas[0].open
        # 初始化交易相关变量
        self.order = None  # 用于跟踪订单状态
        self.buy_price = None  # 记录买入价格
        self.buy_comm = None  # 记录买入手续费
        # 添加移动均线指标，用于生成交易信号
        self.sma = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.params.maperiod
        )

        # To keep track of pending orders
        self.order = None

    def notify_order(self, order):
        print("notify_order")
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log('BUY EXECUTED, %.2f' % order.executed.price)
            elif order.issell():
                self.log('SELL EXECUTED, %.2f' % order.executed.price)

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Write down: no pending order
        self.order = None

    def next(self):
        # 记录当前K线的收盘价
        self.log('Close, %.2f' % self.data_close[0], 'SMA, %.2f' % self.sma[0])
        """
        每个K线周期执行一次交易逻辑判断
        """
        # 检查是否有指令等待执行，如果有则跳过本次执行
        # if self.order:
        #     print("当前有未执行订单，等待执行完成...")
        #     return

        # 买入条件：收盘价上涨突破20日均线
        if self.data_close[0] > self.sma[0]:
            print("买入-----------------")
            # 执行买入操作，买入100股
            self.order = self.buy(size=100)
        else:
            # 检查是否持仓
            if self.position:
                # 有持仓时，判断是否满足卖出条件
                # 卖出条件：收盘价跌破20日均线
                if self.data_close[0] < self.sma[0]:
                    print("卖出..........................")
                    # 执行卖出操作，卖出100股
                    self.order = self.sell(size=100)
            else:
                print("当前无持仓，等待买入机会...")


if __name__ == "__main__":
    # 初始化回测引擎
    cerebro = bt.Cerebro()
    # 设置回测时间范围
    start_date = datetime(2020, 1, 1)  # 回测开始时间
    # end_date = datetime(2025, 8, 20)  # 回测结束时间
    end_date = datetime.now()  # 回测结束时间
    # 创建数据源，使用Pandas数据格式
    data = bt.feeds.PandasData(dataname=stock_hfq_df, fromdate=start_date, todate=end_date)
    # 将自定义策略添加到回测引擎中
    cerebro.addstrategy(MyStrategy)
    # 将数据源添加到回测引擎中
    cerebro.adddata(data)
    # 设置初始资金为1000000
    start_cash = 1000000
    cerebro.broker.setcash(start_cash)
    # 设置交易手续费为0.2%
    cerebro.broker.setcommission(commission=0.002)
    # 运行回测
    cerebro.run()
    # 计算收益情况
    port_value = cerebro.broker.getvalue()  # 获取回测结束后的总资金
    pnl = port_value - start_cash  # 计算净收益

    # 输出回测结果统计
    print(f"初始资金: {start_cash}\n回测期间：{start_date.strftime('%Y%m%d')}:{end_date.strftime('%Y%m%d')}")
    print(f"总资金: {round(port_value, 2)}")
    print(f"净收益: {round(pnl, 2)}")

    # 绘制回测结果图表（可选）
    cerebro.plot(style='candlestick')  # 画图
