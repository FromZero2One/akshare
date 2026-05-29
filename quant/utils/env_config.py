#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2025/1/15
Desc: 环境变量配置加载器

注意: 功能已合并到 db_config.py，此文件仅为向后兼容保留。
请优先使用:
    from quant.utils.db_config import DB_CONFIG, DB_CONFIG_PRO
"""

from quant.utils.db_config import DB_CONFIG, DB_CONFIG_PRO, get_env_var  # noqa: F401
