#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
个人量化回测系统主程序

功能：
- 配置文件管理
- 策略注册和管理
- 回测执行控制
- 结果分析和展示
- 命令行接口
"""

import os
import sys
import argparse
import logging
import configparser
from datetime import datetime
from typing import List, Dict, Any, Optional

# 添加项目路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'core'))
sys.path.append(os.path.join(project_root, 'strategies'))

# 添加 akshare 根目录，以便导入 quant 模块
akshare_root = os.path.dirname(project_root)
if akshare_root not in sys.path:
    sys.path.insert(0, akshare_root)

from core.data_fetcher import DataFetcher
from core.strategy_executor import StrategyExecutor
from core.result_manager import ResultManager
from strategies.sma_cross import SMACrossStrategy, SMACrossEnhancedStrategy

# 设置logger
logger = logging.getLogger(__name__)


class BacktestSystem:
    """个人量化回测系统主类"""
    
    def __init__(self, config_dir: str = None):
        """
        初始化回测系统
        
        Args:
            config_dir: 配置文件目录
        """
        self.config_dir = config_dir or os.path.join(os.path.dirname(__file__), "config")
        self.config = self._load_config()
        
        # 初始化组件
        self.data_fetcher = self._init_data_fetcher()
        self.strategy_executor = self._init_strategy_executor()
        self.result_manager = self._init_result_manager()
        
        # 配置日志
        self._setup_logging()
        
        logger.info("回测系统初始化完成")
    
    def _load_config(self) -> configparser.ConfigParser:
        """加载配置文件"""
        config = configparser.ConfigParser()
        
        config_files = [
            os.path.join(self.config_dir, "backtest.ini"),
            os.path.join(self.config_dir, "strategies.ini"),
            os.path.join(self.config_dir, "cache.ini")
        ]
        
        for config_file in config_files:
            if os.path.exists(config_file):
                config.read(config_file, encoding='utf-8')
                logger.debug(f"加载配置文件: {config_file}")
        
        return config
    
    def _init_data_fetcher(self) -> DataFetcher:
        """初始化数据获取器"""
        cache_enabled = self.config.getboolean('data', 'cache_enabled', fallback=True)
        cache_expiry_days = self.config.getint('data', 'cache_expiry_days', fallback=7)
        
        # 从配置文件读取数据库相关设置
        db_enabled = self.config.getboolean('data', 'db_enabled', fallback=True)
        db_save_enabled = self.config.getboolean('data', 'db_save_enabled', fallback=True)
        
        fetcher = DataFetcher(
            cache_enabled=cache_enabled,
            cache_expiry_days=cache_expiry_days,
            db_enabled=db_enabled,
            db_save_enabled=db_save_enabled
        )
        
        return fetcher
    
    def _init_strategy_executor(self) -> StrategyExecutor:
        """初始化策略执行器"""
        max_workers = self.config.getint('performance', 'max_workers', fallback=4)
        
        executor = StrategyExecutor(self.data_fetcher, max_workers)
        
        # 注册默认策略
        self._register_default_strategies(executor)
        
        # 从目录加载策略
        if self.config.getboolean('strategies', 'load_from_directory', fallback=True):
            strategies_dir = self.config.get('strategies', 'strategies_dir', fallback='../strategies')
            executor.import_strategies_from_directory(strategies_dir)
        
        return executor
    
    def _init_result_manager(self) -> ResultManager:
        """初始化结果管理器"""
        save_format = self.config.get('result', 'save_format', fallback='json')
        results_dir = self.config.get('result', 'results_dir', fallback='../../backtest_results')
        
        manager = ResultManager(results_dir=results_dir, save_format=save_format)
        
        return manager
    
    def _setup_logging(self):
        """设置日志配置"""
        log_level = self.config.get('logging', 'log_level', fallback='INFO')
        log_file = self.config.get('logging', 'log_file', fallback='../../data/logs/backtest.log')
        log_format = self.config.get('logging', 'log_format', 
                                   fallback='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # 确保日志目录存在
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # 配置日志
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format=log_format.replace('{asctime}', '%(asctime)s').replace('{name}', '%(name)s').replace('{levelname}', '%(levelname)s').replace('{message}', '%(message)s'),
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
    
    def _register_default_strategies(self, executor: StrategyExecutor):
        """注册默认策略"""
        # 从配置文件读取策略参数
        if 'SMACross' in self.config:
            params = dict(self.config['SMACross'])
            sma_strategy = SMACrossStrategy(
                fast_ma=int(params['fast_ma']),
                slow_ma=int(params['slow_ma']),
                stop_loss=float(params['stop_loss']),
                take_profit=float(params['take_profit']),
                max_position=float(params['max_position'])
            )
            executor.register_strategy(sma_strategy)
        
        if 'SMACrossEnhanced' in self.config:
            params = dict(self.config['SMACrossEnhanced'])
            enhanced_strategy = SMACrossEnhancedStrategy(
                fast_ma=int(params['fast_ma']),
                slow_ma=int(params['slow_ma']),
                stop_loss=float(params['stop_loss']),
                take_profit=float(params['take_profit']),
                max_position=float(params['max_position']),
                volume_filter=self.config.getboolean('SMACrossEnhanced', 'volume_filter'),
                trend_filter=self.config.getboolean('SMACrossEnhanced', 'trend_filter')
            )
            executor.register_strategy(enhanced_strategy)
    
    def get_default_symbols(self) -> List[str]:
        """获取默认股票列表"""
        # 这里可以返回默认的股票代码列表
        # 实际使用时可以从数据库或配置文件读取
        return ["000001", "000002", "000003", "000004", "000005", 
                "000858", "000895", "002415", "002594", "002714"]
    
    def run_single(self, symbol: str, strategy_name: str = None, 
                  adjust: str = None, initial_capital: float = None) -> Dict[str, Any]:
        """
        执行单只股票回测
        
        Args:
            symbol: 股票代码
            strategy_name: 策略名称
            adjust: 复权方式
            initial_capital: 初始资金
        
        Returns:
            Dict[str, Any]: 回测结果
        """
        logger.info(f"开始单只股票回测: {symbol}")
        
        # 使用配置默认值
        adjust = adjust or self.config.get('backtest', 'default_adjust', fallback='qfq')
        initial_capital = initial_capital or self.config.getfloat('backtest', 'initial_capital', fallback=100000)
        
        # 如果没有指定策略，使用默认策略
        if strategy_name is None:
            strategy_name = self.config.get('backtest', 'default_strategy', fallback='SMACross')
        
        # 执行回测
        result = self.strategy_executor.execute_single(
            symbol, strategy_name, adjust, initial_capital
        )
        
        if result:
            # 保存结果
            if self.config.getboolean('result', 'auto_save', fallback=True):
                self.result_manager.save_results(symbol, strategy_name, result, adjust)
            
            # 打印摘要
            from strategies.base import BaseStrategy
            for strategy in self.strategy_executor.strategies.values():
                if strategy.name == strategy_name:
                    strategy.print_summary()
                    break
        
        return result or {}
    
    def run_batch(self, symbols: List[str] = None, strategy_names: List[str] = None,
                  adjust: str = None, initial_capital: float = None,
                  mode: str = 'parallel', max_workers: int = None) -> Dict[str, Dict[str, Any]]:
        """
        执行批量回测
        
        Args:
            symbols: 股票代码列表
            strategy_names: 策略名称列表
            adjust: 复权方式
            initial_capital: 初始资金
            mode: 执行模式 ('sequential', 'parallel')
            max_workers: 最大并发数
        
        Returns:
            Dict[str, Dict[str, Any]]: 回测结果
        """
        # 使用默认值
        symbols = symbols or self.get_default_symbols()
        adjust = adjust or self.config.get('backtest', 'default_adjust', fallback='qfq')
        initial_capital = initial_capital or self.config.getfloat('backtest', 'initial_capital', fallback=100000)
        max_workers = max_workers or self.config.getint('performance', 'max_workers', fallback=4)
        
        # 如果没有指定策略，使用所有策略
        strategy_names = strategy_names or list(self.strategy_executor.strategies.keys())
        
        logger.info(f"开始批量回测 - 模式: {mode}, 股票数: {len(symbols)}, 策略数: {len(strategy_names)}")
        
        # 执行回测
        if mode == 'sequential':
            results = self.strategy_executor.execute_batch_sequential(
                symbols, strategy_names, adjust, initial_capital
            )
        else:  # parallel
            results = self.strategy_executor.execute_batch_parallel(
                symbols, strategy_names, adjust, initial_capital, max_workers
            )
        
        # 保存结果
        if self.config.getboolean('result', 'auto_save', fallback=True):
            for key, result in results.items():
                symbol, strategy_name = key.split('_')
                self.result_manager.save_results(symbol, strategy_name, result, adjust)
        
        # 生成汇总报告
        if self.config.getboolean('result', 'summary_report', fallback=True):
            summary = self.result_manager.generate_summary_report(list(results.values()))
            print(f"\n批量回测汇总:")
            print(f"  成功数量: {len(results)}")
            print(f"  平均收益率: {summary['performance_stats']['total_return_avg']:.2%}")
            print(f"  正收益比例: {summary['performance_stats']['positive_return_rate']:.2%}")
        
        return results
    
    def analyze_results(self, symbols: List[str] = None, strategy_names: List[str] = None):
        """分析回测结果"""
        logger.info("开始分析回测结果")
        
        # 加载结果
        results = self.result_manager.load_results(
            symbol=symbols[0] if symbols else None,
            strategy_name=strategy_names[0] if strategy_names else None
        )
        
        if not results:
            print("没有找到回测结果")
            return
        
        # 生成汇总报告
        summary = self.result_manager.generate_summary_report(results)
        
        print(f"\n{'='*60}")
        print(f"回测结果分析报告")
        print(f"{'='*60}")
        print(f"总结果数: {summary['total_results']}")
        print(f"股票数量: {summary['unique_symbols']}")
        print(f"策略数量: {summary['unique_strategies']}")
        print(f"平均收益率: {summary['performance_stats']['total_return_avg']:.2%}")
        print(f"正收益比例: {summary['performance_stats']['positive_return_rate']:.2%}")
        print(f"最佳收益率: {summary['performance_stats']['best_return']:.2%}")
        print(f"最差收益率: {summary['performance_stats']['worst_return']:.2%}")
        
        # 策略表现
        print(f"\n策略表现:")
        for strategy_name, perf in summary['strategy_performance'].items():
            print(f"  {strategy_name}: 平均收益 {perf['avg_return']:.2%}, 胜率 {perf['win_rate']:.2%}")
        
        # 生成图表
        chart_path = self.result_manager.generate_comparison_chart(results)
        if chart_path:
            print(f"\n比较图表已保存: {chart_path}")
    
    def list_strategies(self):
        """列出已注册的策略"""
        print(f"\n已注册策略:")
        for name in self.strategy_executor.strategies.keys():
            print(f"  - {name}")
    
    def system_info(self):
        """显示系统信息"""
        print(f"\n系统信息:")
        print(f"  数据获取器: {type(self.data_fetcher).__name__}")
        print(f"  策略执行器: {type(self.strategy_executor).__name__}")
        print(f"  结果管理器: {type(self.result_manager).__name__}")
        print(f"  最大并发数: {self.strategy_executor.max_workers}")
        print(f"  缓存状态: {'启用' if self.data_fetcher.cache_enabled else '禁用'}")
        print(f"  数据库状态: {'启用' if self.data_fetcher.db_enabled else '禁用'}")
        print(f"  自动保存DB: {'启用' if self.data_fetcher.db_save_enabled else '禁用'}")
        print(f"  保存格式: {self.result_manager.save_format}")
        
        # 显示数据库连接信息
        from core.data_fetcher import DB_AVAILABLE
        if DB_AVAILABLE:
            info = self.data_fetcher.get_cache_info()
            print(f"  数据库连接: {info.get('db_status', 'unknown')}")
            print(f"  连接池大小: {info.get('db_pool_size', 'unknown')}")
        else:
            print(f"  数据库模块: 未安装（quant 模块不可用）")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='个人量化回测系统')
    
    # 基本参数
    parser.add_argument('--symbols', nargs='+', help='股票代码列表')
    parser.add_argument('--strategies', nargs='+', help='策略名称列表')
    parser.add_argument('--adjust', default='qfq', help='复权方式')
    parser.add_argument('--capital', type=float, help='初始资金')
    
    # 执行模式
    parser.add_argument('--mode', choices=['single', 'batch', 'sequential', 'parallel'], 
                       default='parallel', help='执行模式')
    parser.add_argument('--max-workers', type=int, help='最大并发数')
    
    # 功能选项
    parser.add_argument('--list-strategies', action='store_true', help='列出所有策略')
    parser.add_argument('--analyze', action='store_true', help='分析回测结果')
    parser.add_argument('--info', action='store_true', help='显示系统信息')
    parser.add_argument('--config-dir', help='配置文件目录')
    
    # 其他选项
    parser.add_argument('--no-cache', action='store_true', help='禁用缓存')
    parser.add_argument('--no-save', action='store_true', help='不保存结果')
    
    args = parser.parse_args()
    
    # 初始化系统
    system = BacktestSystem(config_dir=args.config_dir)
    
    # 处理各种命令
    if args.info:
        system.system_info()
        return
    
    if args.list_strategies:
        system.list_strategies()
        return
    
    # 处理缓存选项
    if args.no_cache:
        system.data_fetcher.cache_enabled = False
        print("缓存已禁用")
    
    # 执行回测
    if args.mode == 'single':
        if not args.symbols or not args.strategies:
            print("单模式需要指定 --symbols 和 --strategies")
            return
        
        for symbol in args.symbols:
            for strategy in args.strategies:
                result = system.run_single(symbol, strategy, args.adjust, args.capital)
                if result:
                    print(f"\n{symbol} - {strategy} 回测完成")
    
    else:  # batch mode
        results = system.run_batch(
            symbols=args.symbols,
            strategy_names=args.strategies,
            adjust=args.adjust,
            initial_capital=args.capital,
            mode=args.mode if args.mode in ['sequential', 'parallel'] else 'parallel',
            max_workers=args.max_workers
        )
        
        print(f"\n批量回测完成，成功: {len(results)} 个组合")
    
    # 分析结果
    if args.analyze:
        system.analyze_results(args.symbols, args.strategies)
    
    print("\n回测系统执行完成")


if __name__ == "__main__":
    main()