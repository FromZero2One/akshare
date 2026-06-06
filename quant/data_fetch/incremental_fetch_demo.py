#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2026/6/5
Desc: 增量拉取单只股票历史数据


"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from quant.utils.db_orm import get_latest_date_from_db
from quant.data_fetch.stock_data_save_script import stock_zh_a_hist_orm_incremental
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_incremental_fetch():
    """测试智能增量拉取"""
    print("\n" + "=" * 60)
    print("测试: 智能增量拉取数据")
    print("=" * 60)

    symbol = "000007"
    adjust = "qfq"

    # 先查询当前最新日期
    before_latest = get_latest_date_from_db(symbol=symbol, adjust=adjust)
    print(f"拉取前最新日期: {before_latest or '无数据'}")

    # 执行增量拉取
    logger.info(f"\n开始测试增量拉取 {symbol}...")
    success = stock_zh_a_hist_orm_incremental(
        symbol=symbol,
        adjust=adjust,
        isDel=False  # 关键:使用增量模式
    )

    if success:
        print(f"✓ 增量拉取成功")

        # 查询拉取后的最新日期
        after_latest = get_latest_date_from_db(symbol=symbol, adjust=adjust)
        print(f"拉取后最新日期: {after_latest or '无数据'}")

        if before_latest != after_latest:
            print(f"✓ 数据已更新: {before_latest} → {after_latest}")
        else:
            print(f"→ 数据已是最新,无需更新")
    else:
        print(f"✗ 增量拉取失败")

    return success


def main():
    test_incremental_fetch()


if __name__ == '__main__':
    main()
