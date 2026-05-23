#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据获取模块 - 支持多种数据源、数据库和缓存

数据获取优先级：
1. MySQL数据库（优先）- 避免重复网络请求
2. AKShare API（主要在线数据源）
   - 东方财富（主要）
   - 新浪财经（备用1）
   - 腾讯财经（备用2）
3. 本地文件缓存（pickle缓存）

参考逻辑：quant/utils/db_orm.get_mysql_data_to_df + quant/entity/script/stock_data_save_script
"""

import os
import sys
import json
import logging
import pickle
import time
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, List, Dict, Any
import pandas as pd
import akshare as ak
import hashlib

# 添加项目根目录路径，以便正确导入 quant 包（作为 Python 包而非目录）
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if os.path.exists(project_root) and project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    import quant.utils.db_orm as db_orm
    from quant.entity.StockHistoryDailyInfoEntity import StockHistoryDailyInfoEntity
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    StockHistoryDailyInfoEntity = None

logger = logging.getLogger(__name__)


class DataFetcher:
    """数据获取器 - 支持多种数据源、数据库和缓存
    
    数据获取优先级：
    1. MySQL数据库 - 通过 quant 模块的 ORM 查询
    2. AKShare API - 东方财富/新浪/腾讯自动降级
    3. 本地 pickle 缓存 - 文件级缓存
    
    当数据库有数据时直接使用，无数据时从API拉取并自动保存到数据库。
    """
    
    def __init__(self, cache_enabled: bool = True, cache_dir: str = None, cache_expiry_days: int = 7,
                 db_enabled: bool = True, db_save_enabled: bool = True):
        self.cache_enabled = cache_enabled
        self.db_enabled = db_enabled and DB_AVAILABLE  # 数据库功能需要 quant 模块可用
        self.db_save_enabled = db_save_enabled and self.db_enabled  # 是否自动保存拉取数据到数据库
        
        if cache_dir is None:
            cache_dir = os.path.join(os.path.dirname(__file__), "../../data/cache")
        
        self.cache_dir = cache_dir
        self.cache_expiry_days = cache_expiry_days
        
        # 确保缓存目录存在
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # 初始化数据源映射
        self.data_sources = {
            'mysql': self._fetch_from_mysql,       # 优先：数据库
            'akshare': self._fetch_from_akshare,    # 主要：AKShare API（多源降级）
            'tushare': self._fetch_from_tushare,    # 预留：Tushare
            'local': self._fetch_from_local         # 预留：本地文件
        }
        
        # 数据源降级策略（用于在线数据获取）
        self.online_fallback_sources = [
            ("东方财富", self._fetch_from_eastmoney),
            ("腾讯证券", self._fetch_from_sina),      # 备用1: 实际调用腾讯证券
            ("腾讯证券2", self._fetch_from_tencent),   # 备用2: 同源但不同重试窗口
        ]
        
        logger.info(f"数据获取器初始化完成 - 缓存: {'启用' if cache_enabled else '禁用'}, "
                    f"数据库: {'启用' if self.db_enabled else '禁用'}, "
                    f"自动保存到DB: {'启用' if self.db_save_enabled else '禁用'}")
    
    def _get_cache_key(self, symbol: str, adjust: str, source: str) -> str:
        """生成缓存文件名"""
        key = f"{symbol}_{adjust}_{source}"
        return hashlib.md5(key.encode()).hexdigest()
    
    def _check_cache(self, cache_key: str) -> bool:
        """检查缓存是否存在且有效"""
        if not self.cache_enabled:
            return False
        
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.pkl")
        
        if not os.path.exists(cache_file):
            return False
        
        # 检查缓存是否过期
        file_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
        expiry_time = datetime.now() - timedelta(days=self.cache_expiry_days)
        
        if file_time < expiry_time:
            logger.debug(f"缓存已过期: {cache_file}")
            return False
        
        logger.debug(f"找到有效缓存: {cache_file}")
        return True
    
    def _save_to_cache(self, cache_key: str, data: pd.DataFrame):
        """保存数据到缓存"""
        if not self.cache_enabled:
            return
        
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.pkl")
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(data, f)
            logger.debug(f"数据已缓存: {cache_file}")
        except Exception as e:
            logger.warning(f"缓存失败: {e}")
    
    def _load_from_cache(self, cache_key: str) -> pd.DataFrame:
        """从缓存加载数据"""
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.pkl")
        try:
            with open(cache_file, 'rb') as f:
                data = pickle.load(f)
            logger.debug(f"从缓存加载数据: {cache_file}")
            return data
        except Exception as e:
            logger.error(f"加载缓存失败: {e}")
            return pd.DataFrame()
    
    # ==================== 数据库数据源 ====================
    
    def _fetch_from_mysql(self, symbol: str, adjust: str = "qfq") -> pd.DataFrame:
        """从MySQL数据库获取数据（优先数据源）
        
        参考 quant/utils/db_orm.get_mysql_data_to_df 的查询逻辑
        """
        if not self.db_enabled:
            logger.debug("数据库功能未启用，跳过")
            return pd.DataFrame()
        
        try:
            logger.info(f"从数据库获取数据: {symbol} ({adjust})")
            df = db_orm.get_mysql_data_to_df(
                orm_class=StockHistoryDailyInfoEntity,
                adjust=adjust,
                symbol=symbol
            )
            
            if df.empty:
                logger.info(f"数据库中无 {symbol} ({adjust}) 的数据")
                return pd.DataFrame()
            
            # 从数据库返回的数据中提取回测所需的标准列
            required_columns = ['date', 'open', 'close', 'high', 'low', 'volume']
            available_columns = [col for col in required_columns if col in df.columns]
            
            if len(available_columns) < len(required_columns):
                missing = set(required_columns) - set(available_columns)
                logger.warning(f"数据库数据缺少必要列: {missing}")
                return pd.DataFrame()
            
            result_df = df[required_columns].copy()
            
            # 去重：同一日期可能有多条记录（数据库增量保存可能导致重复）
            result_df = result_df.drop_duplicates(subset=['date'], keep='last')
            
            # 确保日期格式正确
            result_df['date'] = pd.to_datetime(result_df['date'])
            # 按日期排序
            result_df = result_df.sort_values('date').reset_index(drop=True)
            
            logger.info(f"从数据库成功获取 {symbol} 数据，共 {len(result_df)} 条记录")
            return result_df
            
        except Exception as e:
            logger.warning(f"从数据库获取数据失败 {symbol}: {e}")
            return pd.DataFrame()
    
    def _save_to_database(self, df: pd.DataFrame, symbol: str, adjust: str = "qfq"):
        """将拉取的数据保存到MySQL数据库，供下次直接使用
        
        参考 quant/utils/db_orm.save_to_mysql_orm_incremental 的保存逻辑
        使用 ak.stock_zh_a_hist_orm 获取ORM格式数据，确保与数据库表结构一致
        """
        if not self.db_save_enabled:
            return
        
        try:
            # 使用 stock_zh_a_hist_orm 获取完整ORM格式数据并保存到数据库
            logger.info(f"开始获取ORM格式数据并保存到数据库: {symbol} ({adjust})")
            orm_df = ak.stock_zh_a_hist_orm(
                symbol=symbol, adjust=adjust,
                start_date="20200101", end_date=datetime.now().strftime("%Y%m%d")
            )
            
            if orm_df is not None and not orm_df.empty:
                db_orm.save_to_mysql_orm_incremental(
                    df=orm_df,
                    orm_class=StockHistoryDailyInfoEntity,
                    symbol=symbol,
                    isDel=True,
                    adjust=adjust
                )
                logger.info(f"数据成功保存到数据库: {symbol} ({adjust})")
            else:
                logger.warning(f"获取ORM格式数据为空，跳过数据库保存: {symbol}")
        except Exception as e:
            logger.warning(f"保存数据到数据库失败 {symbol}: {e}")
    
    # ==================== 在线数据源（多源降级） ====================
    
    def _fetch_from_eastmoney(self, symbol: str, adjust: str = "qfq") -> pd.DataFrame:
        """从东方财富获取数据（AKShare主要数据源）"""
        try:
            logger.info(f"从东方财富获取数据: {symbol} ({adjust})")
            df = ak.stock_zh_a_hist(symbol=symbol, period="daily", adjust=adjust,
                                   start_date="20200101", end_date=datetime.now().strftime("%Y%m%d"))
            
            if df is None or df.empty:
                logger.warning(f"东方财富返回空数据: {symbol}")
                return pd.DataFrame()
            
            return self._normalize_akshare_columns(df, symbol, adjust)
        except Exception as e:
            logger.warning(f"东方财富获取失败 {symbol}: {e}")
            return pd.DataFrame()
    
    def _fetch_from_sina(self, symbol: str, adjust: str = "qfq") -> pd.DataFrame:
        """从腾讯证券获取数据（备用数据源1）
        
        注意: akshare 已移除 stock_zh_a_hist_sina 和 stock_zh_a_hist_163，
        当前仅东方财富和腾讯证券两个历史行情接口可用
        使用 stock_zh_a_hist_tx 作为备用数据源
        """
        try:
            # 转换股票代码格式：添加市场前缀
            tx_symbol = symbol
            if not symbol.startswith(('sz', 'sh', 'bj')):
                if symbol.startswith('6'):
                    tx_symbol = f'sh{symbol}'
                elif symbol.startswith(('0', '3')):
                    tx_symbol = f'sz{symbol}'
                elif symbol.startswith('8') or symbol.startswith('4'):
                    tx_symbol = f'bj{symbol}'
                else:
                    tx_symbol = f'sz{symbol}'  # 默认深市
            
            logger.info(f"从腾讯证券获取数据(备用源1): {symbol} ({adjust}), tx_symbol={tx_symbol}")
            df = ak.stock_zh_a_hist_tx(symbol=tx_symbol, adjust=adjust)
            
            if df is None or df.empty:
                logger.warning(f"腾讯证券返回空数据: {symbol}")
                return pd.DataFrame()
            
            return self._normalize_akshare_columns(df, symbol, adjust)
        except Exception as e:
            logger.warning(f"腾讯证券获取失败 {symbol}: {e}")
            return pd.DataFrame()
    
    def _fetch_from_tencent(self, symbol: str, adjust: str = "qfq") -> pd.DataFrame:
        """从腾讯证券获取数据（备用数据源2）
        
        使用 akshare.stock_zh_a_hist_tx 接口
        注意: symbol 需要带市场前缀，如 sz000001, sh600000
        """
        try:
            # 转换股票代码格式：添加市场前缀
            tx_symbol = symbol
            if not symbol.startswith(('sz', 'sh', 'bj')):
                if symbol.startswith('6'):
                    tx_symbol = f'sh{symbol}'
                elif symbol.startswith(('0', '3')):
                    tx_symbol = f'sz{symbol}'
                elif symbol.startswith('8') or symbol.startswith('4'):
                    tx_symbol = f'bj{symbol}'
                else:
                    tx_symbol = f'sz{symbol}'  # 默认深市
            
            logger.info(f"从腾讯证券获取数据: {symbol} ({adjust}), tx_symbol={tx_symbol}")
            df = ak.stock_zh_a_hist_tx(symbol=tx_symbol, adjust=adjust)
            
            if df is None or df.empty:
                logger.warning(f"腾讯证券返回空数据: {symbol}")
                return pd.DataFrame()
            
            return self._normalize_akshare_columns(df, symbol, adjust)
        except Exception as e:
            logger.warning(f"腾讯证券获取失败 {symbol}: {e}")
            return pd.DataFrame()
    
    def _fetch_from_akshare(self, symbol: str, adjust: str = "qfq") -> pd.DataFrame:
        """从AKShare获取数据 - 使用多数据源自动降级策略
        
        数据源优先级：东方财富 → 新浪财经 → 腾讯财经
        参考 quant/entity/script/stock_data_save_script.get_stock_data_with_fallback
        """
        max_retries = 3
        retry_delay = 2.0
        
        for source_name, fetch_func in self.online_fallback_sources:
            logger.info(f"尝试使用数据源: {source_name}")
            
            for attempt in range(1, max_retries + 1):
                try:
                    df = fetch_func(symbol, adjust)
                    
                    if df is not None and not df.empty:
                        logger.info(f"成功从 {source_name} 获取 {symbol} 数据 ({len(df)} 条记录)")
                        return df
                    else:
                        logger.warning(f"{source_name} 返回空数据")
                except Exception as e:
                    if attempt < max_retries:
                        logger.warning(f"第{attempt}次尝试失败: {str(e)[:100]}，{retry_delay}秒后重试...")
                        time.sleep(retry_delay)
                    else:
                        logger.error(f"{source_name} 已重试{max_retries}次，全部失败")
            
            logger.warning(f"数据源 [{source_name}] 不可用，切换到下一个...")
        
        logger.error(f"所有在线数据源都已失败，无法获取股票 {symbol} 的数据")
        return pd.DataFrame()
    
    def _normalize_akshare_columns(self, df: pd.DataFrame, symbol: str, adjust: str) -> pd.DataFrame:
        """统一AKShare不同接口返回的列名格式"""
        # 重命名列以符合标准格式
        column_mapping = {
            '日期': 'date', '开盘': 'open', '收盘': 'close',
            '最高': 'high', '最低': 'low', '成交量': 'volume'
        }
        
        mapped_columns = {}
        for ak_col, std_col in column_mapping.items():
            if ak_col in df.columns:
                mapped_columns[ak_col] = std_col
        
        df = df.rename(columns=mapped_columns)
        
        # 确保必要列存在
        required_columns = ['date', 'open', 'close', 'high', 'low', 'volume']
        for col in required_columns:
            if col not in df.columns:
                logger.error(f"缺少必要列: {col}")
                return pd.DataFrame()
        
        # 确保日期格式正确
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        
        logger.info(f"成功获取 {symbol} 数据，共 {len(df)} 条记录")
        return df
    
    # ==================== 预留数据源 ====================
    
    def _fetch_from_tushare(self, symbol: str, adjust: str = "qfq") -> pd.DataFrame:
        """从Tushare获取数据（预留接口）"""
        logger.warning("Tushare数据源暂未实现")
        return pd.DataFrame()
    
    def _fetch_from_local(self, symbol: str, adjust: str = "qfq") -> pd.DataFrame:
        """从本地文件获取数据（预留接口）"""
        logger.warning("本地数据源暂未实现")
        return pd.DataFrame()
    
    # ==================== 统一数据获取接口 ====================
    
    def fetch_data(self, symbol: str, adjust: str = "qfq", source: str = "auto") -> pd.DataFrame:
        """
        统一数据获取接口 - 支持智能数据源选择
        
        数据获取优先级（source='auto'时）：
        1. MySQL数据库 - 优先从数据库获取，避免网络请求
        2. 本地缓存 - pickle文件缓存
        3. AKShare API - 多数据源自动降级
        4. 自动保存到数据库和缓存
        
        Args:
            symbol: 股票代码
            adjust: 复权方式 ('qfq', 'hfq', None)
            source: 数据源 ('auto', 'mysql', 'akshare', 'tushare', 'local')
                'auto' = 智能选择（默认），优先数据库
                'mysql' = 仅从数据库
                'akshare' = 仅从API（跳过数据库）
                'tushare' = 仅从Tushare
                'local' = 仅从本地文件
        
        Returns:
            pd.DataFrame: 股票数据
        """
        if source == 'auto':
            # 智能模式：优先从数据库获取
            # 1. 尝试从数据库获取
            if self.db_enabled:
                db_data = self._fetch_from_mysql(symbol, adjust)
                if not db_data.empty:
                    logger.info(f"使用数据库数据: {symbol} ({adjust})")
                    return db_data
                logger.info(f"数据库无数据，将从API获取: {symbol} ({adjust})")
            
            # 2. 尝试从缓存获取
            if self.cache_enabled:
                cache_key = self._get_cache_key(symbol, adjust, 'akshare')
                if self._check_cache(cache_key):
                    cached_data = self._load_from_cache(cache_key)
                    if not cached_data.empty:
                        logger.info(f"使用缓存数据: {symbol} ({adjust})")
                        return cached_data
            
            # 3. 从API获取（多数据源降级）
            api_data = self._fetch_from_akshare(symbol, adjust)
            
            if not api_data.empty:
                # 保存到缓存
                if self.cache_enabled:
                    cache_key = self._get_cache_key(symbol, adjust, 'akshare')
                    self._save_to_cache(cache_key, api_data)
                
                # 保存到数据库（异步，不影响返回）
                self._save_to_database(api_data, symbol, adjust)
                
                return api_data
            
            logger.error(f"所有数据源获取失败: {symbol} ({adjust})")
            return pd.DataFrame()
        
        elif source not in self.data_sources:
            logger.error(f"不支持的数据源: {source}")
            return pd.DataFrame()
        
        else:
            # 指定数据源模式
            if source == 'mysql' and not self.db_enabled:
                logger.warning("数据库功能未启用")
                return pd.DataFrame()
            
            fetch_func = self.data_sources[source]
            data = fetch_func(symbol, adjust)
            
            # 保存缓存
            if not data.empty and source != 'mysql':
                cache_key = self._get_cache_key(symbol, adjust, source)
                self._save_to_cache(cache_key, data)
                # 非数据库数据也保存到数据库
                self._save_to_database(data, symbol, adjust)
            
            return data
    
    def fetch_batch_data(self, symbol_list: List[str], adjust: str = "qfq", 
                        source: str = "auto", max_workers: int = 4) -> Dict[str, pd.DataFrame]:
        """
        批量数据获取 - 并行化
        
        Args:
            symbol_list: 股票代码列表
            adjust: 复权方式
            source: 数据源（默认auto，智能选择）
            max_workers: 最大并发数
        
        Returns:
            Dict[str, pd.DataFrame]: {symbol: data}
        """
        logger.info(f"开始批量获取数据，股票数量: {len(symbol_list)}, 并发数: {max_workers}")
        
        results = {}
        failed_symbols = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交任务
            future_to_symbol = {
                executor.submit(self.fetch_data, symbol, adjust, source): symbol 
                for symbol in symbol_list
            }
            
            # 收集结果
            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    data = future.result()
                    if not data.empty:
                        results[symbol] = data
                        logger.debug(f"获取成功: {symbol}")
                    else:
                        failed_symbols.append(symbol)
                        logger.warning(f"获取数据为空: {symbol}")
                except Exception as e:
                    failed_symbols.append(symbol)
                    logger.error(f"获取数据失败 {symbol}: {e}")
        
        logger.info(f"批量数据获取完成 - 成功: {len(results)}, 失败: {len(failed_symbols)}")
        
        if failed_symbols:
            logger.warning(f"失败的股票: {failed_symbols}")
        
        return results
    
    def clear_cache(self, symbol: str = None, adjust: str = None, source: str = None):
        """清理缓存"""
        if symbol is None and adjust is None and source is None:
            # 清理所有缓存
            for file in os.listdir(self.cache_dir):
                if file.endswith('.pkl'):
                    os.remove(os.path.join(self.cache_dir, file))
            logger.info("已清理所有缓存")
        else:
            # 清理特定缓存
            cache_key = self._get_cache_key(symbol or "", adjust or "", source or "")
            cache_file = os.path.join(self.cache_dir, f"{cache_key}.pkl")
            if os.path.exists(cache_file):
                os.remove(cache_file)
                logger.info(f"已清理缓存: {cache_file}")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """获取缓存和数据库信息"""
        cache_files = [f for f in os.listdir(self.cache_dir) if f.endswith('.pkl')]
        total_size = sum(os.path.getsize(os.path.join(self.cache_dir, f)) for f in cache_files)
        
        info = {
            'cache_enabled': self.cache_enabled,
            'cache_dir': self.cache_dir,
            'cache_files_count': len(cache_files),
            'total_size_mb': total_size / 1024 / 1024,
            'cache_expiry_days': self.cache_expiry_days,
            'db_enabled': self.db_enabled,
            'db_save_enabled': self.db_save_enabled,
            'online_fallback_sources': [name for name, _ in self.online_fallback_sources]
        }
        
        # 如果数据库可用，检查数据库连接状态
        if self.db_enabled:
            try:
                engine = db_orm.get_engine()
                info['db_status'] = 'connected'
                info['db_pool_size'] = engine.pool.size()
            except Exception as e:
                info['db_status'] = f'error: {e}'
        else:
            info['db_status'] = 'disabled'
        
        return info


# 测试函数
def test_data_fetcher():
    """测试数据获取器"""
    fetcher = DataFetcher(cache_enabled=True, db_enabled=DB_AVAILABLE, db_save_enabled=DB_AVAILABLE)
    
    # 显示系统信息
    print("数据获取器系统信息:")
    info = fetcher.get_cache_info()
    for k, v in info.items():
        print(f"  {k}: {v}")
    
    # 测试单只股票（auto模式 - 优先数据库）
    print("\n测试单只股票数据获取（auto模式）...")
    data = fetcher.fetch_data("000001", "qfq")
    if not data.empty:
        print(f"000001 数据形状: {data.shape}")
        print(f"列名: {list(data.columns)}")
        print(f"日期范围: {data['date'].min()} ~ {data['date'].max()}")
    else:
        print("获取数据失败")
    
    # 测试指定数据源
    if DB_AVAILABLE:
        print("\n测试从数据库直接获取...")
        db_data = fetcher.fetch_data("000001", "qfq", source="mysql")
        if not db_data.empty:
            print(f"数据库数据形状: {db_data.shape}")
        else:
            print("数据库中无数据")
    
    # 测试批量获取
    print("\n测试批量数据获取...")
    symbols = ["000001", "000002"]
    batch_data = fetcher.fetch_batch_data(symbols)
    print(f"批量获取结果: {len(batch_data)} 只股票")
    for symbol, data in batch_data.items():
        print(f"  {symbol}: {len(data)} 条记录")


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    test_data_fetcher()