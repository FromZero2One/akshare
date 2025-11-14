


import akshare as ak

def test_stock_fund_flow_individual():
    """
    个股资金流向
    """
    stock_fund_flow_individual_df = ak.stock_fund_flow_individual(symbol="即时")
    print(stock_fund_flow_individual_df)


if __name__ == "__main__":
    test_stock_fund_flow_individual()
