import stock_data_save_script as ads
from quant.entity.StockNameEntity import StockNameEntity
import quant.utils.db_orm as db_orm


def main():
    # 千股千评
    # ads.stock_comment_em_orm(reBuild=True)

    symbol = "600000"
    # 获取所有股票名称
    # all_stock_name_df = db_orm.get_mysql_data_to_df(orm_class=StockNameEntity)
    # 获取指定股票历史行情数据
    # ads.stock_zh_a_hist_orm(reBuild=True, symbol=symbol, start_date="20220101", end_date="20221231")
    # 估值分析
    ads.stock_value_em_orm(symbol='', TRADE_DATE="2025-09-25", reBuild=True)
    # 个股关注度
    # ads.stock_comment_detail_scrd_focus_em(symbol=symbol, reBuild=True)
    # 个股机构参与度
    # ads.stock_comment_detail_zlkp_jgcyd_em(symbol=symbol, reBuild=True)
    # 个股综合评分与历史评分
    # ads.stock_comment_detail_zhpj_lspf_em(symbol=symbol, reBuild=True)


if __name__ == '__main__':
    main()
