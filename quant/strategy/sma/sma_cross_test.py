import time

import quant.utils.db_orm as db_orm
from quant.entity.StockHistoryDailyInfoEntity import StockHistoryDailyInfoEntity
from quant.entity.StockNameEntity import StockNameEntity
from quant.entity.stock_data_save_script import stoch_zh_a_hist_orm_incremental
from quant.strategy.sma.SmaCross import SmaCross
from quant.strategy.sma.SmaStrategyScript import strategy_back_trader

if __name__ == '__main__':
    # 获取所有symbol列表
    adjust = "qfq"  # 复权方式 'qfq' 前复权 'hfq' 后复权 None 不复权
    df_name_list = db_orm.get_mysql_data_to_df(orm_class=StockNameEntity)
    if df_name_list.empty:
        print("没有获取到股票列表")

    # 只拉取股票历史数据 不进行回测
    only_pull = False
    # 是否重新构建回测结果 新添加字段时 只执行一次即可
    reBuildResult = False
    for index, row in df_name_list.iterrows():
        symbol = row['symbol']
        stock_name = row['stock_name']
        history_df = db_orm.get_mysql_data_to_df(orm_class=StockHistoryDailyInfoEntity, symbol=symbol, adjust=adjust)
        # 如果没有历史数据 先拉取数据
        if history_df.empty:
            print(f"股票 {symbol} 没有历史数据,先拉取数据")
            # 最终暂停时间为2秒加上0-2秒的随机值，即2-4秒之间的随机延迟
            time.sleep(2 + int(3 * time.time()) % 3)
            stoch_zh_a_hist_orm_incremental(symbol=symbol, adjust=adjust, isDel=False)
        else:
            if only_pull:
                print(f"股票 {symbol} 已有历史数据,跳过拉取")
                continue
            else:
                print(f"开始回测股票: {symbol}")
                strategy_back_trader(tb_df=history_df, strategy=SmaCross, symbol=symbol, stock_name=stock_name,
                                     adjust=adjust, reBuildResult=reBuildResult)
    print(f"完成回测所有股票")

    # strategy_back_trader(strategy=SmaCross)
