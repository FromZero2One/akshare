import logging
import random
import time

logger = logging.getLogger(__name__)

import pandas as pd

import quant.utils.db_orm as db_orm
from quant.entity.StockHistoryDailyInfoEntity import StockHistoryDailyInfoEntity
from quant.entity.StockNameEntity import StockNameEntity
from quant.entity.script.stock_data_save_script import stock_zh_a_hist_orm_incremental
from quant.strategy.sma.vectorized_sma_cross import run_vectorized_backtest
from quant.utils.backtest_result_store import get_exist_symbols, remove_result
from quant.utils.stock_cache import stock_cache


def run_strategy(
        adjust: str = "qfq",
        re_run_result: bool = False,
        only_pull: bool = False,
        symbols: list[str] | None = None,
):
    # 1. 查询所有股票代码
    df_name_list = db_orm.get_mysql_data_to_df(orm_class=StockNameEntity)
    if df_name_list.empty:
        logging.warning("没有获取到股票列表")
        return

    # 如果指定了股票代码集合，则过滤
    if symbols:
        df_name_list = df_name_list[df_name_list['symbol'].isin(symbols)]
        if df_name_list.empty:
            logging.warning(f"指定的股票代码 {symbols} 不在股票列表中")
            return
        logging.info(f"指定回测 {len(df_name_list)} 只股票: {symbols}")

    # 已有历史数据的股票代码（Redis 缓存优先，兜底查 MySQL）
    t0 = time.time()
    cached_df = stock_cache.get("__all_symbols__", "__meta__")
    if cached_df is not None and not cached_df.empty:
        exist_history_symbols = cached_df["symbol"].tolist()
        logging.info(f"✓ Redis 命中: __all_symbols__ ({len(exist_history_symbols)} 只, {(time.time()-t0)*1000:.0f}ms)")
    else:
        exist_history_symbols = db_orm.execute_sql_query(
            f"SELECT DISTINCT symbol FROM stock_history_daily_info_entity WHERE adjust='{adjust}'"
        )['symbol'].tolist()
        logging.info(f"→ MySQL 查询 DISTINCT symbol ({len(exist_history_symbols)} 只, {(time.time()-t0)*1000:.0f}ms)")
        # 回填 Redis 缓存
        if exist_history_symbols:
            stock_cache.put("__all_symbols__", "__meta__", pd.DataFrame({"symbol": exist_history_symbols}))

    # 已有回测结果的股票代码（从Parquet文件读取）
    exist_result_symbols = get_exist_symbols()

    total = len(df_name_list)
    for index, row in df_name_list.iterrows():
        symbol = row['symbol']
        stock_name = row['stock_name']
        logging.info(f"[{index + 1}/{total}] 处理股票 {symbol}[{stock_name}]")
        try:
            # 3. 如果没有历史数据则先拉取
            if symbol not in exist_history_symbols:
                logging.info(f"股票 {symbol}[{stock_name}] 没有历史数据，先拉取")
                time.sleep(random.uniform(2, 4))
                success = stock_zh_a_hist_orm_incremental(symbol=symbol, adjust=adjust, isDel=False)
                if not success:
                    logging.warning(f"股票 {symbol}[{stock_name}] 拉取数据失败，跳过")
                    continue
                # 拉取成功后加入已有数据列表，后续不再重复拉取
                exist_history_symbols.append(symbol)

            # only_pull模式下只拉取数据不回测
            if only_pull:
                logging.info(f"股票 {symbol}[{stock_name}] 仅拉取模式，跳过回测")
                continue

            # 2. 查询历史数据跑策略
            if symbol in exist_result_symbols:
                if re_run_result:
                    logging.info(f"股票 {symbol}[{stock_name}] 已有回测结果，重新回测")
                    remove_result(symbol)
            else:
                logging.info(f"股票 {symbol}[{stock_name}] 没有回测结果，开始回测")

            history_df = db_orm.get_mysql_data_to_df(
                orm_class=StockHistoryDailyInfoEntity, symbol=symbol, adjust=adjust
            )
            if len(history_df) < 100:
                logging.warning(f"股票 {symbol}[{stock_name}] 历史数据不足100天，跳过回测")
                continue

            run_vectorized_backtest(
                df=history_df,
                symbol=symbol, stock_name=stock_name,
            )
        except Exception as e:
            logging.error(f"股票 {symbol}[{stock_name}] 处理异常: {e}")
            continue
    logging.info("完成回测所有股票")


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    # 全量回测
    # run_strategy()

    # 指定股票回测
    run_strategy(symbols=['601398', '600519', '000001'])
