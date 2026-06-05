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
    # 方案一：基于文件路径定位 .env（不受工作目录影响）
    env_path_by_file = Path(__file__).resolve().parent.parent.parent / '.env'
    # 方案二：基于当前工作目录定位 .env（兼容 PyCharm 等 IDE 直接运行）
    env_path_by_cwd = Path.cwd() / '.env'

    loaded = False
    for env_path in [env_path_by_file, env_path_by_cwd]:
        if env_path.exists():
            load_dotenv(dotenv_path=env_path, override=True)
            loaded = True
            break

    if not loaded:
        # 兜底：让 load_dotenv 自动搜索
        load_dotenv(override=True)
except ImportError:
    import logging
    logging.warning("python-dotenv 未安装，无法加载 .env 文件。请执行: pip install python-dotenv")


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

# 数据库环境选择配置
def should_use_pro_db() -> bool:
    """
    判断是否使用生产环境数据库
    
    Returns:
        bool: True=使用生产环境, False=使用开发环境
    """
    use_pro_str = get_env_var('DB_USE_PRO', 'true').strip().lower()
    return use_pro_str in ('true', '1', 'yes', 'on')
