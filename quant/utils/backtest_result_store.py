#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2026/5/23
Desc: 回测结果存储工具 - 使用Parquet文件替代数据库存储计算结果

回测结果属于确定性计算产物（相同输入=相同输出），不适合持久化到数据库。
Parquet文件方案：轻量级、跨会话持久、pandas原生支持、增量追加简单。
"""

import os
import logging
from datetime import datetime

import pandas as pd

logger = logging.getLogger(__name__)

# 默认存储路径（data目录下）
DEFAULT_RESULT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "cache")
DEFAULT_RESULT_FILE = os.path.join(DEFAULT_RESULT_DIR, "backtest_results.parquet")

# Parquet文件的列定义（与原BacktestResultEntity字段对齐）
RESULT_COLUMNS = [
    'symbol', 'stock_name', 'strategy_name',
    'initial_cash', 'final_value', 'net_profit', 'returns',
    'commission', 'start_date', 'end_date', 'create_time'
]


def load_results(result_file: str = DEFAULT_RESULT_FILE) -> pd.DataFrame:
    """
    加载已有的回测结果

    Returns:
        pd.DataFrame: 回测结果DataFrame，如果文件不存在则返回空DataFrame
    """
    if os.path.exists(result_file):
        try:
            df = pd.read_parquet(result_file)
            logger.info(f"加载回测结果: {len(df)} 条记录")
            return df
        except Exception as e:
            logger.warning(f"读取回测结果文件失败: {e}, 返回空DataFrame")
            return pd.DataFrame(columns=RESULT_COLUMNS)
    else:
        logger.info("回测结果文件不存在，返回空DataFrame")
        return pd.DataFrame(columns=RESULT_COLUMNS)


def get_exist_symbols(result_file: str = DEFAULT_RESULT_FILE) -> list:
    """
    获取已有回测结果的股票代码列表（用于增量跳过）

    Returns:
        list: 已有回测结果的symbol列表
    """
    df = load_results(result_file)
    if df.empty:
        return []
    return df['symbol'].tolist()


def append_result(
        result_data: dict,
        result_file: str = DEFAULT_RESULT_FILE,
) -> bool:
    """
    追加一条回测结果到Parquet文件

    Args:
        result_data: 回测结果字典，包含 symbol, stock_name, strategy_name 等字段
        result_file: 结果文件路径

    Returns:
        bool: 保存成功返回True
    """
    # 确保目录存在
    os.makedirs(os.path.dirname(result_file), exist_ok=True)

    # 加载已有结果
    df = load_results(result_file)

    # 构造新行
    new_row = pd.DataFrame([result_data])

    # 如果已有该symbol的结果，先删除旧记录再追加（覆盖更新）
    if not df.empty and result_data['symbol'] in df['symbol'].values:
        df = df[df['symbol'] != result_data['symbol']]
        logger.info(f"覆盖更新股票 {result_data['symbol']} 的回测结果")

    # 合并追加
    df = pd.concat([df, new_row], ignore_index=True)

    # 保存
    try:
        df.to_parquet(result_file, index=False)
        logger.info(f"回测结果保存成功: {result_data['symbol']}[{result_data['stock_name']}]")
        return True
    except Exception as e:
        logger.error(f"回测结果保存失败: {e}")
        return False


def remove_result(symbol: str, result_file: str = DEFAULT_RESULT_FILE) -> bool:
    """
    删除指定股票的回测结果（用于重新回测场景）

    Args:
        symbol: 股票代码
        result_file: 结果文件路径

    Returns:
        bool: 删除成功返回True
    """
    df = load_results(result_file)
    if df.empty or symbol not in df['symbol'].values:
        return True  # 不存在也算成功

    df = df[df['symbol'] != symbol]
    try:
        df.to_parquet(result_file, index=False)
        logger.info(f"已删除股票 {symbol} 的回测结果")
        return True
    except Exception as e:
        logger.error(f"删除回测结果失败: {e}")
        return False


def build_result_dict(
        symbol: str, stock_name: str, strategy_name: str,
        initial_cash: float, final_value: float, net_profit: float,
        returns: float, commission: float,
        start_date, end_date,
) -> dict:
    """
    构造回测结果字典（替代原BacktestResultEntity构造）

    Args:
        symbol: 股票代码
        stock_name: 股票名称
        strategy_name: 策略名称
        initial_cash: 初始资金
        final_value: 最终资金
        net_profit: 净收益
        returns: 收益率(%)
        commission: 手续费率
        start_date: 回测开始日期
        end_date: 回测结束日期

    Returns:
        dict: 回测结果字典
    """
    return {
        'symbol': symbol,
        'stock_name': stock_name,
        'strategy_name': strategy_name,
        'initial_cash': round(initial_cash, 2),
        'final_value': round(final_value, 2),
        'net_profit': round(net_profit, 2),
        'returns': round(returns, 2),
        'commission': commission,
        'start_date': start_date,
        'end_date': end_date,
        'create_time': datetime.now(),
    }