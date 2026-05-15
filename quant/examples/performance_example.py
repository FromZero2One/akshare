#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2025/1/15
Desc: 性能监控和缓存使用示例
展示如何使用性能监控和缓存功能优化量化模块
"""

import sys
import os
import time

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from quant.utils.logger_config import get_quant_logger
from quant.utils.performance_monitor import (
    Timer, 
    performance_monitor, 
    monitored_operation,
    perf_stats
)
from quant.utils.cache import cache_result, query_cache, clear_all_cache, get_cache_stats

logger = get_quant_logger()


def example_timer():
    """示例1: 使用Timer上下文管理器"""
    print("\n" + "="*60)
    print("示例1: Timer 上下文管理器")
    print("="*60)
    
    # 计时代码块
    with Timer("数据加载"):
        time.sleep(0.5)  # 模拟耗时操作
        data = list(range(1000))
    
    with Timer("数据处理"):
        time.sleep(0.3)
        result = sum(data)
    
    print(f"处理结果: {result}")


@performance_monitor
def example_performance_monitor():
    """示例2: 使用性能监控装饰器"""
    print("\n" + "="*60)
    print("示例2: performance_monitor 装饰器")
    print("="*60)
    
    # 模拟复杂计算
    time.sleep(0.2)
    result = sum(i**2 for i in range(10000))
    
    return result


@monitored_operation("数据库查询模拟")
def example_monitored_operation():
    """示例3: 使用monitored_operation装饰器"""
    print("\n" + "="*60)
    print("示例3: monitored_operation 装饰器")
    print("="*60)
    
    # 模拟数据库查询
    time.sleep(0.4)
    return {"data": "query_result"}


@cache_result(ttl=5)  # 缓存5秒
def example_cached_function(x):
    """示例4: 使用缓存装饰器"""
    print(f"  执行计算: {x} * {x}")
    time.sleep(0.3)  # 模拟耗时计算
    return x * x


def example_manual_cache():
    """示例5: 手动操作缓存"""
    print("\n" + "="*60)
    print("示例5: 手动缓存操作")
    print("="*60)
    
    # 设置缓存
    print("设置缓存...")
    query_cache.set("user_123", {"name": "张三", "age": 25}, ttl=60)
    query_cache.set("user_456", {"name": "李四", "age": 30}, ttl=60)
    
    # 获取缓存
    print("获取缓存...")
    user = query_cache.get("user_123")
    print(f"  用户数据: {user}")
    
    # 查看缓存统计
    stats = get_cache_stats()
    print(f"  缓存大小: {stats['size']}/{stats['max_size']}")
    print(f"  使用率: {stats['utilization']:.1f}%")
    
    # 删除缓存
    print("删除缓存...")
    query_cache.delete("user_123")
    
    # 验证删除
    user = query_cache.get("user_123")
    print(f"  删除后获取: {user}")  # 应该为 None


def example_cache_demo():
    """示例6: 缓存效果演示"""
    print("\n" + "="*60)
    print("示例6: 缓存效果演示")
    print("="*60)
    
    print("\n第一次调用（需要计算）:")
    start = time.time()
    result1 = example_cached_function(5)
    elapsed1 = time.time() - start
    print(f"  结果: {result1}, 耗时: {elapsed1:.3f}秒")
    
    print("\n第二次调用（从缓存读取）:")
    start = time.time()
    result2 = example_cached_function(5)
    elapsed2 = time.time() - start
    print(f"  结果: {result2}, 耗时: {elapsed2:.3f}秒")
    
    print(f"\n  性能提升: {elapsed1/elapsed2:.1f}x")


def example_performance_report():
    """示例7: 生成性能报告"""
    print("\n" + "="*60)
    print("示例7: 性能统计报告")
    print("="*60)
    
    # 执行一些被监控的操作
    example_monitored_operation()
    example_monitored_operation()
    example_monitored_operation()
    
    # 打印性能报告
    perf_stats.print_report()


def main():
    """运行所有示例"""
    print("\n" + "="*60)
    print("性能监控和缓存使用示例")
    print("="*60)
    
    try:
        # 运行示例
        example_timer()
        example_performance_monitor()
        example_monitored_operation()
        example_manual_cache()
        example_cache_demo()
        example_performance_report()
        
        print("\n" + "="*60)
        print("✅ 所有示例运行完成！")
        print("="*60)
        
    except Exception as e:
        logger.error(f"示例运行失败: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
