#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2025/9/4 19:00
Desc: 数据库配置文件示例
此文件展示了如何配置数据库连接参数
"""
import os

# 切换生产环境或本地环境
useProd = True
# 设置数据库连接参数（通过环境变量）
os.environ['MYSQL_HOST'] = '8.137.104.120' if useProd else 'localhost'
os.environ['MYSQL_PORT'] = '3306'
os.environ['MYSQL_USER'] = 'root'
os.environ['MYSQL_PASSWORD'] = 'root1314pwd' if useProd else ''
os.environ['MYSQL_DATABASE'] = 'akshare'

# 数据库配置
DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': os.getenv('MYSQL_DATABASE', 'akshare')
}

DB_CONFIG_PRO = {
    'host': '8.137.104.120',
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': 'root1314pwd',
    'database': os.getenv('MYSQL_DATABASE', 'akshare')
}