#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2025/9/4 19:00
Desc: 示例脚本，展示如何使用SQLAlchemy ORM保存数据到数据库

https://sqlalchemy.org.cn/
"""

from typing import Type

import pandas as pd
from sqlalchemy import create_engine, MetaData
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from akshare.utils.db_config import DB_CONFIG

# 使用传入的参数或配置中的默认值
host = DB_CONFIG['host']
port = DB_CONFIG['port']
user = DB_CONFIG['user']
password = DB_CONFIG['password']
database = DB_CONFIG['database']

# 创建数据库连接   echo=False 不打印sql
engine = create_engine(
    f'mysql+pymysql://{user}:{password}@{host}:{port}/{database}',
    echo=False
)


def save_to_mysql_orm(df: pd.DataFrame = None, orm_class: Type = None, rebuild: bool = False):
    # 使用ORM保存数据到数据库（使用默认配置）
    success = save(
        df=df,
        orm_class=orm_class,
        rebuild=rebuild
    )

    if success:
        print("数据成功保存到数据库")
    else:
        print("数据保存失败")


def save(df: pd.DataFrame, orm_class: Type, rebuild: bool = False) -> bool:
    """
    使用SQLAlchemy ORM保存数据到数据库

    Parameters:
    -----------
    df : pd.DataFrame
        要保存的数据
    orm_class : Type
        ORM 类，用于映射到数据库表
    rebuild: bool, default False
        是否重建表
    Returns:
    --------
    bool
        保存成功返回True，失败返回False
    """
    try:

        # 删除现有表并重新创建（确保表结构与ORM定义一致）
        if rebuild:
            orm_class.metadata.drop_all(engine)

        # 这行代码会根据 ORM 类的定义创建相应的数据库表。如果表已经存在，则不会重复创建。
        orm_class.metadata.create_all(engine)

        # 创建会话
        Session = sessionmaker(bind=engine)
        session = Session()

        # 获取Entity中定义的字段名（排除自增主键字段）
        entity_columns = []
        for column in orm_class.__table__.columns:
            # 如果字段是自增主键，则跳过
            if not (column.autoincrement and column.primary_key):
                entity_columns.append(column.name)

        # 只保留DataFrame中与Entity字段匹配的列
        filtered_df = df[entity_columns].copy()

        # 将DataFrame转换为ORM对象列表
        records = []
        for _, row in filtered_df.iterrows():
            record = orm_class(**row.to_dict())
            records.append(record)

        # 批量插入数据
        session.bulk_save_objects(records)
        session.commit()
        session.close()

        return True

    except Exception as e:
        print(f"保存数据到 MySQL 失败: {e}")
        return False


# ticker 股票代码
def get_data_to_df(orm_class: Type = None, Ticker: str = None):
    """
    通过ORM类获取表名并查询数据
    """
    table_name = orm_class.__tablename__

    # 反射数据库结构（自动获取表信息）
    metadata = MetaData()
    metadata.reflect(bind=engine)

    # 检查表是否存在
    if table_name in metadata.tables:
        target_table = metadata.tables[table_name]  # 获取对应的表

        # 构建查询
        if Ticker:
            stmt = select(target_table).where(target_table.c.Ticker == Ticker)
        else:
            stmt = select(target_table)  # 查询表的所有数据

        # 使用 Pandas 读取查询结果
        with engine.connect() as connection:
            df = pd.read_sql(stmt, con=connection)

        print(df)
        return df
    else:
        print(f"表 {table_name} 不存在")
        return pd.DataFrame()
