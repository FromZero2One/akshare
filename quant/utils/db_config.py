#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2025/9/4 19:00
Desc: 数据库配置文件

支持两种配置方式：
1. 环境变量（推荐）：设置 DB_HOST, DB_PASSWORD 等环境变量
2. 直接配置：修改下方的 DB_CONFIG 字典

优先级：环境变量 > 直接配置

环境变量示例：
    export DB_HOST=localhost
    export DB_PORT=3306
    export DB_USER=root
    export DB_PASSWORD=your_password
    export DB_NAME=akshare
"""

import os
from typing import Optional


def get_env_var(key: str, default: Optional[str] = None) -> str:
    """获取环境变量值"""
    return os.environ.get(key, default)


# 尝试从环境变量加载配置，如果不存在则使用默认值
DB_CONFIG = {
    'host': get_env_var('DB_HOST', 'localhost'),
    'port': int(get_env_var('DB_PORT', '3306')),
    'user': get_env_var('DB_USER', 'root'),
    'password': get_env_var('DB_PASSWORD', 'root1314pwd'),  # ⚠️ 建议通过环境变量设置
    'database': get_env_var('DB_NAME', 'akshare')
}

DB_CONFIG_PRO = {
    'host': get_env_var('DB_PRO_HOST', '8.137.104.120'),
    'port': int(get_env_var('DB_PRO_PORT', '3306')),
    'user': get_env_var('DB_PRO_USER', 'root'),
    'password': get_env_var('DB_PRO_PASSWORD', 'root1314pwd'),  # ⚠️ 建议通过环境变量设置
    'database': get_env_var('DB_PRO_NAME', 'akshare')
}
