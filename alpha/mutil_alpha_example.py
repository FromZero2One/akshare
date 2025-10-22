import numpy as np
import pandas as pd

from alpha.alpha101 import Alphas, get_alpha
from alpha.alpha_script import getAlphaDataDF


# 主函数演示如何使用Alphas类
def main():
    df = getAlphaDataDF()
    print("示例数据前5行:")
    print(df.head())
    print("\n数据形状:", df.shape)

    # 创建Alphas对象
    alpha_calculator = Alphas(df)

    # 计算特定的Alpha因子
    print("\n计算Alpha#22因子:")
    alpha22 = alpha_calculator.alpha022()
    print(alpha22.tail(10))  # 显示最后10个值

    # 计算多个Alpha因子
    print("\n计算多个Alpha因子:")
    alpha_list = ['alpha001', 'alpha002', 'alpha003', 'alpha022']

    # 为DataFrame添加Alpha因子列
    df_with_alphas = df.copy()
    for alpha_name in alpha_list:
        alpha_method = getattr(alpha_calculator, alpha_name)
        df_with_alphas[alpha_name] = alpha_method()

    print("包含Alpha因子的数据前5行:")
    print(df_with_alphas[['S_DQ_CLOSE', 'alpha001', 'alpha002', 'alpha003', 'alpha022']].head(10))

    # 使用get_alpha函数计算所有Alpha因子
    print("\n使用get_alpha函数计算所有Alpha因子:")
    # 注意: 由于数据量较小，许多Alpha因子可能无法计算(返回NaN)
    df_all_alphas = df.copy()
    try:
        df_all_alphas = get_alpha(df_all_alphas)
        print("成功计算所有Alpha因子，数据形状:", df_all_alphas.shape)
        # 显示部分Alpha因子
        alpha_columns = [col for col in df_all_alphas.columns if col.startswith('alpha')]
        print("计算出的前10个Alpha因子的后5行数据", df_all_alphas[alpha_columns[:10]].tail(5))
    except Exception as e:
        print(f"计算所有Alpha因子时出错: {e}")


if __name__ == "__main__":
    main()
