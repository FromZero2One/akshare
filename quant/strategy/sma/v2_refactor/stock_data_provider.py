#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2026/6/5
Desc: 股票数据提供者 - 简化版

核心职责：
  - 获取股票列表
  - 获取历史数据（自动确保数据完整）
"""

import logging
from datetime import datetime
from typing import Optional

import pandas as pd

import quant.utils.db_orm as db_orm
from quant.entity.StockHistoryDailyInfoEntity import StockHistoryDailyInfoEntity
from quant.entity.StockNameEntity import StockNameEntity
from quant.entity.script.stock_data_save_script import stock_zh_a_hist_orm_incremental

logger = logging.getLogger(__name__)


class StockDataProvider:
    """
    股票数据提供者（简化版）
    
    提供两个核心方法：
      - get_stock_list(): 获取股票列表
      - get_history_data(): 获取历史数据（自动确保数据完整）
    """
    
    def __init__(self, adjust: str = "qfq"):
        """
        Args:
            adjust: 复权类型 (qfq=前复权, hfq=后复权)
        """
        self.adjust = adjust
    
    def get_stock_list(self, symbols: Optional[list[str]] = None) -> pd.DataFrame:
        """
        获取股票列表
        
        Args:
            symbols: 指定股票代码列表，None则返回全部
            
        Returns:
            DataFrame with columns: symbol, stock_name
        """
        df = db_orm.get_mysql_data_to_df(orm_class=StockNameEntity)
        
        if df.empty:
            logger.warning("数据库中无股票列表")
            return pd.DataFrame(columns=['symbol', 'stock_name'])
        
        # 过滤指定股票
        if symbols:
            df = df[df['symbol'].isin(symbols)]
        
        return df[['symbol', 'stock_name']].drop_duplicates(subset=['symbol'])
    
    def get_history_data(
        self, 
        symbol: str, 
        stock_name: str = "",
        min_days: int = 100
    ) -> Optional[pd.DataFrame]:
        """
        获取股票历史数据（自动确保数据完整）
        
        流程：
          1. 检查数据是否完整（最新日期在5天内）
          2. 如果不完整，自动拉取增量数据
          3. 从数据库读取并返回
        
        Args:
            symbol: 股票代码
            stock_name: 股票名称（用于日志）
            min_days: 最小数据天数要求，不足则返回None
            
        Returns:
            DataFrame with historical data, or None if insufficient
        """
        # 第1步：检查数据完整性
        is_complete = self._check_data_complete(symbol)
        
        # 第2步：数据不完整则拉取
        if not is_complete:
            logger.info(f"→ {symbol}[{stock_name}] 数据需更新，开始拉取...")
            try:
                success = stock_zh_a_hist_orm_incremental(
                    symbol=symbol,
                    adjust=self.adjust,
                    isDel=False  # 增量模式
                )
                if not success:
                    logger.warning(f"✗ 拉取 {symbol} 数据失败")
                    return None
            except Exception as e:
                logger.error(f"✗ 拉取 {symbol} 数据异常: {e}")
                return None
        
        # 第3步：从数据库读取
        df = db_orm.get_mysql_data_to_df(
            orm_class=StockHistoryDailyInfoEntity,
            symbol=symbol,
            adjust=self.adjust
        )
        
        if df.empty:
            logger.warning(f"{symbol} 历史数据为空")
            return None
        
        # 第4步：检查数据量
        if len(df) < min_days:
            logger.warning(f"{symbol} 数据不足{min_days}天 (实际{len(df)}天)")
            return None
        
        return df
    
    def _check_data_complete(self, symbol: str, days_threshold: int = 5) -> bool:
        """
        检查数据是否完整（内部方法）
        
        Args:
            symbol: 股票代码
            days_threshold: 允许的最大天数差距
            
        Returns:
            True if data is up-to-date
        """
        # 查询最新日期（使用ORM查询，避免SQL注入）
        df = db_orm.get_mysql_data_to_df(
            orm_class=StockHistoryDailyInfoEntity,
            symbol=symbol,
            adjust=self.adjust
        )
        
        if df.empty or 'date' not in df.columns:
            return False
        
        latest_date = df['date'].max()
        
        # 转换为日期对象
        if isinstance(latest_date, str):
            latest_date = datetime.strptime(latest_date, '%Y-%m-%d').date()
        elif hasattr(latest_date, 'date'):
            latest_date = latest_date.date()
        
        # 计算差距
        today = datetime.now().date()
        days_diff = (today - latest_date).days
        
        return days_diff <= days_threshold
