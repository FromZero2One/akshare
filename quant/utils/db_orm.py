#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2025/9/4 19:00
Desc: 示例脚本，展示如何使用SQLAlchemy ORM保存数据到数据库

https://sqlalchemy.org.cn/
"""

from typing import Type

import pandas as pd
from sqlalchemy import Column, String, Float, DateTime
from sqlalchemy import create_engine, MetaData, BigInteger
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker, declarative_base

from quant.utils.db_config import DB_CONFIG

# 使用传入的参数或配置中的默认值
host = DB_CONFIG['host']
port = DB_CONFIG['port']
user = DB_CONFIG['user']
password = DB_CONFIG['password']
database = DB_CONFIG['database']

# 创建数据库连接   echo=False 不打印sql
engine = create_engine(
    f'mysql+pymysql://{user}:{password}@{host}:{port}/{database}',
    echo=True
)


def save_to_mysql_orm(df: pd.DataFrame = None, orm_class: Type = None, reBuild: bool = False):
    # 使用ORM保存数据到数据库（使用默认配置）
    success = save(
        df=df,
        orm_class=orm_class,
        reBuild=reBuild
    )

    if success:
        print("数据成功保存到数据库")
    else:
        print("数据保存失败")


def save(df: pd.DataFrame, orm_class: Type, reBuild: bool = False) -> bool:
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
        if reBuild:
            # 删除所有表
            # orm_class.metadata.drop_all(engine)
            # 只删除指定的表
            orm_class.__table__.drop(engine, checkfirst=True)

        # 这行代码会根据 ORM 类的定义创建相应的数据库表。如果表已经存在，则不会重复创建。
        # orm_class.metadata.create_all(engine)
        # 只创建指定的表
        orm_class.__table__.create(engine, checkfirst=True)

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
        # 处理NaN值，将其替换为None以便正确插入MySQL数据库
        # 使用两种方法确保所有NaN值都被正确处理
        filtered_df = filtered_df.where(pd.notnull(filtered_df), None)
        filtered_df = filtered_df.replace({float('nan'): None, pd.NaT: None})

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
def get_mysql_data_to_df(orm_class: Type = None, table_name: str = None, adjust="", Ticker: str = None):
    """
    通过ORM类获取表名并查询数据
    """
    if table_name is None:
        # 获取指定类的表名
        table_name = orm_class.__tablename__

    # 反射数据库结构（自动获取表信息）
    metadata = MetaData()
    metadata.reflect(bind=engine)

    # 检查表是否存在
    if table_name in metadata.tables:
        target_table = metadata.tables[table_name]  # 获取对应的表

        # 构建查询
        if Ticker:
            stmt = select(target_table).where(target_table.c.Ticker == Ticker, target_table.c.adjust == adjust)
        else:
            stmt = select(target_table)  # 查询表的所有数据

        # 使用 Pandas 读取查询结果
        with engine.connect() as connection:
            df = pd.read_sql(stmt, con=connection)

        # print(df)
        return df
    else:
        print(f"表 {table_name} 不存在")
        return pd.DataFrame()


column_comments = {"index": "序号",
                   "SECURITY_INNER_CODE": "-",
                   "SECURITY_CODE": "代码",
                   "SECUCODE": "-",
                   "TRADE_DATE": "交易日",
                   "SECURITY_NAME_ABBR": "名称",
                   "SUPERDEAL_INFLOW": "-",
                   "SUPERDEAL_OUTFLOW": "-",
                   "PRIME_INFLOW": "-",
                   "CLOSE_PRICE": "最新价",
                   "CHANGE_RATE": "涨跌幅",
                   "TRADE_MARKET_CODE": "-",
                   "TURNOVERRATE": "换手率",
                   "PRIME_COST": "主力成本",
                   "PE_DYNAMIC": "市盈率",
                   "PRIME_COST_20DAYS": "-",
                   "PRIME_COST_60DAYS": "-",
                   "ORG_PARTICIPATE": "机构参与度",
                   "PARTICIPATE_TYPE": "-",
                   "BIGDEAL_INFLOW": "-",
                   "BIGDEAL_OUTFLOW": "-",
                   "BUY_SUPERDEAL_RATIO": "-",
                   "BUY_BIGDEAL_RATIO": "-",
                   "RATIO": "-",
                   "RATIO_3DAYS": "-",
                   "RATIO_50DAYS": "-",
                   "TOTALSCORE": "综合得分",
                   "RANK_UP": "上升",
                   "RANK": "目前排名",
                   "FOCUS": "关注指数",
                   "SECURITY_TYPE_CODE": "-",
                   "LISTING_STATE": "-", }

# SQLAlchemy的declarative_base基类
Base = declarative_base()


def save_with_auto_entity(df: pd.DataFrame, table_name: str, reBuild: bool = False,
                          table_comment: str = None) -> bool:
    """
    自动根据DataFrame创建Entity并保存数据

    Parameters:
    df: 要保存的DataFrame
    table_name: 数据库表名
    base_class: SQLAlchemy的declarative_base基类
    rebuild: 是否重建表
    table_comment: 表注释
    """

    def infer_sql_type(series):
        if series.dtype == 'object':
            sample_data = series.dropna().iloc[:5]
            # 股票代码直接转字符串
            if series.name == 'SECURITY_CODE' or series.name == 'Ticker' or series.name == 'Stock_Code':
                return String(10)
            # 先尝试数值转换
            try:
                pd.to_numeric(sample_data)
                return Float  # 数值类型
            except:
                pass
            # 再尝试日期时间转换（更严格的检查）
            try:
                # 检查是否真的是日期格式的字符串
                if all(isinstance(x, str) and
                       (len(x) > 8 and ('-' in x or '/' in x or ':' in x))
                       for x in sample_data):
                    pd.to_datetime(sample_data)
                    return DateTime
            except:
                pass

            # 默认为字符串
            max_len = series.astype(str).str.len().max()
            return String(max_len if max_len and max_len < 65535 else 65535)
        elif series.dtype in ['int64', 'int32']:
            return BigInteger
        elif series.dtype in ['float64', 'float32']:
            # 浮点数应该映射为Float而不是DateTime
            return Float
        elif 'datetime' in str(series.dtype):
            return DateTime
        else:
            return String(255)

    try:
        # df.dropna()  NaN 值的行或列删除
        df = df.fillna("0")  # 将 NaN 替换为 ""
        # 动态创建Entity类
        attrs = {'__tablename__': table_name}

        # 添加表注释
        if table_comment:
            attrs['__table_args__'] = {'comment': table_comment}

        # 添加自增主键index字段
        attrs['index'] = Column(BigInteger, primary_key=True, autoincrement=True)

        # 为每列创建Column定义
        for column_name in df.columns:
            sql_type = infer_sql_type(df[column_name])
            attrs[column_name] = Column(sql_type)

            # 添加字段注释
            if column_comments and column_name in column_comments:
                attrs[column_name].comment = column_comments[column_name]

        # 动态创建Entity类
        entity_class = type(table_name.capitalize() + 'Entity', (Base,), attrs)

        # 删除并重建表（如果需要）
        if rebuild:
            # entity_class.metadata.drop_all(engine)
            # 只删除指定的表
            entity_class.__table__.drop(engine, checkfirst=True)

        # 创建表
        # entity_class.metadata.create_all(engine)
        # 只创建指定的表
        entity_class.__table__.create(engine, checkfirst=True)

        # 创建会话
        Session = sessionmaker(bind=engine)
        session = Session()

        # 将DataFrame转换为ORM对象列表
        records = []
        for _, row in df.iterrows():
            # 过滤掉不在Entity定义中的列
            record_data = {col: row[col] for col in df.columns if col in attrs}
            record = entity_class(**record_data)
            records.append(record)

        # 批量插入数据
        session.bulk_save_objects(records)
        session.commit()
        session.close()

        return True

    except Exception as e:
        print(f"保存数据到数据库失败: {e}")
        return False

# 使用示例
# Base = declarative_base()
# entity_class = save_with_auto_entity(df, 'my_table', Base)
