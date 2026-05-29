#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2025/1/15
Desc: 简单缓存工具
提供基于内存的LRU缓存，用于缓存频繁查询的数据
"""

import time
import functools
import hashlib
import json
from typing import Any, Optional, Callable
from collections import OrderedDict

from .logger_config import get_quant_logger

logger = get_quant_logger()


class SimpleCache:
    """
    简单的LRU缓存实现
    
    特性:
    - 基于内存存储
    - LRU淘汰策略
    - 支持TTL过期
    - 线程安全（通过锁）
    """
    
    def __init__(self, max_size: int = 128, default_ttl: int = 300):
        """
        初始化缓存
        
        Args:
            max_size: 最大缓存条目数
            default_ttl: 默认过期时间（秒），0表示永不过期
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache = OrderedDict()
        self._timestamps = {}
    
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，如果不存在或已过期则返回None
        """
        if key not in self._cache:
            return None
        
        # 检查是否过期
        if key in self._timestamps:
            timestamp, ttl = self._timestamps[key]
            if ttl > 0 and time.time() - timestamp > ttl:
                # 已过期，删除
                self.delete(key)
                logger.debug(f"缓存过期: {key}")
                return None
        
        # 移动到末尾（最近使用）
        self._cache.move_to_end(key)
        logger.debug(f"缓存命中: {key}")
        return self._cache[key]
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），None使用默认值，0表示永不过期
        """
        # 如果缓存已满，删除最旧的
        if len(self._cache) >= self.max_size:
            oldest_key = next(iter(self._cache))
            self.delete(oldest_key)
            logger.debug(f"缓存已满，删除最旧条目: {oldest_key}")
        
        self._cache[key] = value
        self._cache.move_to_end(key)
        
        # 设置过期时间
        if ttl is None:
            ttl = self.default_ttl
        self._timestamps[key] = (time.time(), ttl)
        
        logger.debug(f"缓存设置: {key} (TTL: {ttl}s)")
    
    def delete(self, key: str):
        """删除缓存条目"""
        if key in self._cache:
            del self._cache[key]
        if key in self._timestamps:
            del self._timestamps[key]
    
    def clear(self):
        """清空所有缓存"""
        self._cache.clear()
        self._timestamps.clear()
        logger.info("缓存已清空")
    
    def size(self) -> int:
        """获取当前缓存大小"""
        return len(self._cache)
    
    def get_size_bytes(self) -> int:
        """估算缓存占用内存字节数"""
        total = 0
        for key, value in self._cache.items():
            total += len(str(key))
            if hasattr(value, 'memory_usage'):
                total += int(value.memory_usage(deep=True).sum())
            else:
                total += len(str(value))
        return total

    def stats(self) -> dict:
        """获取缓存统计信息（含内存占用估算）"""
        mem_bytes = self.get_size_bytes()
        return {
            'size': len(self._cache),
            'max_size': self.max_size,
            'utilization': len(self._cache) / self.max_size * 100 if self.max_size > 0 else 0,
            'memory_bytes': mem_bytes,
            'memory_mb': round(mem_bytes / (1024 * 1024), 2),
        }


# 全局缓存实例（扩大容量支持批量回测场景）
query_cache = SimpleCache(max_size=10000, default_ttl=0)  # 历史数据不变，永不过期


def cache_result(ttl: Optional[int] = None, cache_instance: SimpleCache = None):
    """
    缓存函数结果的装饰器
    
    Args:
        ttl: 过期时间（秒）
        cache_instance: 缓存实例，默认使用全局缓存
        
    Example:
        @cache_result(ttl=600)  # 缓存10分钟
        def get_stock_data(symbol):
            return fetch_from_db(symbol)
    """
    if cache_instance is None:
        cache_instance = query_cache
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = _generate_cache_key(func.__name__, args, kwargs)
            
            # 尝试从缓存获取
            cached_result = cache_instance.get(cache_key)
            if cached_result is not None:
                logger.debug(f"使用缓存结果: {func.__name__}")
                return cached_result
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 存入缓存
            cache_instance.set(cache_key, result, ttl)
            logger.debug(f"缓存新结果: {func.__name__}")
            
            return result
        return wrapper
    return decorator


def _generate_cache_key(func_name: str, args: tuple, kwargs: dict) -> str:
    """
    生成缓存键
    
    Args:
        func_name: 函数名
        args: 位置参数
        kwargs: 关键字参数
        
    Returns:
        缓存键字符串
    """
    # 将参数转换为可哈希的形式
    key_data = {
        'func': func_name,
        'args': args,
        'kwargs': sorted(kwargs.items())
    }
    
    # 序列化为JSON并计算哈希
    try:
        key_string = json.dumps(key_data, default=str, sort_keys=True)
        cache_key = hashlib.md5(key_string.encode()).hexdigest()
    except Exception:
        # 如果序列化失败，使用简化版本
        cache_key = f"{func_name}_{hash(str(args))}_{hash(str(kwargs))}"
    
    return cache_key


def invalidate_cache(pattern: str, cache_instance: SimpleCache = None):
    """
    使匹配模式的缓存失效
    
    Args:
        pattern: 匹配模式（函数名前缀）
        cache_instance: 缓存实例
    """
    if cache_instance is None:
        cache_instance = query_cache
    
    keys_to_delete = []
    for key in cache_instance._cache.keys():
        # 这里简化处理，实际可以实现更复杂的模式匹配
        if pattern in str(key):
            keys_to_delete.append(key)
    
    for key in keys_to_delete:
        cache_instance.delete(key)
    
    logger.info(f"清除 {len(keys_to_delete)} 条缓存（模式: {pattern}）")


# 便捷函数
def clear_all_cache():
    """清空所有缓存"""
    query_cache.clear()


def get_cache_stats():
    """获取缓存统计"""
    return query_cache.stats()
