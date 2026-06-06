#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2026/5/15
Desc: 量化模块自定义异常定义
提供细粒度的异常分类，便于上层调用者进行精准的错误处理
"""


class QuantBaseException(Exception):
    """量化模块基础异常类"""
    def __init__(self, message="量化模块发生未知错误", code=None):
        self.message = message
        self.code = code
        super().__init__(self.message)


class DataSaveError(QuantBaseException):
    """数据保存异常"""
    def __init__(self, table_name=None, reason="数据保存到数据库失败"):
        msg = f"[{table_name}] {reason}" if table_name else reason
        super().__init__(message=msg, code="DATA_SAVE_ERR")


class ConfigError(QuantBaseException):
    """配置加载异常"""
    def __init__(self, config_item=None, reason="配置项加载失败"):
        msg = f"[{config_item}] {reason}" if config_item else reason
        super().__init__(message=msg, code="CONFIG_ERR")
