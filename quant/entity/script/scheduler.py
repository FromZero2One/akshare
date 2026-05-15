#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2025/1/15
Desc: 定时任务调度器 - 每日自动更新股票数据
使用APScheduler实现定时任务
"""

import sys
import os
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

# 将项目根目录添加到Python路径中
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from quant.utils.logger_config import get_quant_logger
from quant.entity.script.daily_stock_updater import DailyStockDataUpdater

# 配置日志
logger = get_quant_logger()


def daily_update_job():
    """每日更新任务"""
    logger.info("=" * 70)
    logger.info("⏰ 定时任务触发：开始执行每日股票数据更新")
    logger.info(f"📅 执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 70)
    
    try:
        # 创建更新器（生产环境配置）
        updater = DailyStockDataUpdater(
            adjust="qfq",              # 前复权
            max_workers=5,             # 5个并发线程
            delay_between_requests=0.5, # 0.5秒间隔
            isDel=False                # 不删除旧数据
        )
        
        # 执行更新（非测试模式）
        updater.run(test_mode=False)
        
        logger.info("✅ 定时任务执行完成")
        
    except Exception as e:
        logger.error(f"❌ 定时任务执行失败: {e}", exc_info=True)


def test_update_job():
    """测试更新任务（少量股票）"""
    logger.info("=" * 70)
    logger.info("🧪 测试任务触发：开始执行测试更新")
    logger.info(f"📅 执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 70)
    
    try:
        # 创建更新器（测试环境配置）
        updater = DailyStockDataUpdater(
            adjust="qfq",
            max_workers=2,
            delay_between_requests=0.3,
            isDel=False
        )
        
        # 执行更新（测试模式，只处理10只股票）
        updater.run(test_mode=True, test_count=10)
        
        logger.info("✅ 测试任务执行完成")
        
    except Exception as e:
        logger.error(f"❌ 测试任务执行失败: {e}", exc_info=True)


def setup_scheduler():
    """设置定时任务调度器"""
    scheduler = BlockingScheduler()
    
    # 添加每日更新任务
    # 交易日下午4点执行（A股收盘后）
    scheduler.add_job(
        func=daily_update_job,
        trigger=CronTrigger(day_of_week='mon-fri', hour=16, minute=0),
        id='daily_stock_update',
        name='每日股票数据更新',
        replace_existing=True,
        misfire_grace_time=3600  # 错过执行时间的容忍度（1小时）
    )
    
    # 添加测试任务（每小时的第30分钟执行，用于验证）
    # 生产环境建议注释掉此任务
    scheduler.add_job(
        func=test_update_job,
        trigger=CronTrigger(minute=30),
        id='test_stock_update',
        name='测试股票数据更新',
        replace_existing=True
    )
    
    logger.info("=" * 70)
    logger.info("⏰ 定时任务调度器已启动")
    logger.info("=" * 70)
    logger.info("📅 每日更新任务: 周一至周五 16:00")
    logger.info("🧪 测试任务: 每小时 :30 执行")
    logger.info("=" * 70)
    logger.info("按 Ctrl+C 停止调度器...")
    
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("⏹️  调度器已停止")


if __name__ == '__main__':
    setup_scheduler()
