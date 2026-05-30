#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2026/5/30
Desc: 多策略向量化回测统一入口

同时测试 SmaCross、RSI、Bollinger、RSI+MACD 四种策略。
所有策略共享 Redis 缓存，数据获取耗时不计入回测耗时。

用法示例：
    # 指定股票 + 指定策略
    python3 all_strategies_test.py --symbols 601398 --strategies sma,rsi

    # 全量股票 + 全部策略
    python3 all_strategies_test.py --symbols 601398,600519,000001

    # 命令行参数说明
    python3 all_strategies_test.py --help
"""

import argparse
import logging
import time

import pandas as pd

import quant.utils.db_orm as db_orm
from quant.entity.StockHistoryDailyInfoEntity import StockHistoryDailyInfoEntity
from quant.entity.StockNameEntity import StockNameEntity
from quant.strategy.boll.vectorized_boll import run_vectorized_backtest as boll_backtest
from quant.strategy.rsi.vectorized_rsi import run_vectorized_backtest as rsi_backtest
from quant.strategy.sma.vectorized_sma_cross import run_vectorized_backtest as sma_backtest
from quant.strategy.ta_lib.vectorized_ta_lib import run_vectorized_backtest as ta_lib_backtest
from quant.utils.stock_cache import stock_cache

logger = logging.getLogger(__name__)

# 已注册的策略
STRATEGIES = {
    "sma": {
        "name": "SmaCross (向量化)",
        "func": sma_backtest,
        "params": {"pfast": 7, "pslow": 30, "stop_loss": 0.05, "take_profit": 0.15},
    },
    "rsi": {
        "name": "RSI (向量化)",
        "func": rsi_backtest,
        "params": {"rsi_period": 10, "rsi_upper": 75, "rsi_lower": 25, "sma_period": 20},
    },
    "boll": {
        "name": "Bollinger (向量化)",
        "func": boll_backtest,
        "params": {"period": 20, "devfactor": 2.0},
    },
    "talib": {
        "name": "RSI+MACD (向量化)",
        "func": ta_lib_backtest,
        "params": {
            "rsi_period": 14,
            "macd_fast": 12,
            "macd_slow": 26,
            "macd_signal": 9,
            "rsi_upper": 70,
            "rsi_lower": 30,
        },
    },
}


def run_all_strategies(
    symbols: list[str] | None = None,
    strategies: list[str] | None = None,
):
    """批量运行多个策略的回测"""

    if strategies is None:
        strategies = list(STRATEGIES.keys())

    selected = {k: v for k, v in STRATEGIES.items() if k in strategies}
    if not selected:
        logger.error(f"未找到有效策略: {strategies}，可选: {list(STRATEGIES.keys())}")
        return

    # -- 查询股票列表 --
    t0 = time.time()
    df_name_list = db_orm.get_mysql_data_to_df(orm_class=StockNameEntity)
    if df_name_list.empty:
        logger.warning("没有获取到股票列表")
        return

    if symbols:
        df_name_list = df_name_list[df_name_list["symbol"].isin(symbols)]
        if df_name_list.empty:
            logger.warning(f"指定的股票代码 {symbols} 不在股票列表中")
            return
    logger.info(f"股票列表: {len(df_name_list)} 只 ({time.time()-t0:.2f}s)")

    # -- 缓存 DISTINCT symbol（复用 SmaCross 的缓存键） --
    cached_df = stock_cache.get("__all_symbols__", "__meta__")
    if cached_df is not None and not cached_df.empty:
        exist_history_symbols = set(cached_df["symbol"].tolist())
    else:
        exist_history_symbols = set(
            db_orm.execute_sql_query(
                "SELECT DISTINCT symbol FROM stock_history_daily_info_entity WHERE adjust='qfq'"
            )["symbol"].tolist()
        )
        stock_cache.put("__all_symbols__", "__meta__", pd.DataFrame({"symbol": list(exist_history_symbols)}))

    # -- 逐个股票运行选定策略 --
    total_ok, total_fail = 0, 0
    total_start = time.time()

    for _, row in df_name_list.iterrows():
        symbol = row["symbol"]
        stock_name = row["stock_name"]

        if symbol not in exist_history_symbols:
            continue

        history_df = db_orm.get_mysql_data_to_df(
            orm_class=StockHistoryDailyInfoEntity, symbol=symbol, adjust="qfq"
        )
        if len(history_df) < 100:
            continue

        for sk, sv in selected.items():
            try:
                sv["func"](
                    df=history_df,
                    symbol=symbol,
                    stock_name=stock_name,
                    **sv["params"],
                )
                total_ok += 1
            except Exception as e:
                logger.error(f"{sv['name']} {symbol} 失败: {e}")
                total_fail += 1

    elapsed = time.time() - total_start
    logger.info(
        f"完成: 成功 {total_ok}, 失败 {total_fail}, 耗时 {elapsed:.2f}s"
    )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    parser = argparse.ArgumentParser(description="多策略向量化回测")
    parser.add_argument(
        "--symbols",
        type=str,
        default="601398,600519,000001",
        help="股票代码，逗号分隔（默认 601398,600519,000001）",
    )
    parser.add_argument(
        "--strategies",
        type=str,
        default="sma,rsi,boll,talib",
        help="策略名，逗号分隔，可选: sma,rsi,boll,talib（默认全部）",
    )
    args = parser.parse_args()

    run_all_strategies(
        symbols=args.symbols.split(",") if args.symbols else None,
        strategies=args.strategies.split(",") if args.strategies else None,
    )
