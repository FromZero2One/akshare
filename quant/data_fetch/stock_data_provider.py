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
from quant.data_fetch.stock_data_save_script import stock_zh_a_hist_orm_incremental

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
    
    def get_stock_name_list(self, symbols: Optional[list[str]] = None) -> pd.DataFrame:
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


def main():
    """
    StockDataProvider 功能测试
    
    测试内容：
      1. 获取股票列表
      2. 获取单只股票历史数据
      3. 验证数据完整性检查
      4. 自动增量拉取测试
    """
    import logging
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("StockDataProvider 功能测试开始")
    logger.info("=" * 60)
    
    # 初始化数据提供者
    provider = StockDataProvider(adjust="qfq")
    
    # 测试1：获取股票列表
    logger.info("\n【测试1】获取股票列表")
    stock_list_df = provider.get_stock_name_list(symbols=['601398', '600519', '601399'])
    logger.info(f"✓ 获取到 {len(stock_list_df)} 只股票")
    print(stock_list_df.to_string(index=False))
    
    # 测试2：遍历获取历史数据
    logger.info("\n【测试2】获取历史数据（自动增量更新）")
    for _, stock_info in stock_list_df.iterrows():
        symbol = stock_info['symbol']
        stock_name = stock_info['stock_name']
        
        logger.info(f"\n{'─' * 60}")
        logger.info(f"处理股票: {symbol}[{stock_name}]")
        
        # 获取历史数据（会自动检查并拉取增量数据）
        history_df = provider.get_history_data(
            symbol=symbol,
            stock_name=stock_name,
            min_days=100
        )
        
        if history_df is not None:
            logger.info(f"✓ 成功获取 {len(history_df)} 天历史数据")
            logger.info(f"  日期范围: {history_df['date'].min()} ~ {history_df['date'].max()}")
            logger.info(f"  最新收盘价: {history_df.iloc[-1]['close']:.2f}")
            
            # 显示前5行和后5行数据
            print("\n前5行数据:")
            print(history_df.head(5).to_string(index=False))
            print("\n后5行数据:")
            print(history_df.tail(5).to_string(index=False))
        else:
            logger.warning(f"✗ 无法获取 {symbol} 的历史数据（数据不足）")
    
    # 测试3：获取全部股票列表（示例）
    logger.info("\n【测试3】获取全部股票列表（前10只）")
    all_stocks = provider.get_stock_name_list()
    logger.info(f"数据库共有 {len(all_stocks)} 只股票")
    print(all_stocks.head(10).to_string(index=False))
    
    logger.info("\n" + "=" * 60)
    logger.info("StockDataProvider 功能测试完成 ✓")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
