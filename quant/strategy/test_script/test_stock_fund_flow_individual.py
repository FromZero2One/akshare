import datetime

import akshare as ak
from quant.utils.db_orm import save_with_auto_entity


def test_stock_fund_flow_individual():
    """
    个股资金流向
    返回所有股票的资金流向
     symbol:  {“即时”, "3日排行", "5日排行", "10日排行", "20日排行"}
    """

    symbols = ["即时", "3日排行", "5日排行", "10日排行", "20日排行"]
    for symbol in symbols:
        print(f'开始查询数据---{symbol}')
        get_and_save(symbol)


def get_and_save(symbol="即时"):
    df = ak.stock_fund_flow_individual(symbol=symbol)
    columns_to_convert = ["净额", "流入资金", "流出资金", "成交额"]
    for column in columns_to_convert:
        if column in df.columns:
            # apply 对Series中的每个元素执行convert_amount函数
            df[column] = df[column].apply(convert_amount)
    # ascending 表示降序
    df = df.sort_values(by=["净额"], ascending=True)
    # 重命名字段
    df = df.rename(columns={col: f"{col}(万)" for col in columns_to_convert if col in df.columns})
    df['create_time'] = datetime.datetime.now()
    df['type'] = symbol
    print(df.head())
    # 保存
    save_with_auto_entity(df=df, table_name="stock_fund_flow_individual", table_comment="个股资金流向表", reBuild=False)


def convert_amount(amount_str):
    try:
        amount_str = str(amount_str)
        if "亿" in amount_str:
            return float(amount_str.replace("亿", "")) * 10000
        elif "万" in amount_str:
            return float(amount_str.replace("万", ""))
        else:
            return float(amount_str)
    except:
        return amount_str  # 如果转换失败，返回原始值


if __name__ == "__main__":
    get_and_save()