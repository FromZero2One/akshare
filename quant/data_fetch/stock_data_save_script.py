import sys
import os

# 将项目根目录添加到Python路径中
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import akshare as ak
import pandas as pd
import numpy as np
from quant.utils.logger_config import get_quant_logger
# 导入模块
import quant.utils.db_orm as db_orm
from quant.entity.StockCommentEntity import StockCommentEntity
# 导入模块中所有类 一般不推荐
# from quant.entity import *
# 导入指定类，从具体文件中导入避免模块冲突
from quant.entity.StockNameEntity import StockNameEntity
from quant.entity.StockHistoryDailyInfoEntity import StockHistoryDailyInfoEntity
from quant.entity.StockValueEntity import StockValueEntity

# 配置日志
logger = get_quant_logger()


def stock_name_and_save(reBuild: bool = False):
    """
    获取所有股票名称并保存到数据库
    
    Args:
        reBuild: 是否重建表（True=删除旧表重建，False=追加数据）
    """
    df = ak.stock_a_indicator_lg(symbol="all")
    db_orm.save_to_mysql_orm(df, StockNameEntity, reBuild=reBuild)


def stock_value_em_orm(symbol: str = '000001', TRADE_DATE: str = "2025-09-25", reBuild: bool = False):
    """
    获取个股估值数据并保存到数据库
    
    Args:
        symbol: 股票代码（默认'000001'）
        TRADE_DATE: 交易日期（默认"2025-09-25"）
        reBuild: 是否重建表
    """
    stock_value_em_df = ak.stock_value_em_orm(symbol=symbol, TRADE_DATE=TRADE_DATE)
    db_orm.save_to_mysql_orm(stock_value_em_df, StockValueEntity, reBuild=reBuild)


def stock_comment_em_orm(reBuild: bool = False):
    """
    获取千股千评数据并保存到数据库
    
    Args:
        reBuild: 是否重建表
    """
    df = ak.stock_comment_em_orm()
    db_orm.save_to_mysql_orm(df, StockCommentEntity, reBuild)


def stock_zh_a_hist_orm(reBuild: bool = False, symbol: str = "601398", start_date: str = "19700101",
                        end_date: str = "20500101"):
    """
    获取指定股票历史行情数据并保存到数据库（全量）
    
    Args:
        reBuild: 是否重建表
        symbol: 股票代码（默认"601398"）
        start_date: 开始日期（默认"19700101"）
        end_date: 结束日期（默认"20500101"）
    """
    stock_hfq_df = ak.stock_zh_a_hist_orm(symbol=symbol, adjust="qfq", start_date=start_date, end_date=end_date)
    db_orm.save_to_mysql_orm(stock_hfq_df, StockHistoryDailyInfoEntity, reBuild=reBuild)


def _normalize_stock_data(df: pd.DataFrame, source: str = 'sina', 
                          symbol: str = None, adjust: str = None) -> pd.DataFrame:
    """
    标准化股票数据格式，确保所有数据源返回统一的列和顺序
    
    标准列顺序（与StockHistoryDailyInfoEntity一致）：
    ['symbol', 'date', 'open', 'close', 'high', 'low', 'volume', 'trading_value',
     'average_true_range', 'price_limit_change', 'price_change_amount', 
     'turnover_rate', 'create_date', 'adjust']
    
    Args:
        df: 原始数据DataFrame
        source: 数据源标识 ('sina' 或 'tencent')
        symbol: 股票代码
        adjust: 复权类型
        
    Returns:
        pd.DataFrame: 标准化后的数据
    """
    if df is None or df.empty:
        return df
    
    # 定义标准列和顺序（与StockHistoryDailyInfoEntity完全一致）
    standard_columns = [
        'symbol', 'date', 'open', 'close', 'high', 'low', 'volume', 
        'trading_value', 'average_true_range', 'price_limit_change', 
        'price_change_amount', 'turnover_rate', 'create_date', 'adjust'
    ]
    
    # 创建新的DataFrame，确保列的顺序一致
    normalized_df = pd.DataFrame()
    
    for col in standard_columns:
        if col in df.columns:
            # 如果列存在，直接使用
            normalized_df[col] = df[col].values
        else:
            # 如果列不存在，用NaN填充
            normalized_df[col] = np.nan
    
    # 补充特殊字段
    if 'symbol' not in df.columns and symbol:
        normalized_df['symbol'] = symbol
    
    if 'adjust' not in df.columns and adjust:
        normalized_df['adjust'] = adjust
    
    if 'create_date' not in df.columns:
        from datetime import datetime
        normalized_df['create_date'] = datetime.now().date()
    
    # 映射列名（处理不同数据源的列名差异）
    column_mapping = {
        'amount': 'trading_value',           # 成交额
        'outstanding_share': None,           # 流通股数（数据库不需要）
        'turnover': None,                    # 换手率（可能是百分比形式）
        '振幅': 'average_true_range',
        '涨跌幅': 'price_limit_change',
        '涨跌额': 'price_change_amount',
        '换手率': 'turnover_rate',
        '成交额': 'trading_value',
    }
    
    for old_col, new_col in column_mapping.items():
        if old_col in df.columns and new_col and new_col not in normalized_df.columns:
            normalized_df[new_col] = df[old_col].values
    
    # 确保数据类型正确
    numeric_cols = ['open', 'close', 'high', 'low', 'volume', 'trading_value',
                    'average_true_range', 'price_limit_change', 'price_change_amount',
                    'turnover_rate']
    for col in numeric_cols:
        if col in normalized_df.columns:
            normalized_df[col] = pd.to_numeric(normalized_df[col], errors='coerce')
    
    # 日期字段处理
    if 'date' in normalized_df.columns:
        normalized_df['date'] = pd.to_datetime(normalized_df['date'], errors='coerce').dt.date
    
    logger.debug(f"数据标准化完成 ({source}): {len(normalized_df)} 条记录, {len(normalized_df.columns)} 列")
    
    return normalized_df

def get_stock_data_from_sina(symbol: str, adjust: str = "qfq", 
                             start_date: str = "19700101", end_date: str = "20500101"):
    """
    从新浪财经获取股票历史数据（备用数据源1）
    
    Args:
        symbol: 股票代码（会自动添加市场标识）
        adjust: 复权类型
        start_date: 开始日期 (格式: YYYYMMDD)
        end_date: 结束日期 (格式: YYYYMMDD)
        
    Returns:
        pd.DataFrame: 股票历史数据（统一格式）
    """
    try:
        # 添加市场标识
        if symbol.startswith('6'):
            sina_symbol = f"sh{symbol}"
        else:
            sina_symbol = f"sz{symbol}"
        
        logger.info(f"尝试从新浪财经获取股票 {sina_symbol} 数据...")
        df = ak.stock_zh_a_daily(
            symbol=sina_symbol, 
            start_date=start_date,
            end_date=end_date,
            adjust=adjust
        )
        
        # 标准化数据格式
        df = _normalize_stock_data(df, source='sina', symbol=symbol, adjust=adjust)
        
        logger.info(f"✅ 从新浪财经成功获取 {len(df)} 条数据")
        return df
    except Exception as e:
        logger.warning(f"⚠️  新浪财经获取失败: {e}")
        raise


def get_stock_data_from_tencent(symbol: str, 
                                start_date: str = "19700101", end_date: str = "20500101",
                                adjust: str = ""):
    """
    从腾讯财经获取股票历史数据（备用数据源2）
    
    Args:
        symbol: 股票代码（会自动添加市场标识）
        start_date: 开始日期 (格式: YYYYMMDD)
        end_date: 结束日期 (格式: YYYYMMDD)
        adjust: 复权类型
        
    Returns:
        pd.DataFrame: 股票历史数据（统一格式）
    """
    try:
        # 添加市场标识
        if symbol.startswith('6'):
            tx_symbol = f"sh{symbol}"
        else:
            tx_symbol = f"sz{symbol}"
        
        logger.info(f"尝试从腾讯财经获取股票 {tx_symbol} 数据...")
        # 腾讯接口需要通过akshare调用
        df = ak.stock_zh_a_hist_tx(
            symbol=tx_symbol,
            start_date=start_date,
            end_date=end_date,
            adjust=adjust
        )
        
        # 标准化数据格式
        df = _normalize_stock_data(df, source='tencent', symbol=symbol, adjust=adjust)
        
        logger.info(f"✅ 从腾讯财经成功获取 {len(df)} 条数据")
        return df
    except Exception as e:
        logger.warning(f"⚠️  腾讯财经获取失败: {e}")
        raise


def get_stock_data_with_fallback(symbol: str, adjust: str = "qfq", max_retries: int = 3, retry_delay: float = 2.0):
    """
    获取股票数据，支持多数据源自动降级(兼容旧接口,默认全量拉取)
    
    数据源优先级：
    1. 东方财富（主要）
    2. 新浪财经（备用1）
    3. 腾讯财经（备用2）
    
    Args:
        symbol: 股票代码
        adjust: 复权类型
        max_retries: 每个数据源的最大重试次数
        retry_delay: 重试间隔时间
        
    Returns:
        pd.DataFrame: 股票历史数据
        
    Raises:
        Exception: 所有数据源都失败时抛出异常
    """
    return get_stock_data_with_fallback_and_date(
        symbol=symbol,
        adjust=adjust,
        start_date="19700101",
        end_date="20500101",
        max_retries=max_retries,
        retry_delay=retry_delay
    )


def get_stock_data_with_fallback_and_date(symbol: str, adjust: str = "qfq", 
                                          start_date: str = "19700101", 
                                          end_date: str = "20500101",
                                          max_retries: int = 3, 
                                          retry_delay: float = 2.0):
    """
    获取股票数据，支持多数据源自动降级和自定义日期范围
    
    数据源优先级：
    1. 东方财富（主要）
    2. 新浪财经（备用1）
    3. 腾讯财经（备用2）
    
    Args:
        symbol: 股票代码
        adjust: 复权类型
        start_date: 开始日期 (格式: YYYYMMDD)
        end_date: 结束日期 (格式: YYYYMMDD)
        max_retries: 每个数据源的最大重试次数
        retry_delay: 重试间隔时间
        
    Returns:
        pd.DataFrame: 股票历史数据（可能为空DataFrame表示无新数据）
        
    Raises:
        Exception: 所有数据源都因错误而失败时抛出异常（不包括返回空数据的情况）
    """
    import time
    
    # 数据源列表：(名称, 获取函数)
    data_sources = [
        # ("东方财富", lambda: ak.stock_zh_a_hist_orm(symbol, adjust, start_date, end_date)),
        ("新浪财经", lambda: get_stock_data_from_sina(symbol, adjust, start_date, end_date)),
        ("腾讯财经", lambda: get_stock_data_from_tencent(symbol, start_date, end_date, adjust)),
    ]
    
    all_sources_empty = True  # 标记是否所有数据源都返回空
    
    for source_name, fetch_func in data_sources:
        logger.info(f"📊 尝试使用数据源: {source_name}")
        
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"  尝试 {attempt}/{max_retries}...")
                df = fetch_func()
                
                # 验证数据有效性
                if df is not None and not df.empty:
                    logger.info(f"✅ 成功从 {source_name} 获取数据 ({len(df)} 条记录)")
                    return df
                else:
                    logger.warning(f"⚠️  {source_name} 返回空数据")
                    all_sources_empty = True  # 至少有一个数据源返回空
                    
            except Exception as e:
                all_sources_empty = False  # 发生了真正的错误
                if attempt < max_retries:
                    logger.warning(f"  ⚠️  第{attempt}次尝试失败: {str(e)[:100]}")
                    logger.info(f"  ⏳ {retry_delay}秒后重试...")
                    time.sleep(retry_delay)
                else:
                    logger.error(f"  ❌ {source_name} 已重试{max_retries}次，全部失败")
        
        logger.warning(f"⚠️  数据源 [{source_name}] 不可用，切换到下一个...")
    
    # 所有数据源都处理完毕
    if all_sources_empty:
        # 所有数据源都返回空数据，这不是错误，而是确实没有新数据
        logger.info(f"ℹ️  所有数据源都未返回新数据（可能数据已是最新）")
        import pandas as pd
        return pd.DataFrame()  # 返回空DataFrame，而不是抛出异常
    else:
        # 有数据源发生了真正的错误
        error_msg = f"所有数据源都已失败，无法获取股票 {symbol} 的数据"
        logger.error(f"❌ {error_msg}")
        raise Exception(error_msg)


def stock_zh_a_hist_orm_incremental(symbol: str = "601398", adjust: str = "qfq", isDel=False, max_retries: int = 3, retry_delay: float = 2.0):
    """
    获取指定股票历史行情数据 智能增量更新（支持多数据源自动降级）
    
    工作流程:
    1. 查询数据库中最新日期
    2. 如果有数据，从下一天开始拉取；否则从1970年开始
    3. 只拉取缺失的部分，直接追加到数据库
    
    Args:
        symbol: 股票代码
        adjust: 复权类型 (qfq=前复权, hfq=后复权)
        isDel: 是否删除旧数据(默认False,推荐保持False以使用增量模式)
        max_retries: 每个数据源的最大重试次数（默认3次）
        retry_delay: 重试间隔时间（秒，默认2秒）
        
    Returns:
        bool: True=成功, False=失败
    """
    from datetime import datetime, timedelta
    
    try:
        # 步骤1: 查询数据库中最新日期(仅在isDel=False时启用智能增量)
        start_date = "19700101"  # 默认从最早开始
        end_date = "20500101"    # 默认到最晚
        
        if not isDel:
            latest_date = db_orm.get_latest_date_from_db(symbol=symbol, adjust=adjust)
            
            if latest_date:
                # 有历史数据，计算下一天作为起始日期
                latest_dt = datetime.strptime(latest_date, '%Y-%m-%d')
                next_day = latest_dt + timedelta(days=1)
                start_date = next_day.strftime('%Y%m%d')
                logger.info(f"→ 股票 {symbol}({adjust}) 已有数据至 {latest_date}，将拉取 {start_date} 之后的数据")
            else:
                logger.info(f"→ 股票 {symbol}({adjust}) 无历史数据，将从头开始拉取")
        else:
            logger.info(f"→ 股票 {symbol}({adjust}) 使用全量刷新模式(删除旧数据)")
        
        # 步骤2: 使用多数据源降级策略获取数据(带日期范围)
        logger.info(f"开始获取股票 {symbol} 的数据 ({start_date} ~ {end_date})...")
        
        stock_hfq_df = get_stock_data_with_fallback_and_date(
            symbol=symbol,
            adjust=adjust,
            start_date=start_date,
            end_date=end_date,
            max_retries=max_retries,
            retry_delay=retry_delay
        )
        
        # 验证是否有新数据
        if stock_hfq_df.empty:
            logger.info(f"✓ 股票 {symbol} 无新数据需要更新")
            return True
        
        logger.info(f"→ 获取到 {len(stock_hfq_df)} 条新数据，准备保存...")
        
        # 转换列名为小写蛇形命名(兼容ORM定义)
        column_mapping = {
            'Trading_Value': 'trading_value',
            'Average_True_Range': 'average_true_range',
            'Price_Limit_Change': 'price_limit_change',
            'Price_Change_Amount': 'price_change_amount',
            'Turnover_Rate': 'turnover_rate'
        }
        stock_hfq_df.rename(columns=column_mapping, inplace=True)
        logger.debug(f"已转换列名: {list(column_mapping.keys())} → {list(column_mapping.values())}")
        
        # 步骤3: 保存到数据库(isDel=False时为纯追加模式)
        db_orm.save_to_mysql_orm_incremental(
            df=stock_hfq_df, 
            orm_class=StockHistoryDailyInfoEntity, 
            symbol=symbol,
            isDel=isDel
        )
        
        logger.info(f"✅ 股票 {symbol} 增量数据保存成功")
        return True  # 成功则返回
        
    except Exception as e:
        logger.error(f"❌ 获取股票 {symbol} 数据失败（所有数据源均已尝试）: {e}", exc_info=True)
        logger.warning("跳过该股票，继续处理下一个...")
        return False  # 所有重试都失败


def stock_comment_detail_scrd_focus_em(symbol="600000", reBuild=False):
    """
    个股关注度 [千股千评包含该指标]
    
    Args:
        symbol: 股票代码
        reBuild: 是否重建表
    """
    df = ak.stock_comment_detail_scrd_focus_em_orm(symbol=symbol)
    logger.info(f"个股关注度数据预览:\n{df.head()}")
    db_orm.save_with_auto_entity(df=df, table_name="stock_comment_detail_scrd_focus_em_orm",
                                 table_comment="个股关注度表",
                                 reBuild=reBuild)


def stock_comment_detail_zlkp_jgcyd_em(symbol="600000", reBuild=False):
    """
    个股机构参与度 [千股千评包含该指标]
    
    Args:
        symbol: 股票代码
        reBuild: 是否重建表
    """
    df = ak.stock_comment_detail_zlkp_jgcyd_em_orm(symbol=symbol)
    logger.info(f"个股机构参与度数据预览:\n{df.head()}")
    db_orm.save_with_auto_entity(df=df, table_name="stock_comment_detail_zlkp_jgcyd_em_orm",
                                 table_comment="个股机构参与度",
                                 reBuild=reBuild)


def stock_comment_detail_zhpj_lspf_em(symbol="600000", reBuild=False):
    """
    个股历史评价[千股千评包含该指标]
    
    Args:
        symbol: 股票代码
        reBuild: 是否重建表
    """
    df = ak.stock_comment_detail_zhpj_lspf_em_orm(symbol=symbol)
    logger.info(f"个股历史评价数据预览:\n{df.head()}")
    db_orm.save_with_auto_entity(df=df, table_name="stock_comment_detail_zhpj_lspf_em_orm",
                                 table_comment="个股历史评价表",
                                 reBuild=reBuild)


if __name__ == '__main__':
    symbol = '000001'
    reBuild = True
    
    logger.info("="*60)
    logger.info("开始执行股票数据保存脚本")
    logger.info("="*60)
    
    # stock_name_and_save(reBuild=reBuild)
    # stock_comment_em_orm(reBuild=reBuild)
    # 估值
    # logger.info("get_value_and_save")
    # stock_value_em_orm(symbol=symbol, reBuild=reBuild)
    # logger.info("get_and_save_stock_hist")
    # stock_zh_a_hist_orm(symbol=symbol, reBuild=reBuild, start_date="19700101", end_date="20500101")
    # stock_zh_a_hist_orm_incremental(symbol=symbol, adjust="qfq", isDel=True)
    # logger.info("stock_comment_detail_scrd_focus_em")
    # stock_comment_detail_scrd_focus_em(symbol=symbol, reBuild=reBuild)
    # logger.info("stock_comment_detail_zlkp_jgcyd_em")
    # stock_comment_detail_zlkp_jgcyd_em(symbol=symbol, reBuild=reBuild)
    # logger.info("stock_comment_detail_zhpj_lspf_em")
    # stock_comment_detail_zhpj_lspf_em(symbol=symbol, reBuild=reBuild)

    adjust="qfq"
    start_date = "20260101"
    end_date = "20260605"
    # get_stock_data_from_sina(symbol, adjust, start_date, end_date)
    get_stock_data_from_tencent(symbol, start_date, end_date, adjust)
    
    logger.info("="*60)
    logger.info("✅ 数据保存脚本执行完成")
    logger.info("="*60)