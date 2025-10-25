import backtrader as bt


class CloseThanSma(bt.Strategy):
    strategy_name = '收盘大于20sma策略(CloseThanSma)'
    """
    收盘价大于20日线时买入 小于20日线卖出
    """
    params = (("maperiod", 20),)  # 全局设定交易策略的参数 20日线

    # 日志输出
    def log(self, close, sma, datatime=None):
        '''
        记录策略运行日志
        txt (str): 需要记录的日志文本信息
        dt (datetime, optional): 时间戳，默认为None时使用数据源中的当前日期
        '''
        datatime = datatime or self.datas[0].datetime.date(0)
        print('%s, %s, %s' % (datatime, close, sma))

    def __init__(self):
        """
        初始化策略所需的各种变量和指标
        """
        # 指定价格序列，用于访问收盘价数据
        self.data_close = self.datas[0].close
        # 初始化交易相关变量
        self.order = None  # 用于跟踪订单状态
        self.buy_price = None  # 记录买入价格
        self.buy_comm = None  # 记录买入手续费
        # 添加移动均线指标，用于生成交易信号 ExponentialMovingAverage
        self.sma = bt.indicators.SmoothedMovingAverage(
            self.datas[0], period=self.params.maperiod
        )

        # To keep track of pending orders
        self.order = None

    def next(self):
        # 记录当前K线的收盘价
        self.log('Close, %.2f' % self.data_close[0], 'SMA, %.2f' % self.sma[0])
        """
        每个K线周期执行一次交易逻辑判断
        # 买入条件：收盘价上涨突破20日均线
        """
        if self.data_close[0] > self.sma[0]:
            self.order = self.buy(size=1000)
        else:
            # 检查是否持仓
            if self.position:
                # 有持仓时，判断是否满足卖出条件 , 卖出条件：收盘价跌破20日均线
                if self.data_close[0] < self.sma[0]:
                    self.order = self.sell(size=1000)
            else:
                print("当前无持仓，等待买入机会...")
