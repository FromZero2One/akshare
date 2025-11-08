import time

import quant.utils.db_orm as db_orm
from quant.entity.StockHistoryDailyInfoEntity import StockHistoryDailyInfoEntity
from quant.entity.StockNameEntity import StockNameEntity
from quant.entity.script.stock_data_save_script import stoch_zh_a_hist_orm_incremental
from quant.strategy.sma.SmaCross import SmaCross
from quant.strategy.sma.SmaStrategyScript import strategy_back_trader


def save_stock_history(adjust: str = "qfq"):
    """
    获取所有股票列表
    """
    df_name_list = db_orm.get_mysql_data_to_df(orm_class=StockNameEntity)
    if df_name_list.empty:
        print("没有获取到股票列表")
        return
    #  获取已经存在历史数据的股票列表
    exist_name_list = db_orm.execute_sql_query(f"SELECT DISTINCT symbol FROM stock_history_daily_info_entity")

    not_exist_name_list = df_name_list[~df_name_list['symbol'].isin(exist_name_list['symbol'])]
    print(f"获取股票列表完成,共有 {len(not_exist_name_list)} 个股票没有历史数据")
    for index, row in not_exist_name_list.iterrows():
        symbol = row['symbol']
        stock_name = row['stock_name']
        print(f"股票 {symbol}[{stock_name}] +++没有历史数据,先拉取数据")
        # 获取股票历史数据
        # 最终暂停时间为2秒加上0-2秒的随机值，即2-4秒之间的随机延迟
        time.sleep(2 + int(3 * time.time()) % 3)
        stoch_zh_a_hist_orm_incremental(symbol=symbol, adjust=adjust, isDel=False)


def run_strategy(adjust: str = "qfq"):
    # 所有股票
    df_name_list = db_orm.get_mysql_data_to_df(orm_class=StockNameEntity)
    # 存在回测结果
    exist_result_list = db_orm.execute_sql_query(f"SELECT DISTINCT symbol FROM backtest_result_entity")

    not_exist_result_list = df_name_list[~df_name_list['symbol'].isin(exist_result_list['symbol'])]
    print(f"获取股票列表完成,共有 {len(not_exist_result_list)} 个股票没有回测结果")
    for index, row in not_exist_result_list.iterrows():
        symbol = row['symbol']
        stock_name = row['stock_name']
        reBuildResult = False
        print(f"股票 {symbol}[{stock_name}] +++没有回测结果,开始回测")
        history_df = db_orm.get_mysql_data_to_df(orm_class=StockHistoryDailyInfoEntity, symbol=symbol, adjust=adjust)
        if len(history_df) < 100:
            print(f"股票 {symbol}[{stock_name}] ---历史数据不足100天,跳过回测")
            continue

        strategy_back_trader(tb_df=history_df, strategy=SmaCross, symbol=symbol, stock_name=stock_name,
                             adjust=adjust, reBuildResult=reBuildResult)


if __name__ == '__main__':
    # 拉趣并保持没历史数据的股票数据
    save_stock_history()
    # 回测没回测结果的股票
    # run_strategy()
