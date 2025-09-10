#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2025/8/18 12:00
Desc: 数据库工具模块，用于将数据保存到 MySQL 数据库
https://sqlalchemy.org.cn/
"""

from typing import Optional, Dict
import pandas as pd
from sqlalchemy import create_engine, MetaData, Table, text
from .db_config import DB_CONFIG

host = DB_CONFIG['host']
port = DB_CONFIG['port']
user = DB_CONFIG['user']
password = DB_CONFIG['password']
database = DB_CONFIG['database']


def save_to_mysql(df: pd.DataFrame,
                  table_name: str,
                  if_exists: str = 'replace',
                  convert_columns: Optional[Dict[str, str]] = None,
                  columns: Optional[Dict[str, str]] = None) -> bool:
    """
    将 pandas DataFrame 保存到 MySQL 数据库
    
    Parameters:
    -----------
    df : pd.DataFrame
        要保存的数据
    table_name : str
        数据库表名
    if_exists : str, default 'replace'
        如果表存在如何处理，可选 'fail', 'replace', 'append'
    column_mapping : dict, optional
        列名映射字典，键为原始列名，值为数据库列名
    column_comments : dict, optional
        列注释字典，键为列名，值为注释内容
        
    Returns:
    --------
    bool
        保存成功返回 True，否则返回 False
    """
    try:
        # 如果提供了列名映射，则重命名列
        if convert_columns:
            # 重命名DataFrame的列
            df_to_save = df.rename(columns=convert_columns)
        else:
            df_to_save = df.copy()

        # 创建数据库连接
        engine = create_engine(
            f'mysql+pymysql://{user}:{password}@{host}:{port}/{database}',
            echo=False
        )

        # 保存数据到数据库
        df_to_save.to_sql(table_name, con=engine, if_exists=if_exists, index=False)

        # 如果提供了列注释，则添加注释
        if columns:
            # 获取表的元数据
            metadata = MetaData()
            metadata.reflect(bind=engine)

            # 获取表对象
            table = Table(table_name, metadata, autoload_with=engine)

            # 为每个列添加注释
            for column_name, comment in columns.items():
                if column_name in table.c:
                    # 构造 ALTER TABLE 语句添加注释
                    alter_sql = text(
                        f"ALTER TABLE `{table_name}` MODIFY COLUMN `{column_name}` {table.c[column_name].type} COMMENT :comment")
                    with engine.connect() as conn:
                        conn.execute(alter_sql, {"comment": comment})
                        conn.commit()

        return True
    except Exception as e:
        print(f"保存数据到 MySQL 失败: {str(e)}")
        return False


def read_from_mysql(table_name: str,
                    column_mapping: Optional[Dict[str, str]] = None) -> Optional[pd.DataFrame]:

    try:
        # 创建数据库连接
        engine = create_engine(
            f'mysql+pymysql://{user}:{password}@{host}:{port}/{database}',
            echo=False
        )

        # 从数据库读取数据
        df = pd.read_sql_table(table_name, con=engine)

        # 如果提供了列名映射，则将列名映射回原始名称
        if column_mapping and df is not None:
            # 使用映射字典将数据库列名映射回原始列名
            df = df.rename(columns=column_mapping)

        return df
    except Exception as e:
        print(f"从 MySQL 读取数据失败: {str(e)}")
        return None

