#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2026/6/5
Desc: 回测结果存储工具 - 使用MySQL数据库存储

回测结果存储在MySQL数据库中，支持增量跳过和覆盖更新。
"""

import logging
from datetime import datetime

from sqlalchemy.dialects.mysql import insert as mysql_insert

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
    保存或更新一条回测结果到MySQL数据库（原子 upsert）

    依赖 (symbol, strategy_name) 上的唯一键 uk_symbol_strategy：
    - 不存在 → INSERT 新行
    - 已存在 → UPDATE 全部业务字段，保留原 id 与 create_time

    相比旧的 "SELECT → DELETE → INSERT" 三步法：
      ✅ 单次 SQL，单次事务原子完成，无并发竞态
      ✅ 不会因中间失败留下"无记录"窗口

    Args:
        result_data: 回测结果字典，包含 symbol, stock_name, strategy_name 等字段

    Returns:
        bool: 保存成功返回True
    """
    try:
        record = {
            "symbol": result_data['symbol'],
            "stock_name": result_data['stock_name'],
            "strategy_name": result_data['strategy_name'],
            "initial_cash": result_data['initial_cash'],
            "final_value": result_data['final_value'],
            "net_profit": result_data['net_profit'],
            "returns": result_data['returns'],
            "commission": result_data['commission'],
            "start_date": result_data['start_date'],
            "end_date": result_data['end_date'],
            "create_time": datetime.now(),
        }

        # ON DUPLICATE KEY UPDATE：除 create_time 外全部刷新为最新值
        update_cols = {
            "stock_name": record["stock_name"],
            "initial_cash": record["initial_cash"],
            "final_value": record["final_value"],
            "net_profit": record["net_profit"],
            "returns": record["returns"],
            "commission": record["commission"],
            "start_date": record["start_date"],
            "end_date": record["end_date"],
        }
        stmt = mysql_insert(BacktestResultEntity).values(record)
        stmt = stmt.on_duplicate_key_update(**update_cols)

        with db_orm.get_session() as session:
            session.execute(stmt)

        logger.info(
            f"回测结果保存成功: {result_data['symbol']}"
            f"[{result_data['stock_name']}] strategy={result_data['strategy_name']}"
        )
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


def ensure_unique_key() -> bool:
    """
    确保 backtest_result_entity 表存在 (symbol, strategy_name) 唯一键。

    append_result() 的原子 upsert 依赖此唯一键，否则会退化为多次 INSERT。
    本函数是幂等的：唯一键已存在则直接返回 True，不存在则先清理重复行再添加。

    ⚠️  副作用：会删除 (symbol, strategy_name) 重复的行，保留 id 最小的那一条。

    建议用法：
        在生产环境首次部署 upsert 前手动调用一次：
            python -c "from quant.utils.backtest_result_store import ensure_unique_key; ensure_unique_key()"
    """
    from quant.utils.db_orm import get_session
    from sqlalchemy import text

    try:
        with get_session() as s:
            existing = s.execute(text(
                "SELECT COUNT(*) FROM information_schema.statistics "
                "WHERE table_schema=DATABASE() "
                "AND table_name='backtest_result_entity' "
                "AND index_name='uk_symbol_strategy'"
            )).scalar()

            if existing > 0:
                logger.info("✓ 唯一键 uk_symbol_strategy 已存在")
                return True

            # 去重：保留 id 最小行
            dup_count = s.execute(text(
                "SELECT COUNT(*) FROM backtest_result_entity t1 "
                "INNER JOIN backtest_result_entity t2 "
                "ON t1.symbol = t2.symbol AND t1.strategy_name = t2.strategy_name "
                "AND t1.id > t2.id"
            )).scalar()
            if dup_count and dup_count > 0:
                logger.warning(f"清理 {dup_count} 条重复 (symbol, strategy_name) 行")
                s.execute(text(
                    "DELETE t1 FROM backtest_result_entity t1 "
                    "INNER JOIN backtest_result_entity t2 "
                    "ON t1.symbol = t2.symbol AND t1.strategy_name = t2.strategy_name "
                    "AND t1.id > t2.id"
                ))

            s.execute(text(
                "ALTER TABLE backtest_result_entity "
                "ADD UNIQUE KEY uk_symbol_strategy (symbol, strategy_name)"
            ))
            logger.info("✓ 已添加唯一键 uk_symbol_strategy")
        return True
    except Exception as e:
        logger.error(f"添加唯一键失败: {e}", exc_info=True)
        return False