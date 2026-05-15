#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2025/1/15
Desc: 性能监控工具
提供函数执行时间统计和性能分析功能
"""

import time
import functools
import logging
from typing import Optional, Callable
from contextlib import ContextDecorator

from .logger_config import get_quant_logger

logger = get_quant_logger()


class Timer(ContextDecorator):
    """
    计时器上下文管理器
    
    用法:
        # 作为上下文管理器
        with Timer("数据库查询"):
            result = query_database()
        
        # 作为装饰器
        @Timer("复杂计算")
        def complex_calculation():
            pass
    """
    
    def __init__(self, operation_name: str = "Operation", logger_instance=None):
        """
        初始化计时器
        
        Args:
            operation_name: 操作名称
            logger_instance: 日志记录器实例
        """
        self.operation_name = operation_name
        self.logger = logger_instance or logger
        self.start_time = None
        self.end_time = None
        self.elapsed_time = None
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, *exc):
        self.end_time = time.perf_counter()
        self.elapsed_time = self.end_time - self.start_time
        
        if self.elapsed_time > 1.0:  # 超过1秒记录警告
            self.logger.warning(
                f"⏱️ {self.operation_name} 耗时: {self.elapsed_time:.3f}秒"
            )
        else:
            self.logger.debug(
                f"⏱️ {self.operation_name} 耗时: {self.elapsed_time:.3f}秒"
            )
        
        return False
    
    def __call__(self, func: Callable) -> Callable:
        """作为装饰器使用"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with Timer(self.operation_name, self.logger):
                return func(*args, **kwargs)
        return wrapper


def performance_monitor(func: Callable) -> Callable:
    """
    性能监控装饰器
    
    自动记录函数的执行时间和返回值
    
    Args:
        func: 被装饰的函数
        
    Returns:
        包装后的函数
        
    Example:
        @performance_monitor
        def query_data():
            return db.query(...)
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        
        try:
            result = func(*args, **kwargs)
            elapsed_time = time.perf_counter() - start_time
            
            logger.info(
                f"✅ {func.__name__} 执行成功 | "
                f"耗时: {elapsed_time:.3f}秒 | "
                f"参数: args={len(args)}, kwargs={len(kwargs)}"
            )
            
            return result
            
        except Exception as e:
            elapsed_time = time.perf_counter() - start_time
            
            logger.error(
                f"❌ {func.__name__} 执行失败 | "
                f"耗时: {elapsed_time:.3f}秒 | "
                f"错误: {str(e)}",
                exc_info=True
            )
            raise
    
    return wrapper


class PerformanceStats:
    """
    性能统计收集器
    
    用于收集和展示多次操作的性能统计数据
    """
    
    def __init__(self):
        self.stats = {}
    
    def record(self, operation_name: str, elapsed_time: float):
        """
        记录一次操作的耗时
        
        Args:
            operation_name: 操作名称
            elapsed_time: 耗时（秒）
        """
        if operation_name not in self.stats:
            self.stats[operation_name] = {
                'count': 0,
                'total_time': 0.0,
                'min_time': float('inf'),
                'max_time': 0.0,
                'times': []
            }
        
        stat = self.stats[operation_name]
        stat['count'] += 1
        stat['total_time'] += elapsed_time
        stat['min_time'] = min(stat['min_time'], elapsed_time)
        stat['max_time'] = max(stat['max_time'], elapsed_time)
        stat['times'].append(elapsed_time)
    
    def get_average(self, operation_name: str) -> float:
        """获取平均耗时"""
        if operation_name not in self.stats:
            return 0.0
        stat = self.stats[operation_name]
        return stat['total_time'] / stat['count'] if stat['count'] > 0 else 0.0
    
    def get_summary(self, operation_name: str) -> dict:
        """获取操作的性能摘要"""
        if operation_name not in self.stats:
            return {}
        
        stat = self.stats[operation_name]
        return {
            'operation': operation_name,
            'count': stat['count'],
            'total_time': stat['total_time'],
            'average_time': self.get_average(operation_name),
            'min_time': stat['min_time'],
            'max_time': stat['max_time'],
        }
    
    def print_report(self):
        """打印性能报告"""
        if not self.stats:
            logger.info("没有性能统计数据")
            return
        
        logger.info("=" * 60)
        logger.info("性能统计报告")
        logger.info("=" * 60)
        
        for operation_name, stat in self.stats.items():
            summary = self.get_summary(operation_name)
            logger.info(
                f"\n{operation_name}:\n"
                f"  调用次数: {summary['count']}\n"
                f"  总耗时:   {summary['total_time']:.3f}秒\n"
                f"  平均耗时: {summary['average_time']:.3f}秒\n"
                f"  最快:     {summary['min_time']:.3f}秒\n"
                f"  最慢:     {summary['max_time']:.3f}秒"
            )
        
        logger.info("=" * 60)


# 全局性能统计实例
perf_stats = PerformanceStats()


def monitored_operation(operation_name: str):
    """
    带性能监控的操作装饰器
    
    自动记录操作耗时到全局性能统计
    
    Args:
        operation_name: 操作名称
        
    Example:
        @monitored_operation("数据库查询")
        def query_db():
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                elapsed_time = time.perf_counter() - start_time
                
                perf_stats.record(operation_name, elapsed_time)
                
                if elapsed_time > 1.0:
                    logger.warning(
                        f"⚠️ {operation_name} 耗时较长: {elapsed_time:.3f}秒"
                    )
                
                return result
            except Exception as e:
                elapsed_time = time.perf_counter() - start_time
                perf_stats.record(operation_name, elapsed_time)
                logger.error(f"{operation_name} 执行失败: {e}", exc_info=True)
                raise
        return wrapper
    return decorator
