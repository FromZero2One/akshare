#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2025/1/15
Desc: 数据库连接管理器 - 单例模式管理数据库引擎和会话
"""

from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from .db_config import DB_CONFIG, DB_CONFIG_PRO, should_use_pro_db


class DatabaseManager:
    """
    数据库连接管理器（单例模式）
    
    负责管理数据库引擎和会话的生命周期，避免重复创建连接
    """
    
    _instance = None
    _engine = None
    _session_factory = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, use_pro: bool = None, echo_sql: bool = False):
        """
        初始化数据库管理器
        
        Args:
            use_pro: 是否使用生产环境配置（默认从环境变量 DB_USE_PRO 读取）
            echo_sql: 是否打印SQL语句（调试用）
        """
        # 防止重复初始化
        if self._engine is not None:
            return
        
        # 如果未指定 use_pro，则从环境变量读取
        if use_pro is None:
            use_pro = should_use_pro_db()
            
        config = DB_CONFIG_PRO if use_pro else DB_CONFIG
        
        host = config['host']
        port = config['port']
        user = config['user']
        password = config['password']
        database = config['database']
        
        # 创建数据库URL
        url = f'mysql+pymysql://{user}:{password}@{host}:{port}/{database}'
        
        # 创建引擎（带连接池配置）
        self._engine = create_engine(
            url,
            echo=echo_sql,
            pool_size=10,           # 连接池大小
            max_overflow=20,        # 最大溢出连接数
            pool_recycle=3600,      # 连接回收时间（秒）
            pool_pre_ping=True,     # 连接前检查有效性
            pool_timeout=30         # 获取连接超时时间（秒）
        )
        
        # 创建会话工厂
        self._session_factory = sessionmaker(bind=self._engine)
    
    @property
    def engine(self):
        """获取数据库引擎"""
        if self._engine is None:
            raise RuntimeError("DatabaseManager 未初始化")
        return self._engine
    
    @property
    def session_factory(self):
        """获取会话工厂"""
        if self._session_factory is None:
            raise RuntimeError("DatabaseManager 未初始化")
        return self._session_factory
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        获取数据库会话（上下文管理器）
        
        Yields:
            Session: 数据库会话对象
            
        Example:
            with db_manager.get_session() as session:
                session.query(...)
        """
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def dispose(self):
        """销毁连接池（通常在应用关闭时调用）"""
        if self._engine:
            self._engine.dispose()
            self._engine = None
            self._session_factory = None


# 创建全局默认实例
# use_pro 参数从环境变量 DB_USE_PRO 自动读取（默认 true）
db_manager = DatabaseManager(echo_sql=False)

# 便捷函数
def get_engine():
    """获取数据库引擎"""
    return db_manager.engine

def get_session():
    """
    获取数据库会话（上下文管理器）
    
    Example:
        from quant.utils.db_connection import get_session
        
        with get_session() as session:
            result = session.execute(...)
    """
    return db_manager.get_session()
