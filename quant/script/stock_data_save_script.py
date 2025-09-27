
import akshare as ak
# 导入模块
import quant.utils.db_orm as db_orm
from quant.entity.StockCommentEntity import StockCommentEntity
# 导入模块中所有类 一般不推荐
# from quant.entity import *
# 导入指定类，从具体文件中导入避免模块冲突
from quant.entity.StockNameEntity import StockNameEntity
from quant.entity.StockHistoryDailyInfoEntity import StockHistoryDailyInfoEntity
from quant.entity.StockDailyEntity import StockDailyEntity


def stock_name_and_save(reBuild: bool = False):
    """
    获取所有股票名称
    """
    df = ak.stock_a_indicator_lg(symbol="all")
    db_orm.save_to_mysql_orm(df, StockNameEntity, reBuild=reBuild)


def stock_value_em_orm(symbol: str, reBuild: bool = False):
    """
    估值分析
    """
    stock_value_em_df = ak.stock_value_em_orm(symbol=symbol)
    db_orm.save_to_mysql_orm(stock_value_em_df, StockDailyEntity, reBuild=reBuild)


def stock_comment_em_orm(reBuild: bool = False):
    """
    千股千评
    """
    df = ak.stock_comment_em_orm()
    db_orm.save_to_mysql_orm(df, StockCommentEntity, reBuild)


def stock_zh_a_hist_orm(reBuild: bool = False, symbol: str = "601398", start_date: str = "19700101",
                        end_date: str = "20500101"):
    """
    获取指定股票历史行情数据
    """
    stock_hfq_df = ak.stock_zh_a_hist_orm(symbol=symbol, adjust="qfq", start_date=start_date, end_date=end_date)
    db_orm.save_to_mysql_orm(stock_hfq_df, StockHistoryDailyInfoEntity, reBuild=reBuild)


def stock_comment_detail_scrd_focus_em(symbol="600000", reBuild=False):
    """
    个股关注度
    """
    df = ak.stock_comment_detail_scrd_focus_em_orm(symbol=symbol)
    print(df.head())
    db_orm.save_with_auto_entity(df=df, table_name="stock_comment_detail_scrd_focus_em_orm", table_comment="个股关注度表",
                                 reBuild=reBuild)


def stock_comment_detail_zlkp_jgcyd_em(symbol="600000", reBuild=False):
    """
    个股机构参与度
    """

    df = ak.stock_comment_detail_zlkp_jgcyd_em_orm(symbol=symbol)
    print(df.head())
    db_orm.save_with_auto_entity(df=df, table_name="stock_comment_detail_zlkp_jgcyd_em_orm", table_comment="个股机构参与度",
                                 reBuild=reBuild)


def stock_comment_detail_zhpj_lspf_em(symbol="600000", reBuild=False):
    """
    个股历史评价
    """
    df = ak.stock_comment_detail_zhpj_lspf_em_orm(symbol=symbol)
    print(df.head())
    db_orm.save_with_auto_entity(df=df, table_name="stock_comment_detail_zhpj_lspf_em_orm", table_comment="个股历史评价表",
                                 reBuild=reBuild)


if __name__ == '__main__':
    symbol = '000001'
    reBuild = True
    stock_name_and_save(reBuild=reBuild)
    stock_comment_em_orm(reBuild=reBuild)
    # 估值
    # print("get_value_and_save")
    stock_value_em_orm(symbol=symbol, reBuild=reBuild)
    print("get_and_save_stock_hist")
    stock_zh_a_hist_orm(symbol=symbol, reBuild=reBuild, start_date="19700101", end_date="20500101")
    print("stock_comment_detail_scrd_focus_em")
    stock_comment_detail_scrd_focus_em(symbol=symbol, reBuild=reBuild)
    print("stock_comment_detail_zlkp_jgcyd_em")
    stock_comment_detail_zlkp_jgcyd_em(symbol=symbol, reBuild=reBuild)
    print("stock_comment_detail_zhpj_lspf_em")
    stock_comment_detail_zhpj_lspf_em(symbol=symbol, reBuild=reBuild)
