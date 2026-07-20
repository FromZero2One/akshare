#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2026/7/12
Desc: 拉取涨停板行情数据（涨停股池、昨日涨停股池、强势股池、次新股池、炸板股池、跌停股池）
并保存到数据库

数据来源：东方财富网-行情中心-涨停板行情
https://quote.eastmoney.com/ztb/detail#type=ztgc
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from datetime import datetime

import pandas as pd

# 直接从 akshare 模块导入涨停板数据函数
from akshare.stock_feature.stock_ztb_em import (
    stock_zt_pool_em,
    stock_zt_pool_previous_em,
    stock_zt_pool_strong_em,
    stock_zt_pool_sub_new_em,
    stock_zt_pool_zbgc_em,
    stock_zt_pool_dtgc_em,
)
from quant.utils.db_connection import get_engine
from quant.utils.db_orm import save_with_auto_entity, execute_sql_query
from quant.utils.logger_config import get_quant_logger

# 配置日志
logger = get_quant_logger()

# 股票池配置：(函数, 表名, 表注释)
POOL_CONFIGS = [
    (stock_zt_pool_em, "stock_zt_pool_em", "涨停股池"),
    (stock_zt_pool_previous_em, "stock_zt_pool_previous_em", "昨日涨停股池"),
    (stock_zt_pool_strong_em, "stock_zt_pool_strong_em", "强势股池"),
    (stock_zt_pool_sub_new_em, "stock_zt_pool_sub_new_em", "次新股池"),
    (stock_zt_pool_zbgc_em, "stock_zt_pool_zbgc_em", "炸板股池"),
    (stock_zt_pool_dtgc_em, "stock_zt_pool_dtgc_em", "跌停股池"),
]


def _add_date_column(df: pd.DataFrame, date: str) -> pd.DataFrame:
    """
    为 DataFrame 添加日期列，用于标识数据所属交易日

    Args:
        df: 原始数据
        date: 交易日字符串 (格式: YYYYMMDD)

    Returns:
        pd.DataFrame: 添加日期列后的数据
    """
    if df.empty:
        return df
    # 将日期格式化为 YYYY-MM-DD，方便数据库存储和查询
    formatted_date = f"{date[:4]}-{date[4:6]}-{date[6:]}"
    df = df.copy()
    df["date"] = formatted_date
    return df


def _reorder_columns(df: pd.DataFrame, date_first: bool = True) -> pd.DataFrame:
    """
    将 date 列放到第一列，序号放到第二列

    Args:
        df: 原始数据
        date_first: 是否将 date 列放在最前面

    Returns:
        pd.DataFrame: 列重排后的数据
    """
    if df.empty:
        return df
    columns = df.columns.tolist()
    if "date" in columns and date_first:
        columns.remove("date")
        columns = ["date"] + columns
    if "序号" in columns:
        columns.remove("序号")
        # 将序号放在 date 之后
        idx = 1 if date_first and "date" in columns else 0
        columns.insert(idx, "序号")
    return df[columns]


def fetch_and_save_zt_pool(
    date: str,
    pool_func,
    table_name: str,
    table_comment: str,
    reBuild: bool = False,
) -> bool:
    """
    拉取指定股票池数据并保存到数据库

    Args:
        date: 交易日 (格式: YYYYMMDD)
        pool_func: 股票池数据获取函数
        table_name: 数据库表名
        table_comment: 表注释
        reBuild: 是否重建表

    Returns:
        bool: 成功返回 True
    """
    try:
        logger.info(f"正在拉取 {table_comment} ({date}) ...")
        df = pool_func(date=date)

        if df.empty:
            logger.warning(f"{table_comment} ({date}) 无数据")
            return False

        # 添加日期列并重排列
        df = _add_date_column(df, date)
        df = _reorder_columns(df, date_first=True)

        logger.info(f"{table_comment} 获取到 {len(df)} 条记录")

        # 保存到数据库
        success = save_with_auto_entity(
            df=df,
            table_name=table_name,
            reBuild=reBuild,
            table_comment=table_comment,
        )

        if success:
            logger.info(f"✓ {table_comment} ({date}) 数据保存成功 ({len(df)} 条)")
        else:
            logger.error(f"✗ {table_comment} ({date}) 数据保存失败")

        return success

    except Exception as e:
        logger.error(f"✗ {table_comment} ({date}) 处理失败: {e}", exc_info=True)
        return False


def fetch_all_zt_pools(date: str = None, reBuild: bool = False) -> dict:
    """
    拉取所有涨停板股票池数据并保存到数据库

    Args:
        date: 交易日 (格式: YYYYMMDD，默认使用当天)
        reBuild: 是否重建表

    Returns:
        dict: 每个股票池的处理结果 {table_name: success_flag}
    """
    if date is None:
        date = datetime.now().strftime("%Y%m%d")

    logger.info("=" * 60)
    logger.info(f"开始拉取涨停板行情数据 (日期: {date})")
    logger.info("=" * 60)

    results = {}
    for pool_func, table_name, table_comment in POOL_CONFIGS:
        success = fetch_and_save_zt_pool(
            date=date,
            pool_func=pool_func,
            table_name=table_name,
            table_comment=table_comment,
            reBuild=reBuild,
        )
        results[table_name] = success

    # 打印汇总
    logger.info("=" * 60)
    logger.info("拉取结果汇总:")
    for table_name, success in results.items():
        status = "✓" if success else "✗"
        logger.info(f"  {status} {table_name}")
    logger.info("=" * 60)

    return results


def query_last_fetch_date(table_name: str) -> str:
    """
    查询指定表中最新的日期

    Args:
        table_name: 表名

    Returns:
        str: 最新日期 (YYYY-MM-DD)，无数据时返回 None
    """
    try:
        engine = get_engine()
        # 先检查表是否存在，避免首次运行时出现 ERROR 日志
        from sqlalchemy import inspect
        inspector = inspect(engine)
        if table_name not in inspector.get_table_names():
            logger.debug(f"表 {table_name} 尚不存在，跳过日期查询")
            return None

        sql = f"SELECT MAX(date) as latest_date FROM {table_name}"
        df = execute_sql_query(sql)
        if df.empty or df["latest_date"].iloc[0] is None:
            return None
        latest = df["latest_date"].iloc[0]
        if hasattr(latest, "strftime"):
            return latest.strftime("%Y-%m-%d")
        return str(latest)
    except Exception as e:
        logger.debug(f"查询 {table_name} 最新日期失败: {e}")
        return None


def fetch_incremental_zt_pools(date: str = None) -> dict:
    """
    智能增量拉取：仅当数据库中无该日数据时才拉取

    Args:
        date: 交易日 (格式: YYYYMMDD，默认使用当天)

    Returns:
        dict: 处理结果
    """
    if date is None:
        date = datetime.now().strftime("%Y%m%d")

    formatted_date = f"{date[:4]}-{date[4:6]}-{date[6:]}"

    logger.info("=" * 60)
    logger.info(f"智能增量拉取涨停板行情数据 (日期: {date})")
    logger.info("=" * 60)

    results = {}
    for pool_func, table_name, table_comment in POOL_CONFIGS:
        # 查询数据库中该表的最新日期
        latest_date = query_last_fetch_date(table_name)

        if latest_date and latest_date >= formatted_date:
            logger.info(f"→ {table_comment} 已包含 {formatted_date} 数据，跳过")
            results[table_name] = True
            continue

        logger.info(
            f"→ {table_comment} 最新数据: {latest_date or '无数据'}"
            f"，需要拉取 {formatted_date}"
        )

        success = fetch_and_save_zt_pool(
            date=date,
            pool_func=pool_func,
            table_name=table_name,
            table_comment=table_comment,
            reBuild=False,
        )
        results[table_name] = success

    # 打印汇总
    logger.info("=" * 60)
    logger.info("增量拉取结果汇总:")
    for table_name, success in results.items():
        status = "✓" if success else "✗"
        logger.info(f"  {status} {table_name}")
    logger.info("=" * 60)

    return results


def test_fetch():
    """测试: 拉取今日涨停板数据"""
    print("\n" + "=" * 60)
    print("测试: 拉取涨停板行情数据")
    print("=" * 60)

    date = datetime.now().strftime("%Y%m%d")
    print(f"交易日: {date}")

    # 增量模式拉取
    results = fetch_incremental_zt_pools(date=date)

    success_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    print(f"\n结果: {success_count}/{total_count} 个股票池拉取成功")

    return all(results.values())


def main():
    """
    拉取涨停板行情数据 并保存到数据库
    """
    # 默认使用增量模式
    test_fetch()


if __name__ == "__main__":
    main()
