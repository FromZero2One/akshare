#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2026/6/5
Desc: 回测结果存储工具 - 使用MySQL数据库存储

回测结果存储在MySQL数据库中，支持增量跳过和覆盖更新。
"""

import logging
from datetime import datetime

import quant.utils.db_orm as db_orm
from quant.entity.BacktestResultEntity import BacktestResultEntity

logger = logging.getLogger(__name__)


def get_exist_symbols() -> list:
    """
    获取已有回测结果的股票代码列表（用于增量跳过）

    Returns:
        list: 已有回测结果的symbol列表
    """
    df = db_orm.get_mysql_data_to_df(orm_class=BacktestResultEntity)
    if df.empty:
        return []
    return df['symbol'].tolist()


def append_result(result_data: dict) -> bool:
    """
    保存或更新一条回测结果到MySQL数据库

    Args:
        result_data: 回测结果字典，包含 symbol, stock_name, strategy_name 等字段

    Returns:
        bool: 保存成功返回True
    """
    try:
        # 检查是否已存在该股票的回测结果
        existing = db_orm.get_mysql_data_to_df(
            orm_class=BacktestResultEntity,
            symbol=result_data['symbol']
        )
        
        if not existing.empty:
            # 覆盖更新：先删除旧记录
            logger.info(f"覆盖更新股票 {result_data['symbol']} 的回测结果")
            db_orm.delete_from_db(
                orm_class=BacktestResultEntity,
                symbol=result_data['symbol']
            )
        
        # 插入新记录
        from quant.entity.BacktestResultEntity import BacktestResultEntity as BRE
        new_record = BRE(
            symbol=result_data['symbol'],
            stock_name=result_data['stock_name'],
            strategy_name=result_data['strategy_name'],
            initial_cash=result_data['initial_cash'],
            final_value=result_data['final_value'],
            net_profit=result_data['net_profit'],
            returns=result_data['returns'],
            commission=result_data['commission'],
            start_date=result_data['start_date'],
            end_date=result_data['end_date'],
            create_time=datetime.now()
        )
        
        db_orm.add_to_db(new_record)
        logger.info(f"回测结果保存成功: {result_data['symbol']}[{result_data['stock_name']}]")
        return True
        
    except Exception as e:
        logger.error(f"回测结果保存失败: {e}", exc_info=True)
        return False


def remove_result(symbol: str) -> bool:
    """
    删除指定股票的回测结果（用于重新回测场景）

    Args:
        symbol: 股票代码

    Returns:
        bool: 删除成功返回True
    """
    try:
        db_orm.delete_from_db(orm_class=BacktestResultEntity, symbol=symbol)
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
    构造回测结果字典

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
    }