import akshare as ak


def test_stock_cyq_em():
    """
    筹码分布
    """
    stock_cyq_em_df = ak.stock_cyq_em(symbol="601398", adjust="qfq")
    print(stock_cyq_em_df.head())


if __name__ == "__main__":
    test_stock_cyq_em()
