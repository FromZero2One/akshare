#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2025/1/15
Desc: 每日股票数据增量更新脚本
功能：从数据库获取所有股票代码，批量拉取当日数据并增量保存
"""

import sys
import os
import time
from datetime import datetime
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# 将项目根目录添加到Python路径中
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import akshare as ak
import pandas as pd
from quant.utils.logger_config import get_quant_logger
from quant.utils.db_orm import get_mysql_data_to_df
from quant.entity.StockNameEntity import StockNameEntity
from quant.entity.StockHistoryDailyInfoEntity import StockHistoryDailyInfoEntity
from quant.entity.script.stock_data_save_script import stock_zh_a_hist_orm_incremental

# 配置日志
logger = get_quant_logger()


class DailyStockDataUpdater:
    """每日股票数据增量更新器"""
    
    def __init__(self, adjust: str = "qfq", max_workers: int = 5, 
                 delay_between_requests: float = 0.5, isDel: bool = False,
                 max_retries: int = 3, retry_delay: float = 2.0):
        """
        初始化更新器
        
        Args:
            adjust: 复权类型 (qfq=前复权, hfq=后复权)
            max_workers: 最大并发线程数（建议3-10）
            delay_between_requests: 请求间隔时间（秒），避免API限流
            isDel: 是否删除旧数据
            max_retries: 最大重试次数（默认3次）
            retry_delay: 重试间隔时间（秒，默认2秒）
        """
        self.adjust = adjust
        self.max_workers = max_workers
        self.delay_between_requests = delay_between_requests
        self.isDel = isDel
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # 统计信息
        self.total_count = 0
        self.success_count = 0
        self.failed_count = 0
        self.skipped_count = 0
        self.failed_symbols = []
        
    def get_all_stock_symbols(self) -> List[str]:
        """
        从数据库获取所有股票代码
        
        Returns:
            List[str]: 股票代码列表
        """
        logger.info("正在从数据库获取所有股票代码...")
        
        try:
            df = get_mysql_data_to_df(orm_class=StockNameEntity)
            
            if df is None or df.empty:
                logger.warning("数据库中无股票数据，尝试从AKShare获取...")
                # 如果数据库为空，从AKShare获取
                df = ak.stock_a_indicator_lg(symbol="all")
                logger.info(f"从AKShare获取到 {len(df)} 只股票")
            
            # 提取股票代码列（根据实际字段名调整）
            if 'symbol' in df.columns:
                symbols = df['symbol'].dropna().unique().tolist()
            elif '代码' in df.columns:
                symbols = df['代码'].dropna().unique().tolist()
            else:
                raise ValueError(f"DataFrame中未找到股票代码列，可用列: {df.columns.tolist()}")
            
            self.total_count = len(symbols)
            logger.info(f"✅ 获取到 {self.total_count} 只股票代码")
            
            return symbols
            
        except Exception as e:
            logger.error(f"❌ 获取股票代码失败: {e}", exc_info=True)
            raise
    
    def update_single_stock(self, symbol: str) -> dict:
        """
        更新单只股票数据
        
        Args:
            symbol: 股票代码
            
        Returns:
            dict: 更新结果 {'symbol': str, 'status': str, 'message': str}
        """
        try:
            # 调用增量更新函数（带重试机制）
            success = stock_zh_a_hist_orm_incremental(
                symbol=symbol, 
                adjust=self.adjust, 
                isDel=self.isDel,
                max_retries=self.max_retries,
                retry_delay=self.retry_delay
            )
            
            # 添加延迟，避免API限流
            time.sleep(self.delay_between_requests)
            
            if success:
                return {
                    'symbol': symbol,
                    'status': 'success',
                    'message': '更新成功'
                }
            else:
                return {
                    'symbol': symbol,
                    'status': 'failed',
                    'message': f'重试{self.max_retries}次后仍失败'
                }
            
        except Exception as e:
            logger.error(f"❌ 股票 {symbol} 更新失败: {e}")
            return {
                'symbol': symbol,
                'status': 'failed',
                'message': str(e)
            }
    
    def update_stocks_batch(self, symbols: List[str]) -> dict:
        """
        批量更新股票数据（支持并发）
        
        Args:
            symbols: 股票代码列表
            
        Returns:
            dict: 批量更新结果统计
        """
        logger.info(f"开始批量更新 {len(symbols)} 只股票数据...")
        logger.info(f"并发线程数: {self.max_workers}, 请求间隔: {self.delay_between_requests}秒")
        
        start_time = time.time()
        
        # 使用线程池并发处理
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_symbol = {
                executor.submit(self.update_single_stock, symbol): symbol 
                for symbol in symbols
            }
            
            # 处理完成的任务
            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                
                try:
                    result = future.result()
                    
                    if result['status'] == 'success':
                        self.success_count += 1
                    else:
                        self.failed_count += 1
                        self.failed_symbols.append(symbol)
                        
                except Exception as e:
                    self.failed_count += 1
                    self.failed_symbols.append(symbol)
                    logger.error(f"❌ 股票 {symbol} 处理异常: {e}")
                
                # 显示进度
                processed = self.success_count + self.failed_count
                if processed % 10 == 0 or processed == len(symbols):
                    progress = processed / len(symbols) * 100
                    elapsed = time.time() - start_time
                    eta = elapsed / processed * (len(symbols) - processed) if processed > 0 else 0
                    
                    logger.info(
                        f"📊 进度: {processed}/{len(symbols)} ({progress:.1f}%) | "
                        f"成功: {self.success_count} | 失败: {self.failed_count} | "
                        f"预计剩余: {eta:.0f}秒"
                    )
        
        elapsed_time = time.time() - start_time
        
        # 生成统计报告
        report = {
            'total': len(symbols),
            'success': self.success_count,
            'failed': self.failed_count,
            'elapsed_time': elapsed_time,
            'avg_time_per_stock': elapsed_time / len(symbols) if symbols else 0,
            'failed_symbols': self.failed_symbols[:20]  # 只保留前20个失败的
        }
        
        return report
    
    def print_report(self, report: dict):
        """
        打印更新报告
        
        Args:
            report: 更新结果报告
        """
        logger.info("=" * 70)
        logger.info("📊 每日股票数据更新报告")
        logger.info("=" * 70)
        logger.info(f"总股票数:     {report['total']}")
        logger.info(f"成功更新:     {report['success']} ✅")
        logger.info(f"更新失败:     {report['failed']} ❌")
        logger.info(f"耗时:         {report['elapsed_time']:.2f} 秒")
        logger.info(f"平均速度:     {report['avg_time_per_stock']:.2f} 秒/股")
        logger.info(f"成功率:       {report['success']/report['total']*100:.1f}%")
        
        if report['failed_symbols']:
            logger.warning(f"\n失败的股票示例（前20个）:")
            for i, symbol in enumerate(report['failed_symbols'], 1):
                logger.warning(f"  {i}. {symbol}")
        
        logger.info("=" * 70)
        
        if report['failed'] > 0:
            logger.warning(f"⚠️  有 {report['failed']} 只股票更新失败，请检查日志")
        else:
            logger.info("🎉 所有股票数据更新成功！")
    
    def run(self, test_mode: bool = False, test_count: int = 10):
        """
        执行每日更新任务
        
        Args:
            test_mode: 测试模式（只处理少量股票）
            test_count: 测试模式下的股票数量
        """
        logger.info("=" * 70)
        logger.info("🚀 开始执行每日股票数据增量更新")
        logger.info(f"📅 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"🔧 复权类型: {self.adjust}")
        logger.info(f"🔧 并发线程: {self.max_workers}")
        logger.info(f"🔧 删除旧数据: {self.isDel}")
        logger.info("=" * 70)
        
        try:
            # 1. 获取所有股票代码
            symbols = self.get_all_stock_symbols()
            
            # 测试模式：只处理少量股票
            if test_mode:
                logger.info(f"⚠️  测试模式：仅处理前 {test_count} 只股票")
                symbols = symbols[:test_count]
                self.total_count = len(symbols)
            
            if not symbols:
                logger.error("❌ 未获取到任何股票代码")
                return
            
            # 2. 批量更新
            report = self.update_stocks_batch(symbols)
            
            # 3. 打印报告
            self.print_report(report)
            
            # 4. 保存更新记录
            self.save_update_log(report)
            
        except Exception as e:
            logger.error(f"❌ 更新任务执行失败: {e}", exc_info=True)
            raise
    
    def save_update_log(self, report: dict):
        """
        保存更新日志到文件
        
        Args:
            report: 更新结果报告
        """
        log_file = "quant/logs/daily_update_log.txt"
        
        try:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*70}\n")
                f.write(f"更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"总股票数: {report['total']}\n")
                f.write(f"成功: {report['success']}\n")
                f.write(f"失败: {report['failed']}\n")
                f.write(f"耗时: {report['elapsed_time']:.2f}秒\n")
                f.write(f"成功率: {report['success']/report['total']*100:.1f}%\n")
                
                if report['failed_symbols']:
                    f.write(f"失败股票: {', '.join(report['failed_symbols'][:10])}\n")
                
                f.write(f"{'='*70}\n")
            
            logger.info(f"📝 更新日志已保存到: {log_file}")
            
        except Exception as e:
            logger.error(f"保存更新日志失败: {e}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='每日股票数据增量更新脚本')
    parser.add_argument('--adjust', type=str, default='qfq', 
                       choices=['qfq', 'hfq', ''],
                       help='复权类型: qfq=前复权, hfq=后复权, 空=不复权')
    parser.add_argument('--workers', type=int, default=5,
                       help='并发线程数（默认5，建议3-10）')
    parser.add_argument('--delay', type=float, default=0.5,
                       help='请求间隔时间（秒，默认0.5）')
    parser.add_argument('--isDel', action='store_true',
                       help='是否删除旧数据')
    parser.add_argument('--retries', type=int, default=3,
                       help='最大重试次数（默认3）')
    parser.add_argument('--retry-delay', type=float, default=2.0,
                       help='重试间隔时间（秒，默认2.0）')
    parser.add_argument('--test', action='store_true',
                       help='测试模式（只处理10只股票）')
    parser.add_argument('--test-count', type=int, default=10,
                       help='测试模式下的股票数量（默认10）')
    
    args = parser.parse_args()
    
    # 创建更新器
    updater = DailyStockDataUpdater(
        adjust=args.adjust,
        max_workers=args.workers,
        delay_between_requests=args.delay,
        isDel=args.isDel,
        max_retries=args.retries,
        retry_delay=args.retry_delay
    )
    
    # 执行更新
    updater.run(test_mode=args.test, test_count=args.test_count)


if __name__ == '__main__':
    main()
