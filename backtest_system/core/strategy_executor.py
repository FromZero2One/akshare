#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
策略执行器 - 管理策略的注册、加载和执行
"""

import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
from typing import Dict, List, Any, Optional, Type
import importlib
import inspect
from pathlib import Path

from .data_fetcher import DataFetcher
from strategies.base import BaseStrategy

logger = logging.getLogger(__name__)


class StrategyExecutor:
    """
    策略执行器 - 支持并行执行多种策略
    
    功能：
    - 策略注册和管理
    - 单股票和批量股票回测
    - 并行执行优化
    - 执行进度跟踪
    """
    
    def __init__(self, data_fetcher: DataFetcher, max_workers: int = 4):
        """
        初始化策略执行器
        
        Args:
            data_fetcher: 数据获取器
            max_workers: 最大并发工作线程数
        """
        self.data_fetcher = data_fetcher
        self.max_workers = max_workers
        
        # 策略注册表
        self.strategies: Dict[str, BaseStrategy] = {}
        
        # 执行状态
        self.is_running = False
        self.execution_progress = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'start_time': None,
            'end_time': None
        }
        
        # 结果缓存
        self.results_cache = {}
        
        # 执行历史
        self.execution_history = []
        
        logger.info(f"策略执行器初始化完成 - 最大并发数: {max_workers}")
    
    def register_strategy(self, strategy_instance: BaseStrategy) -> bool:
        """
        注册策略实例
        
        Args:
            strategy_instance: 策略实例
        
        Returns:
            bool: 注册成功返回True
        """
        if not isinstance(strategy_instance, BaseStrategy):
            logger.error(f"策略实例必须是BaseStrategy的子类: {type(strategy_instance)}")
            return False
        
        strategy_name = strategy_instance.name
        self.strategies[strategy_name] = strategy_instance
        
        logger.info(f"策略注册成功: {strategy_name}")
        return True
    
    def register_strategy_from_class(self, strategy_class: Type[BaseStrategy], 
                                   strategy_name: str, **kwargs) -> bool:
        """
        从策略类注册策略
        
        Args:
            strategy_class: 策略类
            strategy_name: 策略名称
            **kwargs: 策略参数
        
        Returns:
            bool: 注册成功返回True
        """
        try:
            strategy_instance = strategy_class(**kwargs)
            return self.register_strategy(strategy_instance)
        except Exception as e:
            logger.error(f"策略注册失败: {e}")
            return False
    
    def import_strategies_from_directory(self, directory: str) -> int:
        """
        从目录导入策略
        
        Args:
            directory: 策略目录路径
        
        Returns:
            int: 成功导入的策略数量
        """
        import_count = 0
        
        strategy_dir = Path(directory)
        if not strategy_dir.exists():
            logger.error(f"策略目录不存在: {directory}")
            return 0
        
        # 查找策略文件
        strategy_files = []
        for ext in ['*.py', '*.pyc']:
            strategy_files.extend(strategy_dir.glob(ext))
        
        for file_path in strategy_files:
            if file_path.name.startswith('_') or file_path.name == 'base.py':
                continue  # 跳过私有文件和基类
            
            try:
                # 导入策略文件
                module_name = file_path.stem
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # 查找策略类
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, BaseStrategy) and 
                        obj != BaseStrategy):
                        
                        # 尝试注册策略
                        if self.register_strategy_from_class(obj, name):
                            import_count += 1
                
            except Exception as e:
                logger.error(f"导入策略失败 {file_path}: {e}")
        
        logger.info(f"从目录导入策略完成，成功导入: {import_count} 个")
        return import_count
    
    def execute_single(self, symbol: str, strategy_name: str, 
                      adjust: str = "qfq", initial_capital: float = 100000) -> Optional[Dict[str, Any]]:
        """
        执行单只股票的单个策略
        
        Args:
            symbol: 股票代码
            strategy_name: 策略名称
            adjust: 复权方式
            initial_capital: 初始资金
        
        Returns:
            Optional[Dict[str, Any]]: 回测结果，失败返回None
        """
        if strategy_name not in self.strategies:
            logger.error(f"策略不存在: {strategy_name}")
            return None
        
        # 更新进度
        self.execution_progress['total_tasks'] += 1
        
        logger.info(f"开始执行回测: {symbol} - {strategy_name}")
        
        try:
            # 获取数据
            data = self.data_fetcher.fetch_data(symbol, adjust)
            if data.empty:
                logger.warning(f"获取数据失败: {symbol}")
                self.execution_progress['failed_tasks'] += 1
                return None
            
            # 执行策略
            strategy = self.strategies[strategy_name]
            result = strategy.backtest(data, initial_capital)
            
            if result:
                # 添加执行信息
                result['execution_info'] = {
                    'symbol': symbol,
                    'strategy_name': strategy_name,
                    'adjust': adjust,
                    'initial_capital': initial_capital,
                    'execution_time': time.time(),
                    'status': 'success'
                }
                
                # 更新进度
                self.execution_progress['completed_tasks'] += 1
                
                logger.info(f"回测完成: {symbol} - {strategy_name}, 收益率: {result.get('metrics', {}).get('total_return', 0):.2%}")
                return result
            else:
                self.execution_progress['failed_tasks'] += 1
                logger.error(f"回测失败: {symbol} - {strategy_name}")
                return None
                
        except Exception as e:
            self.execution_progress['failed_tasks'] += 1
            logger.error(f"回测异常 {symbol} - {strategy_name}: {e}")
            return None
    
    def execute_batch_sequential(self, symbol_list: List[str], strategy_names: List[str],
                               adjust: str = "qfq", initial_capital: float = 100000) -> Dict[str, Dict[str, Any]]:
        """
        顺序批量执行回测（单线程）
        
        Args:
            symbol_list: 股票代码列表
            strategy_names: 策略名称列表
            adjust: 复权方式
            initial_capital: 初始资金
        
        Returns:
            Dict[str, Dict[str, Any]]: {(symbol, strategy_name): result}
        """
        logger.info(f"开始顺序批量回测 - 股票数: {len(symbol_list)}, 策略数: {len(strategy_names)}")
        
        # 重置进度
        self._reset_progress(len(symbol_list) * len(strategy_names))
        
        results = {}
        
        for symbol in symbol_list:
            for strategy_name in strategy_names:
                result = self.execute_single(symbol, strategy_name, adjust, initial_capital)
                if result:
                    key = f"{symbol}_{strategy_name}"
                    results[key] = result
        
        # 记录执行历史
        self._record_execution('sequential', symbol_list, strategy_names, len(results))
        
        logger.info(f"顺序批量回测完成 - 成功: {len(results)}, 失败: {self.execution_progress['failed_tasks']}")
        return results
    
    def execute_batch_parallel(self, symbol_list: List[str], strategy_names: List[str],
                              adjust: str = "qfq", initial_capital: float = 100000,
                              max_workers: Optional[int] = None) -> Dict[str, Dict[str, Any]]:
        """
        并行批量执行回测
        
        Args:
            symbol_list: 股票代码列表
            strategy_names: 策略名称列表
            adjust: 复权方式
            initial_capital: 初始资金
            max_workers: 最大并发数
        
        Returns:
            Dict[str, Dict[str, Any]]: {(symbol, strategy_name): result}
        """
        if max_workers is None:
            max_workers = self.max_workers
        
        total_tasks = len(symbol_list) * len(strategy_names)
        logger.info(f"开始并行批量回测 - 股票数: {len(symbol_list)}, 策略数: {len(strategy_names)}, 并发数: {max_workers}")
        
        # 重置进度
        self._reset_progress(total_tasks)
        
        results = {}
        failed_tasks = []
        
        # 创建任务列表
        tasks = []
        for symbol in symbol_list:
            for strategy_name in strategy_names:
                tasks.append((symbol, strategy_name))
        
        # 使用线程池并行执行
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交任务
            future_to_task = {}
            for symbol, strategy_name in tasks:
                future = executor.submit(
                    self.execute_single, 
                    symbol, strategy_name, adjust, initial_capital
                )
                future_to_task[future] = (symbol, strategy_name)
            
            # 收集结果
            for future in as_completed(future_to_task):
                symbol, strategy_name = future_to_task[future]
                try:
                    result = future.result()
                    if result:
                        key = f"{symbol}_{strategy_name}"
                        results[key] = result
                except Exception as e:
                    logger.error(f"任务执行异常 {symbol}_{strategy_name}: {e}")
                    failed_tasks.append((symbol, strategy_name))
        
        # 记录执行历史
        self._record_execution('parallel', symbol_list, strategy_names, len(results))
        
        logger.info(f"并行批量回测完成 - 成功: {len(results)}, 失败: {len(failed_tasks)}")
        return results
    
    def execute_symbol_strategies(self, symbol: str, strategy_names: List[str],
                                 adjust: str = "qfq", initial_capital: float = 100000) -> Dict[str, Dict[str, Any]]:
        """
        对单只股票执行多个策略
        
        Args:
            symbol: 股票代码
            strategy_names: 策略名称列表
            adjust: 复权方式
            initial_capital: 初始资金
        
        Returns:
            Dict[str, Dict[str, Any]]: {strategy_name: result}
        """
        logger.info(f"开始执行策略组合: {symbol} - {strategy_names}")
        
        results = {}
        
        for strategy_name in strategy_names:
            if strategy_name in self.strategies:
                result = self.execute_single(symbol, strategy_name, adjust, initial_capital)
                if result:
                    results[strategy_name] = result
        
        logger.info(f"策略组合执行完成: {symbol} - 成功: {len(results)}")
        return results
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """
        获取执行摘要
        
        Returns:
            Dict[str, Any]: 执行摘要信息
        """
        progress = self.execution_progress.copy()
        
        if progress['start_time'] and progress['end_time']:
            duration = progress['end_time'] - progress['start_time']
            progress['duration_seconds'] = duration
            progress['avg_task_time'] = duration / progress['total_tasks'] if progress['total_tasks'] > 0 else 0
        else:
            progress['duration_seconds'] = 0
            progress['avg_task_time'] = 0
        
        # 成功率
        success_rate = progress['completed_tasks'] / progress['total_tasks'] if progress['total_tasks'] > 0 else 0
        progress['success_rate'] = success_rate
        
        return {
            'current_progress': progress,
            'registered_strategies': list(self.strategies.keys()),
            'total_strategies': len(self.strategies),
            'execution_history': self.execution_history[-5:]  # 最近5次执行记录
        }
    
    def get_best_performing(self, results: Dict[str, Dict[str, Any]], 
                          top_n: int = 5) -> List[Dict[str, Any]]:
        """
        获取表现最好的策略组合
        
        Args:
            results: 回测结果
            top_n: 返回前N个
        
        Returns:
            List[Dict[str, Any]]: 最佳表现列表
        """
        performance_list = []
        
        for key, result in results.items():
            metrics = result.get('metrics', {})
            if 'total_return' in metrics:
                performance_list.append({
                    'key': key,
                    'symbol': result['execution_info']['symbol'],
                    'strategy_name': result['execution_info']['strategy_name'],
                    'total_return': metrics['total_return'],
                    'sharpe_ratio': metrics.get('sharpe_ratio', 0),
                    'max_drawdown': metrics.get('max_drawdown', 0),
                    'annual_return': metrics.get('annual_return', 0)
                })
        
        # 按总收益率排序
        performance_list.sort(key=lambda x: x['total_return'], reverse=True)
        
        return performance_list[:top_n]
    
    def _reset_progress(self, total_tasks: int):
        """重置执行进度"""
        self.execution_progress = {
            'total_tasks': total_tasks,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'start_time': time.time(),
            'end_time': None
        }
    
    def _record_execution(self, mode: str, symbol_list: List[str], 
                         strategy_names: List[str], success_count: int):
        """记录执行历史"""
        self.execution_progress['end_time'] = time.time()
        
        execution_record = {
            'timestamp': time.time(),
            'mode': mode,
            'symbol_count': len(symbol_list),
            'strategy_count': len(strategy_names),
            'success_count': success_count,
            'progress': self.execution_progress.copy()
        }
        
        self.execution_history.append(execution_record)
    
    def stop_execution(self):
        """停止执行"""
        self.is_running = False
        logger.info("策略执行器已停止")
    
    def clear_cache(self):
        """清除结果缓存"""
        self.results_cache.clear()
        logger.info("结果缓存已清除")


# 执行器工厂类
class StrategyExecutorFactory:
    """策略执行器工厂"""
    
    @staticmethod
    def create_standard_executor(data_fetcher: DataFetcher, max_workers: int = 4) -> StrategyExecutor:
        """创建标准策略执行器"""
        return StrategyExecutor(data_fetcher, max_workers)
    
    @staticmethod
    def create_high_performance_executor(data_fetcher: DataFetcher, max_workers: int = 8) -> StrategyExecutor:
        """创建高性能策略执行器"""
        return StrategyExecutor(data_fetcher, max_workers)
    
    @staticmethod
    def create_low_memory_executor(data_fetcher: DataFetcher, max_workers: int = 2) -> StrategyExecutor:
        """创建低内存策略执行器"""
        return StrategyExecutor(data_fetcher, max_workers)


# 测试函数
def test_strategy_executor():
    """测试策略执行器"""
    # 导入必要的模块
    import sys
    import os
    
    # 添加项目路径
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # 创建数据获取器
    data_fetcher = DataFetcher(cache_enabled=True, cache_expiry_days=1)
    
    # 创建执行器
    executor = StrategyExecutor(data_fetcher, max_workers=2)
    
    # 注册策略
    from strategies.sma_cross import SMACrossStrategy
    
    # 注册双均线策略
    sma_strategy = SMACrossStrategy(fast_ma=7, slow_ma=30)
    executor.register_strategy(sma_strategy)
    
    print("策略注册完成")
    print(f"已注册策略: {list(executor.strategies.keys())}")
    
    # 测试单只股票
    print("\n测试单只股票回测...")
    result = executor.execute_single("000001", "双均线交叉")
    if result:
        print(f"回测成功: {result['execution_info']['symbol']} - 收益率: {result['metrics']['total_return']:.2%}")
    
    # 测试批量执行
    print("\n测试批量回测...")
    symbols = ["000001", "000002"]
    results = executor.execute_batch_sequential(symbols, ["双均线交叉"])
    
    print(f"批量回测完成，成功: {len(results)}")
    
    # 显示执行摘要
    summary = executor.get_execution_summary()
    print(f"\n执行摘要:")
    print(f"  总任务数: {summary['current_progress']['total_tasks']}")
    print(f"  成功任务: {summary['current_progress']['completed_tasks']}")
    print(f"  失败任务: {summary['current_progress']['failed_tasks']}")
    print(f"  成功率: {summary['current_progress']['success_rate']:.2%}")


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    test_strategy_executor()