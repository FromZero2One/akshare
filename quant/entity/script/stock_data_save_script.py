import sys
import os

# 将项目根目录添加到Python路径中
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import akshare as ak
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

def get_stock_data_from_sina(symbol: str, adjust: str = "qfq"):
    """
    从新浪财经获取股票历史数据（备用数据源1）
    
    Args:
        symbol: 股票代码
        adjust: 复权类型
        
    Returns:
        pd.DataFrame: 股票历史数据
    """
    try:
        logger.info(f"尝试从新浪财经获取股票 {symbol} 数据...")
        df = ak.stock_zh_a_hist_sina(symbol=symbol, adjust=adjust)
        logger.info(f"✅ 从新浪财经成功获取 {len(df)} 条数据")
        return df
    except Exception as e:
        logger.warning(f"⚠️  新浪财经获取失败: {e}")
        raise


def get_stock_data_from_tencent(symbol: str):
    """
    从腾讯财经获取股票历史数据（备用数据源2）
    
    Args:
        symbol: 股票代码
        
    Returns:
        pd.DataFrame: 股票历史数据
    """
    try:
        logger.info(f"尝试从腾讯财经获取股票 {symbol} 数据...")
        # 腾讯接口需要通过akshare调用
        df = ak.stock_zh_a_daily(symbol=symbol)
        logger.info(f"✅ 从腾讯财经成功获取 {len(df)} 条数据")
        return df
    except Exception as e:
        logger.warning(f"⚠️  腾讯财经获取失败: {e}")
        raise


def get_stock_data_with_fallback(symbol: str, adjust: str = "qfq", max_retries: int = 3, retry_delay: float = 2.0):
    """
    获取股票数据，支持多数据源自动降级
    
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
    import time
    
    # 数据源列表：(名称, 获取函数)
    data_sources = [
        ("东方财富", lambda: ak.stock_zh_a_hist_orm(symbol=symbol, adjust=adjust)),
        ("新浪财经", lambda: get_stock_data_from_sina(symbol, adjust)),
        ("腾讯财经", lambda: get_stock_data_from_tencent(symbol)),
    ]
    
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
                    
            except Exception as e:
                if attempt < max_retries:
                    logger.warning(f"  ⚠️  第{attempt}次尝试失败: {str(e)[:100]}")
                    logger.info(f"  ⏳ {retry_delay}秒后重试...")
                    time.sleep(retry_delay)
                else:
                    logger.error(f"  ❌ {source_name} 已重试{max_retries}次，全部失败")
        
        logger.warning(f"⚠️  数据源 [{source_name}] 不可用，切换到下一个...")
    
    # 所有数据源都失败
    error_msg = f"所有数据源都已失败，无法获取股票 {symbol} 的数据"
    logger.error(f"❌ {error_msg}")
    raise Exception(error_msg)


def stock_zh_a_hist_orm_incremental(symbol: str = "601398", adjust: str = "qfq", isDel=False, max_retries: int = 3, retry_delay: float = 2.0):
    """
    获取指定股票历史行情数据 增量更新（支持多数据源自动降级）
    
    Args:
        symbol: 股票代码
        adjust: 复权类型 (qfq=前复权, hfq=后复权)
        isDel: 是否删除旧数据
        max_retries: 每个数据源的最大重试次数（默认3次）
        retry_delay: 重试间隔时间（秒，默认2秒）
    """
    import time
    
    try:
        logger.info(f"开始获取股票 {symbol} 的增量数据...")
        
        # 使用多数据源降级策略获取数据
        stock_hfq_df = get_stock_data_with_fallback(
            symbol=symbol,
            adjust=adjust,
            max_retries=max_retries,
            retry_delay=retry_delay
        )
        
        # 保存到数据库
        db_orm.save_to_mysql_orm_incremental(df=stock_hfq_df, orm_class=StockHistoryDailyInfoEntity, symbol=symbol,
                                             isDel=isDel)
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
    stock_zh_a_hist_orm_incremental(symbol=symbol, adjust="qfq", isDel=True)
    # logger.info("stock_comment_detail_scrd_focus_em")
    # stock_comment_detail_scrd_focus_em(symbol=symbol, reBuild=reBuild)
    # logger.info("stock_comment_detail_zlkp_jgcyd_em")
    # stock_comment_detail_zlkp_jgcyd_em(symbol=symbol, reBuild=reBuild)
    # logger.info("stock_comment_detail_zhpj_lspf_em")
    # stock_comment_detail_zhpj_lspf_em(symbol=symbol, reBuild=reBuild)
    
    logger.info("="*60)
    logger.info("✅ 数据保存脚本执行完成")
    logger.info("="*60)