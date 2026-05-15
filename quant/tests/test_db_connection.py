#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2025/1/15
Desc: 数据库连接管理器单元测试
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestDatabaseManager(unittest.TestCase):
    """测试数据库连接管理器"""
    
    def setUp(self):
        """测试前准备"""
        # 清除单例实例，确保每次测试都是干净的
        from quant.utils import db_connection
        db_connection.DatabaseManager._instance = None
        db_connection.DatabaseManager._engine = None
        db_connection.DatabaseManager._session_factory = None
    
    def test_singleton_pattern(self):
        """测试单例模式"""
        from quant.utils.db_connection import DatabaseManager
        
        # 创建两个实例
        manager1 = DatabaseManager(use_pro=False, echo_sql=False)
        manager2 = DatabaseManager(use_pro=False, echo_sql=False)
        
        # 应该是同一个实例
        self.assertIs(manager1, manager2)
    
    def test_get_engine(self):
        """测试获取引擎"""
        from quant.utils.db_connection import get_engine
        
        engine = get_engine()
        
        # 引擎不应该为None
        self.assertIsNotNone(engine)
        
        # 再次获取应该是同一个引擎
        engine2 = get_engine()
        self.assertIs(engine, engine2)
    
    @patch('quant.utils.db_connection.create_engine')
    def test_engine_creation_with_pool_config(self, mock_create_engine):
        """测试引擎创建时包含连接池配置"""
        from quant.utils.db_connection import DatabaseManager
        
        # 重置单例
        DatabaseManager._instance = None
        DatabaseManager._engine = None
        
        # 创建管理器
        manager = DatabaseManager(use_pro=False, echo_sql=False)
        
        # 验证 create_engine 被调用且包含连接池参数
        mock_create_engine.assert_called_once()
        call_kwargs = mock_create_engine.call_args[1]
        
        self.assertIn('pool_size', call_kwargs)
        self.assertEqual(call_kwargs['pool_size'], 10)
        self.assertIn('max_overflow', call_kwargs)
        self.assertEqual(call_kwargs['max_overflow'], 20)
        self.assertIn('pool_recycle', call_kwargs)
        self.assertEqual(call_kwargs['pool_recycle'], 3600)
        self.assertIn('pool_pre_ping', call_kwargs)
        self.assertTrue(call_kwargs['pool_pre_ping'])


class TestDataValidation(unittest.TestCase):
    """测试数据验证功能"""
    
    def test_empty_dataframe_validation(self):
        """测试空DataFrame验证"""
        import pandas as pd
        from quant.utils.db_orm import save
        from quant.entity.BaseEntity import BaseEntity
        
        # 创建空的DataFrame
        empty_df = pd.DataFrame()
        
        # 创建一个简单的测试ORM类
        class TestEntity(BaseEntity):
            __tablename__ = "test_table"
        
        # 应该返回False
        result = save(empty_df, TestEntity, reBuild=False)
        self.assertFalse(result)
    
    def test_none_dataframe_validation(self):
        """测试None DataFrame验证"""
        from quant.utils.db_orm import save
        from quant.entity.BaseEntity import BaseEntity
        
        class TestEntity(BaseEntity):
            __tablename__ = "test_table"
        
        # 应该返回False
        result = save(None, TestEntity, reBuild=False)
        self.assertFalse(result)


class TestLoggerConfig(unittest.TestCase):
    """测试日志配置"""
    
    def test_logger_creation(self):
        """测试日志记录器创建"""
        from quant.utils.logger_config import get_quant_logger
        
        logger = get_quant_logger()
        
        # logger不应该为None
        self.assertIsNotNone(logger)
        
        # 应该有handlers
        self.assertTrue(len(logger.handlers) > 0)
    
    def test_logger_singleton(self):
        """测试日志记录器单例"""
        from quant.utils.logger_config import LoggerConfig
        
        logger1 = LoggerConfig.get_logger("test_logger")
        logger2 = LoggerConfig.get_logger("test_logger")
        
        # 应该是同一个logger
        self.assertIs(logger1, logger2)


class TestEnvConfig(unittest.TestCase):
    """测试环境变量配置"""
    
    def test_db_config_structure(self):
        """测试数据库配置结构"""
        from quant.utils.db_config import DB_CONFIG, DB_CONFIG_PRO
        
        # 检查必需的配置项
        required_keys = ['host', 'port', 'user', 'password', 'database']
        
        for key in required_keys:
            self.assertIn(key, DB_CONFIG, f"DB_CONFIG 缺少 {key}")
            self.assertIn(key, DB_CONFIG_PRO, f"DB_CONFIG_PRO 缺少 {key}")
    
    def test_port_is_integer(self):
        """测试端口号是整数"""
        from quant.utils.db_config import DB_CONFIG
        
        self.assertIsInstance(DB_CONFIG['port'], int)


class TestEntityRepr(unittest.TestCase):
    """测试Entity的__repr__方法"""
    
    def test_stock_name_entity_repr(self):
        """测试StockNameEntity的__repr__"""
        from quant.entity.StockNameEntity import StockNameEntity
        
        entity = StockNameEntity()
        entity.id = 1
        entity.symbol = "601398"
        entity.stock_name = "工商银行"
        
        repr_str = repr(entity)
        
        # 应该包含正确的类名和字段
        self.assertIn("StockNameEntity", repr_str)
        self.assertIn("symbol='601398'", repr_str)
        self.assertIn("stock_name='工商银行'", repr_str)
    
    def test_stock_value_entity_repr(self):
        """测试StockValueEntity的__repr__"""
        from quant.entity.StockValueEntity import StockValueEntity
        
        entity = StockValueEntity()
        entity.TRADE_DATE = None
        entity.symbol = "601398"
        
        repr_str = repr(entity)
        
        # 应该包含正确的类名
        self.assertIn("StockValueEntity", repr_str)
        self.assertIn("symbol='601398'", repr_str)
    
    def test_stock_history_daily_info_entity_repr(self):
        """测试StockHistoryDailyInfoEntity的__repr__"""
        from quant.entity.StockHistoryDailyInfoEntity import StockHistoryDailyInfoEntity
        
        entity = StockHistoryDailyInfoEntity()
        entity.symbol = "601398"
        entity.adjust = "qfq"
        
        repr_str = repr(entity)
        
        # 应该包含正确的类名和字段
        self.assertIn("StockHistoryDailyInfoEntity", repr_str)
        self.assertIn("symbol='601398'", repr_str)
        self.assertIn("adjust='qfq'", repr_str)


if __name__ == '__main__':
    unittest.main(verbosity=2)
