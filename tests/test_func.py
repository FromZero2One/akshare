#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2024/8/28 15:00
Desc: To test intention, just write test code here!
"""

import pathlib

import akshare as ak
from akshare.datasets import get_ths_js, get_crypto_info_csv
from akshare.utils.db import save_to_mysql
from akshare.utils.db_orm import save_to_mysql_orm,get_data_to_df
from akshare.stock_feature.stock_value_em import covert_columns, columns, stock_value_em_orm
from tests.StockDailyEntity import StockDailyEntity


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
    stock_code = "601398"
    stock_value_em_df = stock_value_em_orm(symbol=stock_code)
    # 保存到 MySQL 数据库
    save_to_mysql_orm(stock_value_em_df, StockDailyEntity)



def test_get_data_orm():
    df = get_data_to_df(StockDailyEntity)


def test_stock_zh_a_hist():
    stock_hfq_df = ak.stock_zh_a_hist(symbol="601398", adjust="").iloc[:, :7]
    del stock_hfq_df['股票代码']


if __name__ == "__main__":
    # test_cost_living()
    # test_path_func()
    # test_zipfile_func()
    # test_save_db()
    test_save_orm_db()
    # test_stock_zh_a_hist()
