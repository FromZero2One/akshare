#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2025/9/4 19:00
Desc: 数据库配置文件（统一配置入口）

配置加载优先级：
1. .env 文件（项目根目录）
2. 系统环境变量

密码禁止硬编码在此文件中，必须通过 .env 或环境变量设置。
"""

import os
from pathlib import Path
from typing import Optional


def get_env_var(key: str, default: Optional[str] = None) -> str:
    """获取环境变量值"""
    return os.environ.get(key, default)


# 自动加载 .env 文件（若已加载则重复调用无副作用）
try:
    from dotenv import load_dotenv
    # 显式指定 .env 文件路径：当前文件所在目录向上三级即为项目根目录
    env_path = Path(__file__).resolve().parent.parent.parent / '.env'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    else:
        # 如果找不到 .env，尝试在当前工作目录查找
        load_dotenv()
except ImportError:
    pass


DB_CONFIG = {
    'host': get_env_var('DB_HOST', 'localhost'),
    'port': int(get_env_var('DB_PORT', '3306')),
    'user': get_env_var('DB_USER', 'root'),
    'password': get_env_var('DB_PASSWORD'),  # ⚠️ 必填，通过 .env 或环境变量设置
    'database': get_env_var('DB_NAME', 'akshare')
}

DB_CONFIG_PRO = {
    'host': get_env_var('DB_PRO_HOST', '8.137.104.120'),
    'port': int(get_env_var('DB_PRO_PORT', '3306')),
    'user': get_env_var('DB_PRO_USER', 'root'),
    # ⚠️ 密码必填，通过 .env 或环境变量设置，不允许硬编码默认值
    'password': get_env_var('DB_PRO_PASSWORD'),
    'database': get_env_var('DB_PRO_NAME', 'akshare')
}
