#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2025/9/4 19:00
Desc: 示例脚本，展示如何使用SQLAlchemy ORM保存数据到数据库

https://sqlalchemy.org.cn/
"""

from typing import Type

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from akshare.utils.db_config import DB_CONFIG


def save_to_mysql_orm(df: pd.DataFrame = None, orm_class: Type = None, ):
    # 使用ORM保存数据到数据库（使用默认配置）
    success = save(
        df=df,
        orm_class=orm_class
    )

    if success:
        print("数据成功保存到数据库")
    else:
        print("数据保存失败")


def save(df: pd.DataFrame, orm_class: Type, ) -> bool:
    # 使用传入的参数或配置中的默认值
    host = DB_CONFIG['host']
    port = DB_CONFIG['port']
    user = DB_CONFIG['user']
    password = DB_CONFIG['password']
    database = DB_CONFIG['database']

    try:
        # 创建数据库连接   echo=False 不打印sql
        engine = create_engine(
            f'mysql+pymysql://{user}:{password}@{host}:{port}/{database}',
            echo=False
        )

        # 删除现有表并重新创建（确保表结构与ORM定义一致）
        orm_class.metadata.drop_all(engine)
        orm_class.metadata.create_all(engine)

        # 创建会话
        Session = sessionmaker(bind=engine)
        session = Session()

        # 获取Entity中定义的字段名（排除SQLAlchemy内部字段）
        entity_columns = [column.name for column in orm_class.__table__.columns]

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
