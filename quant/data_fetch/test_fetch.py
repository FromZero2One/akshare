#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2024/8/28 15:00
Desc: To test intention, just write test code here!
"""
import datetime
import os
import sys

_PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import akshare as ak
from akshare.stock_feature.stock_value_em import (
    stock_value_em_orm,
)
from quant.utils.db_orm import get_mysql_data_to_df



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
    try:
        stock_comment_detail_scrd_desire_em_df = ak.stock_comment_detail_scrd_desire_em(symbol="600000")
    except Exception as e:
        print(f"  ⊘ 跳过: stock_comment_detail_scrd_desire_em 异常 ({type(e).__name__}: {str(e)[:120]})")
        return
    if stock_comment_detail_scrd_desire_em_df is None:
        print("  ⊘ 跳过: stock_comment_detail_scrd_desire_em 返回 None (东方财富接口可能无该股票数据)")
        return
    print(stock_comment_detail_scrd_desire_em_df)


def test_stock_comment_detail_zhpj_lspf_em():
    """
    个股历史评价
    """
    df = ak.stock_comment_detail_zhpj_lspf_em(symbol="600000")
    print(df.head())



def test_tock_comment_detail_zlkp_jgcyd_em():
    """
    个股机构参与度
    """
    symbol = "600000"
    df = ak.stock_comment_detail_zlkp_jgcyd_em(symbol=symbol)
    print(df.head())



def test_stock_comment_detail_scrd_focus_em():
    """
    个股关注度
    """
    Ticker = "600000"
    df = ak.stock_comment_detail_scrd_focus_em(symbol=Ticker)
    print(df.head())



def test_stock_zh_a_minute():
    """
    分时数据  period='1'; 获取 1, 5, 15, 30, 60 分钟的数据频率
    """
    df = ak.stock_zh_a_minute(symbol='sh600751', period='1', adjust="qfq")
    df['Ticker'] = "600751"
    print(df)



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
    print(df)




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
    print(stock_value_em_df)


# 获取股票日K数据
def test_stock_zh_a_hist():
    """
    获取指定股票的日K数据 601857  601398
    替代源: 新浪 stock_zh_a_daily (eastmoney 拒绝连接)
    """
    stock_hfq_df = ak.stock_zh_a_daily(symbol="sh601398", adjust="qfq")
    print(f"日 K 数据: {len(stock_hfq_df)} 行, 列={list(stock_hfq_df.columns)[:5]}")
    print(stock_hfq_df.head())



def test_get_all_stock_name():
    """
    获取所有股票名称
    """
    df = ak.stock_a_indicator_lg(symbol="all")
    print(df.head())


def test_stock_zh_a_spot_em():
    """
    单次返回所有沪深京 A 股上市公司的实时行情数据
    替代源: 腾讯 stock_zh_a_spot (eastmoney 服务器拒绝连接)
    说明: 用 _get_zh_a_spot_cached 缓存, 让 [24] 沪 A 股过滤复用
    """
    global _ZH_A_SPOT_CACHE, _ZH_A_SPOT_FAILED
    try:
        stock_zh_a_spot_em_df = _get_zh_a_spot_cached()
    except Exception as e:
        print(f"  ⊘ 跳过: ak.stock_zh_a_spot 失败 ({type(e).__name__}: {str(e)[:60]})")
        _ZH_A_SPOT_CACHE = None
        _ZH_A_SPOT_FAILED = True
        return
    # 设置显示选项以显示所有列
    import pandas as pd
    pd.set_option('display.max_columns', None)
    print(stock_zh_a_spot_em_df.head())


def test_stock_sh_a_spot_em():
    """
     单次返回所有沪 A 股上市公司的实时行情数据
     说明: 沪 A 股 = [23] 沪深京全量的子集, 直接复用 _get_zh_a_spot_cached 缓存
     (避免连续两次调 sina 被封 IP)
    """
    df = _get_zh_a_spot_cached()
    if df is None:
        print("  ⊘ 跳过: [23] 上游失败, 无数据可过滤")
        return
    sh_df = df[df["代码"].str.startswith("sh", na=False)].copy()
    print(f"沪 A 股共 {len(sh_df)} 行 (全部 {len(df)} 行中的子集)")
    print(sh_df.head())


# 模块级缓存 (避免连续 2 次调 sina 被封 IP)
_ZH_A_SPOT_CACHE = None
_ZH_A_SPOT_FAILED = False


def _get_zh_a_spot_cached():
    """获取沪深京 A 股实时行情 (单次进程内缓存)"""
    global _ZH_A_SPOT_CACHE, _ZH_A_SPOT_FAILED
    if _ZH_A_SPOT_FAILED:
        return None
    if _ZH_A_SPOT_CACHE is None:
        try:
            _ZH_A_SPOT_CACHE = ak.stock_zh_a_spot()
        except Exception as e:
            _ZH_A_SPOT_FAILED = True
            raise  # 让调用方处理
    return _ZH_A_SPOT_CACHE


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
    try:
        df = ak.stock_hsgt_hold_stock_em(market="沪股通", indicator="5日排行")
    except Exception as e:
        print(f"  ⊘ 跳过: stock_hsgt_hold_stock_em 异常 ({type(e).__name__}: {str(e)[:120]})")
        return
    if df is None:
        print("  ⊘ 跳过: stock_hsgt_hold_stock_em 返回 None (沪股通数据可能为空或接口异常)")
        return
    print(df.head())


def test_stock_zcfz_bj_em():
    """
    资产负债表
    """
    df = ak.stock_zcfz_bj_em(date="20240331")
    print(df.head())


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
    try:
        df = ak.stock_hot_rank_em()
    except Exception as e:
        print(f"  ⊘ 跳过: stock_hot_rank_em 网络异常 ({type(e).__name__}: {str(e)[:120]})")
        return
    if df is None:
        print("  ⊘ 跳过: stock_hot_rank_em 返回 None (东方财富接口无数据)")
        return
    print(df.head())


def test_stock_hot_follow_xq():
    """
    雪球-股吧-股吧指数
    """
    df = ak.stock_hot_follow_xq()
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


# 测试函数映射表
TEST_FUNCTIONS = {
    "2": ("个股资金流向", test_stock_fund_flow_individual),
    "3": ("分红推送", test_stock_fhps_em),
    "4": ("股东增减持", test_stock_ggcg_em),
    "5": ("现金流量表", test_stock_xjll_em),
    "6": ("利润表", test_stock_lrb_em),
    "7": ("资产负债表", test_stock_zcfz_em),
    "8": ("业绩报表", test_stock_yjbb_em),
    "9": ("财经精选", test_stock_news_main_cx),
    "10": ("个股新闻资讯", test_stock_zh_a_hist_em),
    "11": ("个股市场参与意愿", test_stock_comment_detail_scrd_desire_em),
    "12": ("个股历史评价", test_stock_comment_detail_zhpj_lspf_em),
    "13": ("个股机构参与度", test_tock_comment_detail_zlkp_jgcyd_em),
    "14": ("个股关注度", test_stock_comment_detail_scrd_focus_em),
    "15": ("分时数据", test_stock_zh_a_minute),
    "16": ("从数据库读取评论", test_stock_comment_em_get),
    "17": ("千股千评", test_stock_comment_em_save),
    "19": ("ORM保存估值分析", test_save_orm_db),
    "21": ("获取日K数据 [新浪源]", test_stock_zh_a_hist),
    "22": ("获取所有股票名称", test_get_all_stock_name),
    "23": ("沪深京A股实时行情 [腾讯源]", test_stock_zh_a_spot_em),
    "24": ("沪A股实时行情 [腾讯源过滤]", test_stock_sh_a_spot_em),
    "25": ("估值比较", test_stock_zh_valuation_comparison_em),
    "26": ("杜邦分析比较", test_stock_zh_dupont_comparison_em),
    "27": ("沪股通排行", test_stock_hsgt_hold_stock_em),
    "28": ("北交所资产负债表", test_stock_zcfz_bj_em),
    "29": ("利润表(重复)", test_stock_lrb_em),
    "30": ("现金流量表(重复)", test_stock_xjll_em),
    "31": ("创新高", test_stock_rank_cxg_ths),
    "32": ("个股人气指数-实时变动", test_stock_hot_rank_detail_realtime_em),
    "33": ("个股人气榜排名", test_stock_hot_rank_em),
    "34": ("雪球股吧指数", test_stock_hot_follow_xq),
    "36": ("个股人气指数-关键词", test_stock_hot_keyword_em),
    "37": ("涨停股池", test_stock_zt_pool_em),
    "38": ("昨日涨停股池", test_stock_zt_pool_previous_em),
}


def run_all_tests():
    """运行所有测试函数"""
    print("=" * 60)
    print("开始运行所有测试...")
    print("=" * 60)

    passed, failed, skipped = 0, 0, 0
    for key, (name, func) in TEST_FUNCTIONS.items():
        print(f"\n[{key}] 运行测试: {name}")
        print("-" * 60)
        try:
            func()
            print(f"✓ 测试 {name} 完成")
            passed += 1
        except Exception as e:
            print(f"✗ 测试 {name} 失败: {type(e).__name__}: {str(e)[:200]}")
            failed += 1
        print("-" * 60)

    print("\n" + "=" * 60)
    print(f"汇总: ✓ {passed}  ✗ {failed}  (共 {len(TEST_FUNCTIONS)})")
    print("=" * 60)
    if failed:
        sys.exit(1)


def run_selected_test(test_id: str):
    """运行指定的测试函数"""
    if test_id in TEST_FUNCTIONS:
        name, func = TEST_FUNCTIONS[test_id]
        print("=" * 60)
        print(f"运行测试: {name}")
        print("=" * 60)
        try:
            func()
            print(f"\n✓ 测试 {name} 完成")
        except Exception as e:
            print(f"\n✗ 测试 {name} 失败: {type(e).__name__}: {str(e)[:200]}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    else:
        print(f"错误: 未找到测试 ID '{test_id}'")
        sys.exit(1)


def show_menu():
    """显示测试菜单"""
    print("\n" + "=" * 60)
    print("可用测试列表:")
    print("=" * 60)
    for key, (name, _) in TEST_FUNCTIONS.items():
        print(f"  [{key}] {name}")
    print("  [all] 运行所有测试")
    print("  [q] 退出")
    print("=" * 60)


if __name__ == "__main__":

    # 如果提供了命令行参数，直接运行对应的测试
    if len(sys.argv) > 1:
        test_id = sys.argv[1]
        if test_id.lower() == 'all':
            run_all_tests()
        elif test_id.lower() == 'q':
            print("退出")
        else:
            run_selected_test(test_id)
    else:
        # 没有参数，显示菜单并等待输入
        while True:
            show_menu()
            choice = input("\n请输入要运行的测试编号 (或 'all' 运行所有, 'q' 退出): ").strip()

            if choice.lower() == 'q':
                print("退出")
                break
            elif choice.lower() == 'all':
                run_all_tests()
            else:
                run_selected_test(choice)

            input("\n按 Enter 继续...")
