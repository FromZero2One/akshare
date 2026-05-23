#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2025/9/4 19:00
Desc: 示例脚本，展示如何使用SQLAlchemy ORM保存数据到数据库

https://sqlalchemy.org.cn/
"""

from typing import Type, Optional
import pandas as pd
from sqlalchemy import Column, String, Float, DateTime, Double
from sqlalchemy import create_engine, MetaData, BigInteger
from sqlalchemy import select, delete, text
from sqlalchemy.orm import sessionmaker, declarative_base

from quant.utils.db_connection import db_manager, get_engine, get_session
from quant.utils.logger_config import get_quant_logger
from quant.utils.performance_monitor import monitored_operation
from quant.utils.cache import cache_result, query_cache
from quant.utils.exceptions import DataSaveError, DataQueryError

# 配置日志
logger = get_quant_logger()


def save_to_mysql_orm(df: pd.DataFrame = None, orm_class: Type = None, reBuild: bool = False):
    """
    使用ORM保存数据到数据库（使用默认配置）
    
    Parameters:
    -----------
    df : pd.DataFrame, optional
        要保存的数据
    orm_class : Type, optional
        ORM 类，用于映射到数据库表
    reBuild : bool, default False
        是否重建表
    """
    # 使用ORM保存数据到数据库（使用默认配置）
    success = save(
        df=df,
        orm_class=orm_class,
        reBuild=reBuild
    )

    if success:
        logger.info("数据成功保存到数据库")
    else:
        logger.error("数据保存失败")


#  支持先删除后插入的增量保存方式
def save_to_mysql_orm_incremental(df: pd.DataFrame = None, orm_class: Type = None, symbol: str = None,
                                  isDel: bool = False):
    """
    根据symbol增量保存数据到数据库
    
    Parameters:
    -----------
    df : pd.DataFrame, optional
        要保存的数据
    orm_class : Type, optional
        ORM 类，用于映射到数据库表
    symbol : str, optional
        股票代码，用于查询已有数据
    isDel : bool, default False
        是否先删除指定symbol的数据再插入
    """
    success = save_incremental(
        df=df,
        orm_class=orm_class,
        symbol=symbol,
        isDel=isDel
    )

    if success:
        if isDel:
            logger.info(f"股票 {symbol} 的数据成功删除旧数据并保存到数据库")
        else:
            logger.info(f"股票 {symbol} 的数据成功增量保存到数据库")
    else:
        logger.error(f"股票 {symbol} 的数据保存失败")


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
        # 数据验证
        if df is None or df.empty:
            raise DataSaveError(table_name=orm_class.__tablename__, reason="输入的 DataFrame 为空")
        
        engine = get_engine()

        # 删除现有表并重新创建（确保表结构与ORM定义一致）
        if reBuild:
            # 只删除指定的表
            orm_class.__table__.drop(engine, checkfirst=True)

        # 只创建指定的表
        orm_class.__table__.create(engine, checkfirst=True)

        # 获取Entity中定义的字段名（排除自增主键字段）
        entity_columns = []
        for column in orm_class.__table__.columns:
            # 如果字段是自增主键，则跳过
            if not (column.autoincrement and column.primary_key):
                entity_columns.append(column.name)

        # 验证 DataFrame 是否包含必要列
        missing_cols = set(entity_columns) - set(df.columns)
        if missing_cols:
            raise DataSaveError(
                table_name=orm_class.__tablename__, 
                reason=f"DataFrame 缺少必要列: {missing_cols}"
            )

        # 只保留DataFrame中与Entity字段匹配的列
        filtered_df = df[entity_columns].copy()
        # 处理NaN值，将其替换为None以便正确插入MySQL数据库
        filtered_df = filtered_df.where(pd.notnull(filtered_df), None)
        filtered_df = filtered_df.replace({float('nan'): None, pd.NaT: None})

        # 将DataFrame转换为ORM对象列表
        records = []
        for _, row in filtered_df.iterrows():
            record = orm_class(**row.to_dict())
            records.append(record)

        # 使用上下文管理器确保会话正确关闭
        with get_session() as session:
            session.bulk_save_objects(records)

        logger.info(f"成功保存 {len(records)} 条记录到表 {orm_class.__tablename__}")
        return True

    except DataSaveError:
        # 重新抛出我们已经处理过的业务异常
        raise
    except Exception as e:
        logger.error(f"保存数据到 MySQL 失败: {e}", exc_info=True)
        raise DataSaveError(table_name=orm_class.__tablename__ if 'orm_class' in locals() else None, reason=str(e))


def save_incremental(df: pd.DataFrame, orm_class: Type, symbol: str, isDel: bool = False, adjust: str = None) -> bool:
    """
    根据symbol和adjust保存数据到数据库

    Parameters:
    -----------
    df : pd.DataFrame
        要保存的数据
    orm_class : Type
        ORM 类，用于映射到数据库表
    symbol : str
        股票代码，用于查询已有数据
    isDel : bool
        是否先删除指定symbol的数据再插入，默认为False
    adjust : str, optional
        复权类型 (qfq/hfq/None)，如果提供则只清理该类型的旧数据
    Returns:
    --------
    bool
        保存成功返回True，失败返回False
    """
    try:
        # 数据验证
        if df is None or df.empty:
            logger.warning("DataFrame 为空，无法保存")
            return False
        
        engine = get_engine()
        
        # 创建表（如果不存在）
        orm_class.__table__.create(engine, checkfirst=True)

        # 准备删除条件
        delete_conditions = [orm_class.symbol == symbol]
        if adjust and hasattr(orm_class, 'adjust'):
            delete_conditions.append(orm_class.adjust == adjust)
            logger.info(f"正在清理股票 {symbol} ({adjust}) 的历史数据...")
        else:
            logger.info(f"正在清理股票 {symbol} 的所有历史数据...")

        # 执行删除操作
        with get_session() as session:
            delete_stmt = delete(orm_class).where(*delete_conditions)
            result = session.execute(delete_stmt)
            if result.rowcount > 0:
                logger.info(f"已删除 {result.rowcount} 条旧记录")

        # 获取Entity中定义的字段名（排除自增主键字段）
        entity_columns = []
        for column in orm_class.__table__.columns:
            # 如果字段是自增主键，则跳过
            if not (column.autoincrement and column.primary_key):
                entity_columns.append(column.name)

        # 验证 DataFrame 是否包含必要列
        missing_cols = set(entity_columns) - set(df.columns)
        if missing_cols:
            logger.error(f"DataFrame 缺少必要列: {missing_cols}")
            return False

        # 只保留DataFrame中与Entity字段匹配的列
        filtered_df = df[entity_columns].copy()
        # 处理NaN值，将其替换为None以便正确插入MySQL数据库
        filtered_df = filtered_df.where(pd.notnull(filtered_df), None)
        filtered_df = filtered_df.replace({float('nan'): None, pd.NaT: None})

        # 将DataFrame转换为ORM对象列表
        records = []
        for _, row in filtered_df.iterrows():
            record = orm_class(**row.to_dict())
            records.append(record)

        # 使用上下文管理器批量插入数据
        with get_session() as session:
            session.bulk_save_objects(records)

        logger.info(f"成功插入 {len(records)} 条新数据到表 {orm_class.__tablename__}")
        return True

    except Exception as e:
        logger.error(f"保存数据到 MySQL 失败: {e}", exc_info=True)
        return False


# ticker 股票代码
@monitored_operation("数据库查询")
def get_mysql_data_to_df(orm_class: Type = None, table_name: str = None, adjust="qfq", symbol: str = None):
    """
    通过ORM类获取表名并查询数据
    
    Parameters:
    -----------
    orm_class : Type, optional
        ORM 类，用于映射到数据库表
    table_name : str, optional
        表名，如果提供则直接使用
    adjust : str, default "qfq"
        复权类型
    symbol : str, optional
        股票代码，如果提供则只查询该股票的数据
        
    Returns:
    --------
    pd.DataFrame
        查询结果
    """
    if table_name is None:
        if orm_class is None:
            raise ValueError("必须提供 orm_class 或 table_name")
        # 获取指定类的表名
        table_name = orm_class.__tablename__

    try:
        engine = get_engine()
        
        # 反射数据库结构（自动获取表信息）
        metadata = MetaData()
        metadata.reflect(bind=engine)

        # 检查表是否存在
        if table_name not in metadata.tables:
            logger.warning(f"表 {table_name} 不存在")
            return pd.DataFrame()
            
        target_table = metadata.tables[table_name]  # 获取对应的表

        # 构建查询
        if symbol:
            stmt = (select(target_table)
                    .where(target_table.c.symbol == symbol, target_table.c.adjust == adjust)
                    .order_by(target_table.c.symbol.asc()))
        else:
            stmt = select(target_table).order_by(target_table.c.symbol.desc())  # 查询表的所有数据

        # 使用 Pandas 读取查询结果
        with engine.connect() as connection:
            df = pd.read_sql(stmt, con=connection)

        logger.debug(f"从表 {table_name} 查询到 {len(df)} 条记录")
        return df
        
    except Exception as e:
        logger.error(f"查询数据库失败: {e}", exc_info=True)
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
            if series.name == 'SECURITY_CODE' or series.name == 'symbol' or series.name == 'Stock_Code':
                return String(10)
            if series.name == 'date':
                return DateTime
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
            return Double
        elif 'datetime' in str(series.dtype):
            return DateTime
        else:
            return String(255)

    try:
        # 数据验证
        if df is None or df.empty:
            logger.warning("DataFrame 为空，无法保存")
            return False
            
        engine = get_engine()
        
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
        if reBuild:
            # 只删除指定的表
            entity_class.__table__.drop(engine, checkfirst=True)

        # 创建表
        # 只创建指定的表
        entity_class.__table__.create(engine, checkfirst=True)

        # 将DataFrame转换为ORM对象列表
        records = []
        for _, row in df.iterrows():
            # 过滤掉不在Entity定义中的列
            record_data = {col: row[col] for col in df.columns if col in attrs}
            record = entity_class(**record_data)
            records.append(record)

        # 使用上下文管理器批量插入数据
        with get_session() as session:
            session.bulk_save_objects(records)

        logger.info(f"成功保存 {len(records)} 条记录到表 {table_name}")
        return True

    except Exception as e:
        logger.error(f"保存数据到数据库失败: {e}", exc_info=True)
        return False


def execute_sql_delete(sql: str, params: dict = None) -> bool:
    """
    通过SQL语句删除数据库数据（支持参数化查询防止SQL注入）
    
    Parameters:
    -----------
    sql : str
        SQL删除语句，使用 :param_name 作为占位符
    params : dict, optional
        参数字典，例如 {"symbol": "000001"}
        
    Returns:
    --------
    bool
        执行成功返回True，失败返回False
    """
    try:
        engine = get_engine()
        with engine.connect() as connection:
            result = connection.execute(text(sql), params or {})
            connection.commit()
        logger.debug(f"执行SQL删除成功")
        return True
    except Exception as e:
        logger.error(f"执行SQL删除失败: {e}", exc_info=True)
        return False


def execute_sql_query(sql_query: str) -> pd.DataFrame:
    """
    通过SQL语句直接查询数据库数据
    
    Parameters:
    -----------
    sql_query : str
        SQL查询语句
        
    Returns:
    --------
    pd.DataFrame
        查询结果
    """
    try:
        engine = get_engine()
        with engine.connect() as connection:
            df = pd.read_sql(sql_query, con=connection)
        logger.debug(f"执行SQL查询成功，返回 {len(df)} 条记录")
        return df
    except Exception as e:
        logger.error(f"执行SQL查询失败: {e}", exc_info=True)
        return pd.DataFrame()


# 使用示例
# Base = declarative_base()
# entity_class = save_with_auto_entity(df, 'my_table', Base)


if __name__ == '__main__':
    df = execute_sql_query("SELECT * FROM stock_name_entity LIMIT 5;")
    print(df)
