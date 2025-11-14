import akshare as ak


def test_stock_fund_flow_individual():
    """
    个股资金流向
    返回所有股票的资金流向
     symbol:  {“即时”, "3日排行", "5日排行", "10日排行", "20日排行"}
    """
    symbol = "3日排行"
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
    print(df)


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
    test_stock_fund_flow_individual()
