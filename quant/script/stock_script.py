from sqlalchemy.orm import declarative_base

import akshare as ak
# 导入模块
import quant.utils.db_orm as db_orm
from quant.entity.StockCommentEntity import StockCommentEntity
# 导入模块中所有类 一般不推荐
# from quant.entity import *
# 导入指定类，从具体文件中导入避免模块冲突
from quant.entity.StockNameEntity import StockNameEntity
from quant.entity.StockDailyInfoEntity import StockDailyInfoEntity
from quant.entity.StockDailyEntity import StockDailyEntity


def get_all_stock_name_and_save(rebuild: bool = False):
    """
    获取所有股票名称
    """
    df = ak.stock_a_indicator_lg(symbol="all")
    db_orm.save_to_mysql_orm(df, StockNameEntity, rebuild=rebuild)


def get_value_and_save(stock_code: str, rebuild: bool = False):
    """
    估值分析
    """
    stock_value_em_df = ak.stock_value_em_orm(symbol=stock_code)
    db_orm.save_to_mysql_orm(stock_value_em_df, StockDailyEntity, rebuild=rebuild)


def get_stock_comment_and_save(rebuild: bool = False):
    """
    千股千评
    """
    df = ak.stock_comment_em_orm()
    db_orm.save_to_mysql_orm(df, StockCommentEntity, rebuild)


def get_and_save_stock_hist(rebuild: bool = False, stock_code: str = "601398"):
    """
    获取指定股票的日K数据 601857  601398
    """
    stock_hfq_df = ak.stock_zh_a_hist_orm(symbol=stock_code, adjust="")
    db_orm.save_to_mysql_orm(stock_hfq_df, StockDailyInfoEntity, rebuild=rebuild)


if __name__ == '__main__':
    # get_all_stock_name_and_save()
    # get_value_and_save("000001")
    get_stock_comment_and_save(True)
    # get_and_save_stock_hist(stock_code="601398")
