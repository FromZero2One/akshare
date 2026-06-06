from datetime import datetime

import backtrader as bt
import pandas as pd

import quant.utils.db_orm as db_orm
from quant.data_fetch.stock_data_save_script import stock_zh_a_hist_orm_incremental
from quant.entity.StockHistoryDailyInfoEntity import StockHistoryDailyInfoEntity
from quant.strategy.sma.strategy.SmaCross import SmaCross
from quant.utils.backtest_result_store import append_result, build_result_dict
from quant.utils.logger_config import get_quant_logger
from quant.utils.sizer import DynamicSizer
from quant.utils.visualizer import BacktestVisualizer

logger = get_quant_logger()

REQUIRED_COLUMNS = ['date', 'open', 'close', 'high', 'low', 'volume']


def strategy_back_trader(symbol: str = "601398", stock_name: str = "", adjust: str = "qfq", tb_df: pd.DataFrame | None = None,
                         fromdate: datetime = datetime(2020, 1, 1), todate: datetime = datetime.now(),
                         startcash: float = 100000, commission: float = 0.0005,
                         strategy=SmaCross, printlog=False,
                         is_plot: bool = False, is_save_result: bool = True):
    """
     symbol: 股票代码
     stock_name: 股票名称
     adjust: 复权方式 'qfq' 前复权 'hfq' 后复权 None 不复权
     tb_df: 数据框，如果为None则从数据库或akshare获取数据
     fromdate: 回测开始日期
     todate: 回测结束日期
     startcash: 初始资金
     commission: 交易手续费 百分比 0.0005 = 0.05%
     strategy: 策略类 SmaCross 或 SmaCrossEnhanced
     printlog: 是否打印日志
     is_plot: 是否绘图
    """
    if tb_df is None or tb_df.empty:
        df = db_orm.get_mysql_data_to_df(orm_class=StockHistoryDailyInfoEntity, adjust=adjust, symbol=symbol)
        if df.empty:
            # DB 无数据：走智能增量（自动按 DB 最新日期起拉取，不删旧数据）
            logger.info(f"DB 中无 {symbol}({adjust}) 数据，执行智能增量拉取")
            ok = stock_zh_a_hist_orm_incremental(symbol=symbol, adjust=adjust, isDel=False)
            if not ok:
                raise ValueError(f"无法从 akshare 拉取 {symbol} 数据")
            df = db_orm.get_mysql_data_to_df(orm_class=StockHistoryDailyInfoEntity, adjust=adjust, symbol=symbol)
            if df.empty:
                raise ValueError(f"增量拉取后仍无 {symbol} 数据")
        tb_df = df[REQUIRED_COLUMNS].copy()

    # 设置日期为索引
    tb_df.index = pd.to_datetime(tb_df['date'])
    # 同一个策略 执行周期很重要 不同的周期结果可能差异很大
    data = bt.feeds.PandasData(dataname=tb_df, fromdate=fromdate, todate=todate)
    cerebro = bt.Cerebro()
    cerebro.adddata(data)
    cerebro.addstrategy(strategy, printlog=printlog)  # 启用日志打印 调试用
    
    # 设置动态仓位管理器 (默认使用 80% 资金)
    cerebro.addsizer(DynamicSizer, position_pct=0.8)
    
    cerebro.broker.setcommission(commission=commission)
    cerebro.broker.setcash(startcash)
    
    # 添加观察器以记录每日资产总值
    cerebro.addobserver(bt.observers.Value)
    
    results = cerebro.run()
    # broker.getvalue() 返回的是「现金 + 持仓市值」的总资产，不是剩余现金
    end_value = cerebro.broker.getvalue()
    net_profit = end_value - startcash

    # 计算收益率
    returns_pct = (net_profit / startcash) * 100

    print('--------------------------------')
    print(f'策略名: {strategy.__name__}')
    print(f'股票代码: {symbol}')
    print(f'初始资金: {round(startcash, 2)}')
    print(f'总资金: {round(end_value, 2)}')
    print(f'净收益: {round(net_profit, 2)}')
    print(f'收益率: {round(returns_pct, 2)}%')
    # 绘图
    if is_plot:
        cerebro.plot(style='candlestick')

    if is_save_result:
        result_data = build_result_dict(
            symbol=symbol, stock_name=stock_name, strategy_name=strategy.strategy_name,
            initial_cash=startcash, final_value=end_value, net_profit=net_profit,
            returns=returns_pct, commission=commission,
            start_date=fromdate, end_date=todate,
        )
        append_result(result_data)

    # 绘制回测结果图表
    if is_plot:
        try:
            viz = BacktestVisualizer()
            # 获取策略实例
            strat = results[0]
            # 获取交易记录
            trades = strat.broker.get_trades_history()
            # 获取每日资产价值 (从 observers 中提取)
            portfolio_value = pd.Series(
                [obs[0] for obs in strat.observers.value.get().values], 
                index=pd.to_datetime([dt for dt in strat.observers.value.get().keys()])
            )
            
            viz.plot_strategy_performance(
                df_data=tb_df,
                trades=trades,
                portfolio_value=portfolio_value,
                title=f"{strategy.strategy_name} - {symbol}"
            )
        except Exception as e:
            print(f"⚠️ 绘图失败: {e}")



if __name__ == '__main__':
    """
    测试均线交叉策略
    """
    strategy_back_trader(strategy=SmaCross)
