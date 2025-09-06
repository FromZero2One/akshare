#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2025/9/4 19:00
Desc: 示例脚本，展示如何使用SQLAlchemy ORM保存数据到数据库

https://sqlalchemy.org.cn/
"""

from tests.StockEntity import StockEntity
from typing import Optional, Dict, Type
import os
import pandas as pd
from sqlalchemy import create_engine, MetaData, Table, text
from sqlalchemy.orm import sessionmaker

from akshare.utils.db_config import DB_CONFIG

def save_to_mysql_orm(df: pd.DataFrame = None):
    """
    测试使用ORM将数据保存到MySQL数据库
    """

    # 使用ORM保存数据到数据库（使用默认配置）
    success = save(
        df=df,
        orm_class=StockEntity
    )

    if success:
        print("数据成功保存到数据库")
    else:
        print("数据保存失败")


def save(df: pd.DataFrame, orm_class: Type,) -> bool:
    # 使用传入的参数或配置中的默认值
    host = DB_CONFIG['host']
    port = DB_CONFIG['port']
    user = DB_CONFIG['user']
    password = DB_CONFIG['password']
    database = DB_CONFIG['database']

    try:
        # 创建数据库连接
        engine = create_engine(
            f'mysql+pymysql://{user}:{password}@{host}:{port}/{database}',
            echo=False
        )

        # 创建表（如果不存在）
        orm_class.metadata.create_all(engine)

        # 创建会话
        Session = sessionmaker(bind=engine)
        session = Session()

        # 将 DataFrame 转换为 ORM 对象列表
        objects = []
        for _, row in df.iterrows():
            # 创建 ORM 对象，使用字典解包，自动过滤掉不在类定义中的字段
            obj_data = row.to_dict()

            # 如果ORM类有自定义的创建方法，使用它
            if hasattr(orm_class, 'create_from_dict'):
                obj = orm_class.create_from_dict(obj_data)
            else:
                # 否则直接使用构造函数
                # 获取类的列名
                column_names = [column.key for column in orm_class.__table__.columns]
                # 只保留有效的字段
                filtered_data = {k: v for k, v in obj_data.items() if k in column_names}
                obj = orm_class(**filtered_data)

            objects.append(obj)

        try:
            # 批量添加对象
            session.add_all(objects)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"保存数据到 MySQL 失败: {str(e)}")
            return False
        finally:
            session.close()

    except Exception as e:
        print(f"连接数据库失败: {str(e)}")
        return False


if __name__ == "__main__":
    save_to_mysql_orm()
