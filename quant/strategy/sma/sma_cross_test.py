import logging
import random
import time

import pandas as pd
from sqlalchemy import text

logger = logging.getLogger(__name__)

import quant.utils.db_orm as db_orm
from quant.utils.db_connection import get_engine
from quant.entity.StockHistoryDailyInfoEntity import StockHistoryDailyInfoEntity
from quant.entity.StockNameEntity import StockNameEntity
from quant.entity.script.stock_data_save_script import stock_zh_a_hist_orm_incremental
from quant.strategy.sma.strategy.SmaCross import SmaCross
from quant.strategy.sma.SmaStrategyScript import strategy_back_trader


def run_strategy(
    adjust: str = "qfq",
    re_run_result: bool = False,
    only_pull: bool = False,
    only_run_result: bool = True,
    re_build_result: bool = False,
):
    # 获取所有symbol列表
    df_name_list = db_orm.get_mysql_data_to_df(orm_class=StockNameEntity)
    if df_name_list.empty:
        logging.warning("没有获取到股票列表")
        return
    #  获取已经存在历史数据的股票列表
    engine = get_engine()
    with engine.connect() as conn:
        exist_name_list = pd.read_sql(
            text("SELECT DISTINCT symbol FROM stock_history_daily_info_entity WHERE adjust=:adjust"),
            con=conn, params={"adjust": adjust}
        )
    # 存在回测结果
    exist_result_list = db_orm.execute_sql_query(f"SELECT DISTINCT symbol FROM backtest_result_entity")
    # 预先提取已存在数据的symbol列表，避免循环内重复计算
    exist_name_list_symbols = exist_name_list['symbol'].tolist()
    exist_result_list_symbols = exist_result_list['symbol'].tolist()
    for index, row in df_name_list.iterrows():
        symbol = row['symbol']
        stock_name = row['stock_name']
        try:
            # 如果没有历史数据 先拉取数据
            if symbol not in exist_name_list_symbols:
                if only_run_result:
                    logging.info(f"股票 {symbol}[{stock_name}] ---没有历史数据,跳过回测")
                    continue
                else:
                    logging.info(f"股票 {symbol}[{stock_name}] +++没有历史数据,先拉取数据")
                    # 随机延迟2-4秒，避免请求过于频繁
                    time.sleep(random.uniform(2, 4))
                    stock_zh_a_hist_orm_incremental(symbol=symbol, adjust=adjust, isDel=False)
            else:
                logging.debug(f"股票 {symbol}[{stock_name}] ---已有历史数据")
                if only_pull:
                    logging.info(f"股票 {symbol}[{stock_name}] ---已有历史数据,跳过拉取")
                    continue
                else:
                    if symbol in exist_result_list_symbols:
                        if re_run_result:
                            logging.info(f"股票 {symbol}[{stock_name}] +++已有回测结果,重新回测")
                            db_orm.execute_sql_delete(
                                "DELETE FROM backtest_result_entity WHERE symbol=:symbol",
                                params={"symbol": symbol}
                            )
                            history_df = db_orm.get_mysql_data_to_df(orm_class=StockHistoryDailyInfoEntity, symbol=symbol,
                                                                     adjust=adjust)
                            strategy_back_trader(tb_df=history_df, strategy=SmaCross, symbol=symbol, stock_name=stock_name,
                                                 adjust=adjust, reBuildResult=re_build_result)
                        else:
                            logging.info(f"股票 {symbol}[{stock_name}] +++已有回测结果,跳过回测")
                    else:
                        logging.info(f"股票 {symbol}[{stock_name}] +++没有回测结果,开始回测")
                        history_df = db_orm.get_mysql_data_to_df(orm_class=StockHistoryDailyInfoEntity, symbol=symbol,
                                                                 adjust=adjust)
                        if len(history_df) < 100:
                            logging.warning(f"股票 {symbol}[{stock_name}] ---历史数据不足100天,跳过回测")
                            continue

                        strategy_back_trader(tb_df=history_df, strategy=SmaCross, symbol=symbol, stock_name=stock_name,
                                             adjust=adjust, reBuildResult=re_build_result)
        except Exception as e:
            logging.error(f"股票 {symbol}[{stock_name}] 处理异常: {e}")
            continue
    logging.info("完成回测所有股票")


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    run_strategy()
