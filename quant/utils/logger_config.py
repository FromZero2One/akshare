#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2025/1/15
Desc: 日志配置模块
提供统一的日志配置，支持控制台和文件输出
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from typing import Optional


class LoggerConfig:
    """日志配置器"""
    
    _configured = False
    _loggers = {}
    
    @classmethod
    def setup_logger(
        cls,
        name: str = "quant",
        level: int = logging.INFO,
        log_file: Optional[str] = None,
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        format_str: Optional[str] = None
    ) -> logging.Logger:
        """
        配置并获取日志记录器
        
        Args:
            name: 日志记录器名称
            level: 日志级别
            log_file: 日志文件路径，如果为None则只输出到控制台
            max_bytes: 单个日志文件最大字节数
            backup_count: 保留的备份文件数量
            format_str: 日志格式字符串
            
        Returns:
            配置好的日志记录器
        """
        # 如果已经配置过，直接返回
        if name in cls._loggers:
            return cls._loggers[name]
        
        # 默认日志格式
        if format_str is None:
            format_str = (
                '%(asctime)s - %(name)s - %(levelname)s - '
                '%(filename)s:%(lineno)d - %(message)s'
            )
        
        # 创建logger
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        # 避免重复添加handler
        if logger.handlers:
            cls._loggers[name] = logger
            return logger
        
        # 创建formatter
        formatter = logging.Formatter(format_str)
        
        # 控制台handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # 文件handler（如果指定了日志文件）
        if log_file:
            # 确保日志目录存在
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        cls._loggers[name] = logger
        return logger
    
    @classmethod
    def get_logger(cls, name: str = "quant") -> logging.Logger:
        """
        获取已配置的日志记录器
        
        Args:
            name: 日志记录器名称
            
        Returns:
            日志记录器
        """
        if name not in cls._loggers:
            # 如果未配置，使用默认配置
            return cls.setup_logger(name)
        return cls._loggers[name]


# 创建默认的量化模块日志记录器
def get_quant_logger(
    level: int = logging.INFO,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    获取量化模块的默认日志记录器
    
    Args:
        level: 日志级别
        log_file: 日志文件路径
        
    Returns:
        日志记录器
    """
    if log_file is None:
        # 默认日志文件路径
        log_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'logs',
            'quant.log'
        )
    
    return LoggerConfig.setup_logger(
        name="quant",
        level=level,
        log_file=log_file
    )


# 导出便捷函数
logger = get_quant_logger()
