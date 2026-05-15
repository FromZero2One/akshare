#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2025/1/15
Desc: 环境变量配置加载器
从环境变量或 .env 文件加载配置，避免硬编码敏感信息
"""

import os
from typing import Optional


def get_env_var(key: str, default: Optional[str] = None) -> str:
    """
    获取环境变量值
    
    Args:
        key: 环境变量名
        default: 默认值
        
    Returns:
        环境变量值或默认值
    """
    return os.environ.get(key, default)


def load_db_config() -> dict:
    """
    从环境变量加载数据库配置
    
    环境变量优先级：
    1. 系统环境变量
    2. .env 文件（如果存在）
    3. 默认值
    
    Returns:
        数据库配置字典
    """
    # 尝试加载 .env 文件
    try:
        from dotenv import load_dotenv
        load_dotenv()  # 加载项目根目录的 .env 文件
    except ImportError:
        pass  # 如果没有安装 python-dotenv，跳过
    
    config = {
        'host': get_env_var('DB_HOST', 'localhost'),
        'port': int(get_env_var('DB_PORT', '3306')),
        'user': get_env_var('DB_USER', 'root'),
        'password': get_env_var('DB_PASSWORD', ''),
        'database': get_env_var('DB_NAME', 'akshare')
    }
    
    # 生产环境配置
    pro_config = {
        'host': get_env_var('DB_PRO_HOST', config['host']),
        'port': int(get_env_var('DB_PRO_PORT', str(config['port']))),
        'user': get_env_var('DB_PRO_USER', config['user']),
        'password': get_env_var('DB_PRO_PASSWORD', config['password']),
        'database': get_env_var('DB_PRO_NAME', config['database'])
    }
    
    return config, pro_config


# 加载配置
DB_CONFIG, DB_CONFIG_PRO = load_db_config()
