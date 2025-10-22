import quant.utils.db_orm as db
from alpha101 import Alphas
from quant.entity.StockHistoryDailyInfoEntity import StockHistoryDailyInfoEntity


def getAlphaDataDF():
    """
    获取用于计算Alpha因子的数据，并进行必要的预处理。
    """
    df = db.get_mysql_data_to_df(orm_class=StockHistoryDailyInfoEntity)
    df.rename(columns={"open": "S_DQ_OPEN",
                       "close": "S_DQ_CLOSE",
                       "high": "S_DQ_HIGH",
                       "low": "S_DQ_LOW",
                       "volume": "S_DQ_VOLUME",
                       "Trading_Value": "S_DQ_AMOUNT",
                       "Price_Limit_Change": "S_DQ_PCTCHANGE",
                       "date": "date",
                       }, inplace=True)
    # 设置日期列为索引
    df.set_index('date', inplace=True)
    #   选择需要的列
    df = df[["S_DQ_OPEN",
             "S_DQ_CLOSE",
             "S_DQ_LOW",
             "S_DQ_HIGH",
             "S_DQ_VOLUME",  # 成交量
             "S_DQ_AMOUNT",  # 成交额
             "S_DQ_PCTCHANGE",  # 涨跌幅
             ]]
    return df


if __name__ == "__main__":

    df = getAlphaDataDF()

    # 创建Alphas对象
    alpha_calculator = Alphas(df)
    print("\n计算多个Alpha因子:")
    alpha_list = ['alpha001', 'alpha002', 'alpha003', 'alpha022']
    # 为DataFrame添加Alpha因子列
    df_with_alphas = df.copy()
    for alpha_name in alpha_list:
        alpha_method = getattr(alpha_calculator, alpha_name)
        df_with_alphas[alpha_name] = alpha_method()

    print("包含Alpha因子的数据前5行:")
    print(df_with_alphas[['alpha001', 'alpha002', 'alpha003', 'alpha022']].head(10))
