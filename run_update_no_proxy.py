#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2025/1/15
Desc: 禁用系统代理并运行数据更新
"""

import os
import sys

# 禁用所有代理
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''
os.environ['NO_PROXY'] = '*'

print("=" * 70)
print("已禁用系统代理")
print("=" * 70)
print(f"HTTP_PROXY: {os.environ.get('HTTP_PROXY', '未设置')}")
print(f"HTTPS_PROXY: {os.environ.get('HTTPS_PROXY', '未设置')}")
print("=" * 70)

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from quant.entity.script.daily_stock_updater import DailyStockDataUpdater

# 创建更新器并运行
updater = DailyStockDataUpdater(
    adjust="qfq",
    max_workers=3,
    delay_between_requests=0.5,
    isDel=False
)

# 测试模式：只处理5只股票
updater.run(test_mode=True, test_count=5)
