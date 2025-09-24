#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2024/11/26 18:00
Desc: 东方财富网-数据中心-估值分析-每日互动-每日互动-估值分析
https://data.eastmoney.com/gzfx/detail/300766.html
"""
from datetime import datetime

import pandas as pd

from akshare.request import make_request_with_retry_json

columns = {
    "TRADE_DATE": "数据日期",
    "CLOSE_PRICE": "当日收盘价",
    "CHANGE_RATE": "当日涨跌幅",
    "TOTAL_MARKET_CAP": "总市值",
    "NOTLIMITED_MARKETCAP_A": "流通市值",
    "TOTAL_SHARES": "总股本",
    "FREE_SHARES_A": "流通股本",
    "PE_TTM": "PE(TTM)",
    "PE_LAR": "PE(静)",
    "PB_MRQ": "市净率",
    "PEG_CAR": "PEG值",
    "PCF_OCF_TTM": "市现率",
    "PS_TTM": "市销率",
}


def covert_columns():
    # 键值互换后的字典（反向字段映射）
    reverse_field_mapping = {v: k for k, v in columns.items()}
    return reverse_field_mapping


def stock_value_em(symbol: str = "300766") -> pd.DataFrame:
    """
    东方财富网-数据中心-估值分析-每日互动-每日互动-估值分析
    https://data.eastmoney.com/gzfx/detail/300766.html
    :param symbol: 股票代码
    :type symbol: str
    :return: 估值分析
    :rtype: pandas.DataFrame
    """
    url = "https://datacenter-web.eastmoney.com/api/data/v1/get"
    params = {
        "sortColumns": "TRADE_DATE",
        "sortTypes": "-1",
        "pageSize": "5000",
        "pageNumber": "1",
        "reportName": "RPT_VALUEANALYSIS_DET",
        "columns": "ALL",
        "quoteColumns": "",
        "source": "WEB",
        "client": "WEB",
        "filter": f'(SECURITY_CODE="{symbol}")',
    }
    data_json = make_request_with_retry_json(url, params=params)
    temp_json = data_json["result"]["data"]
    temp_df = pd.DataFrame(temp_json)
    # 修改列名   inplace=True 直接修改原对象
    temp_df.rename(
        columns=columns,
        inplace=True,
    )
    temp_df = temp_df[
        [
            "数据日期",
            "当日收盘价",
            "当日涨跌幅",
            "总市值",
            "流通市值",
            "总股本",
            "流通股本",
            "PE(TTM)",
            "PE(静)",
            "市净率",
            "PEG值",
            "市现率",
            "市销率",
        ]
    ]
    # errors ="coerce"  表示转换时遇到错误时，将错误值替换为NaN
    temp_df["数据日期"] = pd.to_datetime(temp_df["数据日期"], errors="coerce").dt.date
    for item in temp_df.columns[1:]:
        temp_df[item] = pd.to_numeric(temp_df[item], errors="coerce")
    temp_df.sort_values(by="数据日期", ignore_index=True, inplace=True)
    return temp_df


def stock_value_em_orm(symbol: str = "300766") -> pd.DataFrame:
    url = "https://datacenter-web.eastmoney.com/api/data/v1/get"
    params = {
        "sortColumns": "TRADE_DATE",
        "sortTypes": "-1",
        "pageSize": "5000",
        "pageNumber": "1",
        "reportName": "RPT_VALUEANALYSIS_DET",
        "columns": "ALL",
        "quoteColumns": "",
        "source": "WEB",
        "client": "WEB",
        "filter": f'(SECURITY_CODE="{symbol}")',
    }
    data_json = make_request_with_retry_json(url, params=params)
    if data_json['code'] != 0:
        print(f"请求数据失败, 返回信息: {data_json}")
        return pd.DataFrame()
    temp_json = data_json["result"]["data"]
    temp_df = pd.DataFrame(temp_json)
    # 添加股票代码列
    temp_df["symbol"] = symbol
    temp_df['create_date'] = datetime.now().date()
    # temp_df["数据日期"] = pd.to_datetime(temp_df["数据日期"], errors="coerce").dt.date
    for item in temp_df.columns[1:]:
        if item == 'TRADE_DATE':
            temp_df[item] = pd.to_datetime(temp_df[item], errors="coerce").dt.date
        elif item == 'symbol':
            temp_df[item] = temp_df[item].astype(str)
        elif item == 'create_date':
            temp_df[item] = pd.to_datetime(temp_df[item]).dt.date
        else:
            temp_df[item] = pd.to_numeric(temp_df[item], errors="coerce")

    temp_df.sort_values(by="TRADE_DATE", ignore_index=True, inplace=True)
    # None的列替换成0
    temp_df = temp_df.fillna('0')
    return temp_df


if __name__ == "__main__":
    stock_code = "601398"
    table_name = "stock_" + stock_code + "_daily"
    # get
    stock_value_em_df = stock_value_em_orm(symbol=stock_code)
    print(stock_value_em_df)

    #  save
    # save_to_mysql(df=stock_value_em_df, table_name=table_name, convert_columns=covert_columns(),
    #     columns=columns)
