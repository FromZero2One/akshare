#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2026/6/5
Desc: 回测执行器 - 负责执行回测逻辑

职责：
  - 单只股票回测
  - 批量股票回测（串行/并行）
  - 回测结果管理
  - 进度监控

设计原则：
  - 单一职责：只负责回测执行，不涉及数据获取
  - 可插拔：支持不同的策略函数
  - 高性能：支持并行化处理
"""

import logging
import time
from typing import Callable, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing

import pandas as pd

from quant.strategy.sma.vectorized_sma_cross import run_vectorized_backtest
from quant.utils.backtest_result_store import get_exist_symbols, remove_result

logger = logging.getLogger(__name__)


class BacktestExecutor:
    """
    回测执行器
    
    支持单只股票和批量股票的回测执行
    """
    
    def __init__(
        self,
        strategy_func: Callable = run_vectorized_backtest,
        re_run_result: bool = True,
    ):
        """
        Args:
            strategy_func: 策略回测函数，默认使用向量化双均线策略
            re_run_result: 是否重新运行已有回测结果的股票
        """
        self.strategy_func = strategy_func
        self.re_run_result = re_run_result
        
        # 缓存已有回测结果的股票
        self._exist_result_symbols = None
    
    def _get_exist_results(self) -> set:
        """获取已有回测结果的股票集合（带缓存）"""
        if self._exist_result_symbols is None:
            self._exist_result_symbols = set(get_exist_symbols())
            logger.info(f"✓ 加载回测结果缓存: {len(self._exist_result_symbols)} 只股票")
        return self._exist_result_symbols
    
    def execute_single(
        self,
        symbol: str,
        stock_name: str,
        history_df: pd.DataFrame,
    ) -> dict:
        """
        执行单只股票回测
        
        Args:
            symbol: 股票代码
            stock_name: 股票名称
            history_df: 历史数据DataFrame
            
        Returns:
            dict with backtest result or error info
            

        """
        try:
            # 检查是否需要重新回测
            exist_results = self._get_exist_results()
            
            if symbol in exist_results:
                if self.re_run_result:
                    logger.info(f"↻ 股票 {symbol}[{stock_name}] 已有回测结果，重新回测")
                    remove_result(symbol)
                else:
                    logger.debug(f"⊘ 股票 {symbol}[{stock_name}] 已有回测结果，跳过")
                    return {'success': False, 'reason': 'already_exists'}
            
            # 执行回测
            logger.info(f"▶ 开始回测 {symbol}[{stock_name}] ({len(history_df)}天数据)")
            t0 = time.time()
            
            result = self.strategy_func(
                df=history_df,
                symbol=symbol,
                stock_name=stock_name,
            )
            
            elapsed = time.time() - t0
            logger.info(f"✓ 回测完成 {symbol}[{stock_name}] ({elapsed*1000:.0f}ms)")
            
            # 更新缓存
            if self._exist_result_symbols is not None:
                self._exist_result_symbols.add(symbol)
            
            return {
                'success': True,
                'symbol': symbol,
                'stock_name': stock_name,
                'result': result,
                'duration_ms': elapsed * 1000,
            }
            
        except Exception as e:
            logger.error(f"✗ 回测失败 {symbol}[{stock_name}]: {e}", exc_info=True)
            return {
                'success': False,
                'reason': f'error: {str(e)}',
            }
    
    def execute_batch_serial(
        self,
        stock_list: pd.DataFrame,
        data_provider,
        progress_callback: Optional[Callable] = None,
    ) -> list[dict]:
        """
        串行执行批量回测
        
        Args:
            stock_list: 股票列表DataFrame (columns: symbol, stock_name)
            data_provider: StockDataProvider实例
            progress_callback: 进度回调函数 callback(current, total, symbol, result)
            
        Returns:
            list of result dicts
            
       
        """
        total = len(stock_list)
        results = []
        
        logger.info(f"开始串行回测 {total} 只股票")
        t_start = time.time()
        
        for index, row in stock_list.iterrows():
            symbol = row['symbol']
            stock_name = row['stock_name']
            current = index + 1
            
            logger.info(f"[{current}/{total}] 处理股票 {symbol}[{stock_name}]")
            
            # 获取历史数据（自动确保数据完整）
            history_df = data_provider.get_history_data(
                symbol=symbol,
                stock_name=stock_name,
                min_days=100
            )
            if history_df is None:
                result = {'success': False, 'symbol': symbol, 'reason': 'insufficient_data'}
                results.append(result)
                if progress_callback:
                    progress_callback(current, total, symbol, result)
                continue
            
            # 执行回测
            result = self.execute_single(symbol, stock_name, history_df)
            results.append(result)
            
            # 进度回调
            if progress_callback:
                progress_callback(current, total, symbol, result)
        
        elapsed = time.time() - t_start
        self._print_summary(results, elapsed)
        
        return results
    
    def execute_batch_parallel(
        self,
        stock_list: pd.DataFrame,
        data_provider,
        max_workers: Optional[int] = None,
        progress_callback: Optional[Callable] = None,
    ) -> list[dict]:
        """
        并行执行批量回测
        
        Args:
            stock_list: 股票列表DataFrame (columns: symbol, stock_name)
            data_provider: StockDataProvider实例
            max_workers: 最大工作线程数，默认CPU核心数
            progress_callback: 进度回调函数 callback(current, total, symbol, result)
            
        Returns:
            list of result dicts
            

        """
        total = len(stock_list)
        
        # 确定并行度
        if max_workers is None:
            max_workers = min(multiprocessing.cpu_count(), 16)
        
        logger.info(f"开始并行回测 {total} 只股票，工作线程数: {max_workers}")
        t_start = time.time()
        
        results = []
        completed = 0
        
        from threading import Lock
        results_lock = Lock()
        
        # 预加载已有回测结果（避免线程竞争）
        exist_results = self._get_exist_results().copy()
        
        def process_stock(symbol: str, stock_name: str) -> dict:
            """处理单只股票（线程函数）"""
            try:
                # 检查是否需要重新回测（在线程内判断，避免重复工作）
                if symbol in exist_results and not self.re_run_result:
                    return {'success': False, 'symbol': symbol, 'reason': 'already_exists'}
                
                # 获取历史数据（自动确保数据完整）
                history_df = data_provider.get_history_data(
                    symbol=symbol,
                    stock_name=stock_name,
                    min_days=100
                )
                if history_df is None:
                    return {'success': False, 'symbol': symbol, 'reason': 'insufficient_data'}
                
                # 执行回测
                return self.execute_single(symbol, stock_name, history_df)
                
            except Exception as e:
                logger.error(f"✗ {symbol} 处理异常: {e}", exc_info=True)
                return {'success': False, 'symbol': symbol, 'reason': f'error: {str(e)}'}
        
        # 使用线程池并行执行
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            
            # 提交所有任务
            for _, row in stock_list.iterrows():
                future = executor.submit(
                    process_stock,
                    row['symbol'],
                    row['stock_name']
                )
                futures[future] = row['symbol']
            
            # 收集结果
            for future in as_completed(futures):
                symbol = futures[future]
                try:
                    result = future.result()
                    with results_lock:
                        results.append(result)
                        completed += 1
                    
                    # 进度回调
                    if progress_callback:
                        progress_callback(completed, total, symbol, result)
                    
                    # 日志输出
                    if result['success']:
                        logger.info(f"✓ [{completed}/{total}] {symbol} 完成")
                    else:
                        logger.debug(f"⊘ [{completed}/{total}] {symbol} 跳过: {result.get('reason')}")
                        
                except Exception as e:
                    logger.error(f"✗ {symbol} 任务异常: {e}")
                    with results_lock:
                        results.append({
                            'success': False,
                            'symbol': symbol,
                            'reason': f'task_error: {str(e)}'
                        })
                        completed += 1
        
        elapsed = time.time() - t_start
        self._print_summary(results, elapsed)
        
        return results
    
    def _print_summary(self, results: list[dict], elapsed: float):
        """打印回测汇总信息"""
        total = len(results)
        success = sum(1 for r in results if r['success'])
        failed = total - success
        
        # 统计跳过原因
        skip_reasons = {}
        for r in results:
            if not r['success'] and 'reason' in r:
                reason = r['reason']
                skip_reasons[reason] = skip_reasons.get(reason, 0) + 1
        
        logger.info("=" * 60)
        logger.info("回测完成汇总")
        logger.info("=" * 60)
        logger.info(f"总股票数: {total}")
        logger.info(f"成功回测: {success}")
        logger.info(f"跳过/失败: {failed}")
        logger.info(f"总耗时: {elapsed:.2f}s")
        logger.info(f"平均速度: {total/elapsed:.2f} 股票/秒")
        
        if skip_reasons:
            logger.info("跳过原因分布:")
            for reason, count in skip_reasons.items():
                logger.info(f"  - {reason}: {count}")
        
        logger.info("=" * 60)


def test_single_backtest():
    """
    测试1：单只股票回测
    
    验证单只股票的回测执行功能
    """
    from quant.data_fetch.stock_data_provider import StockDataProvider
    
    logger = logging.getLogger(__name__)
    logger.info("\n【测试1】单只股票回测（贵州茅台 600519）")
    logger.info("-" * 80)
    
    provider = StockDataProvider(adjust="qfq")
    executor = BacktestExecutor(re_run_result=False)
    
    history_df = provider.get_history_data(
        symbol='600519',
        stock_name='贵州茅台',
        min_days=100
    )
    
    if history_df is not None:
        result = executor.execute_single('600519', '贵州茅台', history_df)
        
        if result['success']:
            logger.info(f"✓ 回测成功")
            logger.info(f"  股票代码: {result['symbol']}")
            logger.info(f"  股票名称: {result['stock_name']}")
            logger.info(f"  耗时: {result['duration_ms']:.0f}ms")
            
            backtest_result = result['result']
            if backtest_result:
                logger.info(f"  初始资金: {backtest_result.get('start_cash', 0):.2f}")
                logger.info(f"  最终资金: {backtest_result.get('final_value', 0):.2f}")
                logger.info(f"  净收益: {backtest_result.get('net_profit', 0):.2f}")
                logger.info(f"  收益率: {backtest_result.get('returns_pct', 0):.2f}%")
        else:
            logger.warning(f"✗ 回测失败: {result.get('reason')}")
    else:
        logger.warning("✗ 无法获取历史数据，跳过单只回测测试")


def test_batch_serial_backtest():
    """
    测试2：批量串行回测
    
    验证多只股票的串行回测执行功能
    """
    from quant.data_fetch.stock_data_provider import StockDataProvider
    
    logger = logging.getLogger(__name__)
    logger.info("\n【测试2】批量串行回测（3只股票）")
    logger.info("-" * 80)
    
    provider = StockDataProvider(adjust="qfq")
    executor = BacktestExecutor(re_run_result=False)
    
    test_stocks = provider.get_stock_name_list(symbols=['601398', '600519', '601399'])
    
    if len(test_stocks) > 0:
        # 定义进度回调函数
        def progress_callback(current, total, symbol, result):
            status = "✓" if result['success'] else "✗"
            logger.info(f"  进度: [{current}/{total}] {symbol} {status}")
        
        serial_results = executor.execute_batch_serial(
            stock_list=test_stocks,
            data_provider=provider,
            progress_callback=progress_callback
        )
        
        # 统计结果
        success_count = sum(1 for r in serial_results if r['success'])
        logger.info(f"\n✓ 串行回测完成: {success_count}/{len(serial_results)} 成功")
    else:
        logger.warning("✗ 无可用股票数据，跳过串行回测测试")


def test_batch_parallel_backtest():
    """
    测试3：批量并行回测
    
    验证多只股票的并行回测执行功能
    """
    from quant.data_fetch.stock_data_provider import StockDataProvider
    
    logger = logging.getLogger(__name__)
    logger.info("\n【测试3】批量并行回测（3只股票，4线程）")
    logger.info("-" * 80)
    
    provider = StockDataProvider(adjust="qfq")
    # 重新创建执行器以清除缓存（模拟新环境）
    executor = BacktestExecutor(re_run_result=False)
    
    test_stocks = provider.get_stock_name_list(symbols=['601398', '600519', '601399'])
    
    if len(test_stocks) > 0:
        # 定义进度回调函数
        def progress_callback(current, total, symbol, result):
            status = "✓" if result['success'] else "✗"
            logger.info(f"  进度: [{current}/{total}] {symbol} {status}")
        
        parallel_results = executor.execute_batch_parallel(
            stock_list=test_stocks,
            data_provider=provider,
            max_workers=4,
            progress_callback=progress_callback
        )
        
        # 统计结果
        success_count = sum(1 for r in parallel_results if r['success'])
        logger.info(f"\n✓ 并行回测完成: {success_count}/{len(parallel_results)} 成功")
    else:
        logger.warning("✗ 无可用股票数据，跳过并行回测测试")


def test_rerun_backtest():
    """
    测试4：重新回测功能
    
    验证对已有回测结果的股票进行重新回测的功能
    """
    from quant.data_fetch.stock_data_provider import StockDataProvider
    
    logger = logging.getLogger(__name__)
    logger.info("\n【测试4】重新回测功能测试")
    logger.info("-" * 80)
    
    provider = StockDataProvider(adjust="qfq")
    executor = BacktestExecutor(re_run_result=True)
    
    history_df = provider.get_history_data(
        symbol='600519',
        stock_name='贵州茅台',
        min_days=100
    )
    
    if history_df is not None:
        logger.info("→ 对已有回测结果的股票进行重新回测...")
        rerun_result = executor.execute_single('600519', '贵州茅台', history_df)
        
        if rerun_result['success']:
            logger.info(f"✓ 重新回测成功")
            logger.info(f"  耗时: {rerun_result['duration_ms']:.0f}ms")
        else:
            logger.info(f"  结果: {rerun_result.get('reason')}")
    else:
        logger.warning("✗ 无法获取历史数据，跳过重新回测测试")


def main():
    """
    BacktestExecutor 功能测试主入口
    
    依次执行4个测试案例：
      1. 单只股票回测
      2. 批量串行回测
      3. 批量并行回测
      4. 回测结果管理测试
    """
    import logging
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    logger.info("=" * 80)
    logger.info("BacktestExecutor 功能测试开始")
    logger.info("=" * 80)
    
    # 执行4个测试案例
    # 单只股票回测
    test_single_backtest()
    # 批量串行回测
    test_batch_serial_backtest()
    # 批量并行回测
    test_batch_parallel_backtest()
    # 覆盖回测结果 通过 BacktestExecutor的re_run_result 参数
    test_rerun_backtest()
    
    # 测试总结
    logger.info("\n" + "=" * 80)
    logger.info("BacktestExecutor 功能测试完成 ✓")
    logger.info("=" * 80)
    logger.info("\n测试覆盖:")
    logger.info("  ✓ 单只股票回测")
    logger.info("  ✓ 批量串行回测")
    logger.info("  ✓ 批量并行回测")
    logger.info("  ✓ 回测结果缓存管理")
    logger.info("  ✓ 重新回测功能")
    logger.info("\n提示: 以上测试展示了 BacktestExecutor 的核心功能")
    logger.info("      实际使用时可根据需求选择串行或并行模式")
    logger.info("=" * 80)


if __name__ == '__main__':
    main()
