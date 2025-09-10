#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2024/8/28 15:00
Desc: To test intention, just write test code here!
"""

import pathlib

from sqlalchemy.orm import declarative_base

import akshare as ak
from akshare.datasets import get_ths_js, get_crypto_info_csv
from akshare.utils.db import save_to_mysql
from akshare.utils.db_orm import save_to_mysql_orm, get_mysql_data_to_df, save_with_auto_entity
from akshare.stock_feature.stock_value_em import covert_columns, columns, stock_value_em_orm
from akshare.stock_feature.stock_hist_em import stock_zh_a_hist_orm
from quant.entity.StockDailyEntity import StockDailyEntity
from quant.entity.StockDailyInfoEntity import StockDailyInfoEntity
from quant.entity import StockNameEntity


def test_stock_comment_em():
    """
    千股千评
    """
    df = ak.stock_comment_em_orm()
    df = df.drop(["SECURITY_CODE"], axis=1)  # 删除列 SECURITY_CODE
    print(f'df.length-------- {len(df)}')
    # SQLAlchemy的declarative_base基类
    Base = declarative_base()
    save_with_auto_entity(df, "stock_comment_em", Base, rebuild=True)


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


def test_save_orm_db():
    """
    通过orm保存数据到mysql

    """
    stock_code = "601398"
    stock_value_em_df = stock_value_em_orm(symbol=stock_code)
    # 保存到 MySQL 数据库
    save_to_mysql_orm(stock_value_em_df, StockDailyEntity)


def test_get_data_orm():
    """
    通过orm方式获取mysql数据
    """

    df = get_mysql_data_to_df(StockDailyInfoEntity, "601857")


def test_stock_zh_a_hist():
    """
    获取指定股票的日K数据 601857  601398
    """
    stock_hfq_df = stock_zh_a_hist_orm(symbol="601398", adjust="")
    # 数据落库
    save_to_mysql_orm(stock_hfq_df, StockDailyInfoEntity, rebuild=True)


def test_get_all_stock_name():
    """
    获取所有股票名称
    """
    df = ak.stock_a_indicator_lg(symbol="all")
    # 保存
    save_to_mysql_orm(df, StockNameEntity, rebuild=True)


if __name__ == "__main__":
    test_cost_living
