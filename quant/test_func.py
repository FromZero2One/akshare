#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2024/8/28 15:00
Desc: To test intention, just write test code here!
"""
import datetime
import pathlib

import akshare as ak
from akshare.datasets import get_ths_js, get_crypto_info_csv
from akshare.stock_feature.stock_hist_em import stock_zh_a_hist_orm
from akshare.stock_feature.stock_value_em import covert_columns, columns, stock_value_em_orm
from quant.entity import StockNameEntity
from quant.entity.StockHistoryDailyInfoEntity import StockHistoryDailyInfoEntity
from quant.entity.StockValueEntity import StockValueEntity
from quant.utils.db import save_to_mysql
from quant.utils.db_orm import save_to_mysql_orm, get_mysql_data_to_df, save_with_auto_entity


# 2025-9-11 22:00:44 基本面
def test_stock_cyq_em():
    """
    筹码分布
    """
    stock_cyq_em_df = ak.stock_cyq_em(symbol="601398", adjust="qfq")
    print(stock_cyq_em_df.head())


def test_stock_fund_flow_individual():
    """
    个股资金流向
    """
    stock_fund_flow_individual_df = ak.stock_fund_flow_individual(symbol="即时")
    print(stock_fund_flow_individual_df)


def test_stock_fhps_em():
    """
    分红推送
    """
    stock_fhps_em_df = ak.stock_fhps_em(date="20231231")
    print(stock_fhps_em_df)


def test_stock_ggcg_em():
    """
    股东增减持
    """
    stock_ggcg_em_df = ak.stock_ggcg_em(symbol="全部")
    print(stock_ggcg_em_df)


def test_stock_xjll_em():
    """
    利润表
    """
    stock_xjll_em_df = ak.stock_xjll_em(date="20240331")
    print(stock_xjll_em_df)


def test_stock_lrb_em():
    """
    利润表
    """
    stock_lrb_em_df = ak.stock_lrb_em(date="20240331")
    print(stock_lrb_em_df)


def test_stock_zcfz_em():
    """
    资产负债表
    """
    stock_zcfz_em_df = ak.stock_zcfz_em(date="20240331")
    print(stock_zcfz_em_df)


def test_stock_yjbb_em():
    """
    业绩报表
    """
    stock_yjbb_em_df = ak.stock_yjbb_em(date="20220331")
    print(stock_yjbb_em_df)


def test_stock_news_main_cx():
    """
    财经精选
    """
    stock_news_main_cx_df = ak.stock_news_main_cx()
    print(stock_news_main_cx_df)


def test_stock_zh_a_hist_em():
    """
    个股新闻资讯
    """
    stock_news_em_df = ak.stock_news_em(symbol="603777")
    print(stock_news_em_df)


def test_stock_comment_detail_scrd_desire_em():
    """
    个股市场参与意愿
    """
    stock_comment_detail_scrd_desire_em_df = ak.stock_comment_detail_scrd_desire_em(symbol="600000")
    print(stock_comment_detail_scrd_desire_em_df)


def test_stock_comment_detail_zhpj_lspf_em():
    """
    个股历史评价
    """
    df = ak.stock_comment_detail_zhpj_lspf_em(symbol="600000")
    print(df.head())
    save_with_auto_entity(df=df, table_name="stock_comment_detail_zhpj_lspf_em", table_comment="个股历史评价表",
                          rebuild=True)


def test_tock_comment_detail_zlkp_jgcyd_em():
    """
    个股机构参与度
    """
    symbol = "600000"
    df = ak.stock_comment_detail_zlkp_jgcyd_em(symbol=symbol)
    print(df.head())
    save_with_auto_entity(df=df, table_name="stock_comment_detail_zlkp_jgcyd_em", table_comment="个股机构参与度",
                          rebuild=True)


def test_stock_comment_detail_scrd_focus_em():
    """
    个股关注度
    """
    Ticker = "600000"
    df = ak.stock_comment_detail_scrd_focus_em(symbol=Ticker)
    print(df.head())
    save_with_auto_entity(df=df, table_name="stock_comment_detail_scrd_focus_em", table_comment="个股关注度表",
                          rebuild=True)


def test_stock_zh_a_minute():
    """
    分时数据  period='1'; 获取 1, 5, 15, 30, 60 分钟的数据频率
    """
    df = ak.stock_zh_a_minute(symbol='sh600751', period='1', adjust="qfq")
    df['Ticker'] = "600751"
    print(df)
    save_with_auto_entity(df=df, table_name="stock_zh_a_minute", table_comment="股票分时数据表",
                          rebuild=True)


def test_stock_comment_em_get():
    table_name = "stock_history_daily_info_entity"
    df = get_mysql_data_to_df(table_name=table_name)
    print(df)


# 千股千评
def test_stock_comment_em_save():
    """
    千股千评
    """
    df = ak.stock_comment_em_orm()
    # df = df.drop(["SECURITY_CODE"], axis=1)  # 删除列 SECURITY_CODE
    print(f'df.length-------- {len(df)}')
    save_with_auto_entity(df=df, table_name="stock_comment_em", table_comment="千股千评表", reBuild=True)


def test_cost_living():
    """
    just for test aim
    :return: assert result
    :rtype: assert
    """
    pass


def test_path_func():
    """
    test path func
    :return: path of file
    :rtype: pathlib.Path
    """
    temp_path = get_ths_js("ths.js")
    assert isinstance(temp_path, pathlib.Path)


def test_zipfile_func():
    """
    test path func
    :return: path of file
    :rtype: pathlib.Path
    """
    temp_path = get_crypto_info_csv("crypto_info.zip")
    assert isinstance(temp_path, pathlib.Path)


def test_save_db():
    """
    获取指定股票的历史估值数据
    """

    stock_code = "601398"
    table_name = "stock_" + stock_code + "_daily_test1"
    stock_value_em_df = ak.stock_value_em(symbol=stock_code)
    # 保存到 MySQL 数据库
    success = save_to_mysql(
        df=stock_value_em_df,
        table_name=table_name,
        convert_columns=covert_columns(),
        columns=columns,
    )

    if success:
        print("数据保存成功")
    else:
        print("数据保存失败")


# 估值分析
def test_save_orm_db():
    """
    通过orm保存数据到mysql
    估值分析
    """
    stock_code = "601398"
    NOW = datetime.datetime.now().strftime("%Y-%m-%d")
    print("NOW: ", NOW)
    stock_value_em_df = stock_value_em_orm(symbol=stock_code, TRADE_DATE=NOW)
    # 保存到 MySQL 数据库
    save_to_mysql_orm(stock_value_em_df, StockValueEntity, rebuild=True)


def test_get_data_orm():
    """
    通过orm方式获取mysql数据
    """

    df = get_mysql_data_to_df(StockHistoryDailyInfoEntity, "601857")


# 获取股票日K数据
def test_stock_zh_a_hist():
    """
    获取指定股票的日K数据 601857  601398
    """
    stock_hfq_df = ak.stock_zh_a_hist_orm(symbol="601398", adjust="")
    # 数据落库
    # save_to_mysql_orm(stock_hfq_df, StockHistoryDailyInfoEntity, reBuild=False)


def test_get_all_stock_name():
    """
    获取所有股票名称
    """
    df = ak.stock_a_indicator_lg(symbol="all")
    # 保存
    save_to_mysql_orm(df, StockNameEntity, reBuild=True)


def test_stock_zh_a_spot_em():
    """
    单次返回所有沪深京 A 股上市公司的实时行情数据
    """
    stock_zh_a_spot_em_df = ak.stock_zh_a_spot_em()
    # 设置显示选项以显示所有列
    import pandas as pd
    pd.set_option('display.max_columns', None)
    print(stock_zh_a_spot_em_df.head())


#  2025-9-29 12:15:09  todo
def test_stock_sh_a_spot_em():
    """
     单次返回所有沪 A 股上市公司的实时行情数据
    """
    df = ak.stock_sh_a_spot_em()
    print(df.head())
    save_with_auto_entity(df=df, table_name="stock_sh_a_spot_em", table_comment="上海A股实时行情表", )


def test_stock_zh_valuation_comparison_em():
    """
    估值比较
    """
    df = ak.stock_zh_valuation_comparison_em(symbol="SZ000895")
    print(df.head())


def test_stock_zh_dupont_comparison_em():
    """
    杜邦分析比较
    """
    df = ak.stock_zh_dupont_comparison_em(symbol="SZ000895")
    print(df.head())


def test_stock_hsgt_hold_stock_em():
    """
    个股排行
    """
    df = ak.stock_hsgt_hold_stock_em(market="沪股通", indicator="5日排行")
    print(df.head())


def test_stock_zcfz_bj_em():
    """
    资产负债表
    """
    df = ak.stock_zcfz_bj_em(date="20240331")
    print(df.head())
    save_with_auto_entity(df=df, table_name="stock_zcfz_bj_em", table_comment="资产负债表表", )


def test_stock_lrb_em():
    """
    利润表
    """
    df = ak.stock_lrb_em(date="20240331")
    print(df.head())
    # save_with_auto_entity(df=df, table_name="stock_lrb_em", table_comment="利润表",)


def test_stock_xjll_em():
    """
    现金流量表
    """
    df = ak.stock_xjll_em(date="20240331")
    print(df.head())
    # save_with_auto_entity(df=df, table_name="stock_xjll_em", table_comment="现金流量表",)


def test_stock_rank_cxg_ths():
    """
    创新高
    """
    df = ak.stock_rank_cxg_ths(symbol="创月新高")
    print(df.head())


def test_stock_hot_rank_detail_realtime_em():
    """
    个股人气指数-实时变动
    """
    df = ak.stock_hot_rank_detail_realtime_em(symbol="SZ000665")
    print(df.head())


def test_stock_hot_rank_em():
    """
    个股人气榜排名
    """
    df = ak.stock_hot_rank_em()
    print(df.head())


def test_stock_hot_follow_xq():
    """
    雪球-股吧-股吧指数
    """
    df = ak.stock_hot_follow_xq()
    print(df.head())


def test_stock_hot_up_em():
    """
    个股人气指数-实时变动
    """
    df = ak.stock_hot_up_em()
    print(df.head())


def test_stock_hot_keyword_em():
    """
    个股人气指数-关键词
    """
    df = ak.stock_hot_keyword_em(symbol="SZ000665")
    print(df.head())


def test_stock_zt_pool_em():
    """
    涨停股池
    """
    df = ak.stock_zt_pool_em(date=datetime.date.strftime(datetime.date.today(), "%Y%m%d"))
    print(df.head())


def test_stock_zt_pool_previous_em():
    """
    昨日涨停股池
    """
    df = ak.stock_zt_pool_previous_em(date=datetime.date.today().strftime("%Y%m%d"))
    print(df.head())


def main():
    test_stock_fund_flow_individual()


if __name__ == "__main__":
    main()
