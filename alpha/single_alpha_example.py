import numpy as np
import pandas as pd

from alpha.alpha101 import Alphas
from alpha.alpha_script import getAlphaDataDF


# 获取需要的类和函数

def create_sample_data():
    """
    创建示例股票数据
    """
    # 生成100天的示例数据
    dates = pd.date_range('2023-01-01', periods=100, freq='D')
    np.random.seed(42)

    # 生成基础价格数据
    prices = 100 + np.cumsum(np.random.randn(100) * 0.5)

    # 基于价格生成其他数据
    opens = prices + np.random.randn(100) * 0.2
    closes = prices + np.random.randn(100) * 0.2
    highs = np.maximum(opens, closes) + np.abs(np.random.randn(100) * 0.3)
    lows = np.minimum(opens, closes) - np.abs(np.random.randn(100) * 0.3)

    volumes = np.random.randint(100000, 1000000, size=100)
    amounts = volumes * prices
    returns = (closes / np.roll(closes, 1) - 1) * 100
    returns[0] = 0  # 第一天收益率设为0

    # 创建DataFrame
    df = pd.DataFrame({
        'S_DQ_OPEN': opens,
        'S_DQ_CLOSE': closes,
        'S_DQ_HIGH': highs,
        'S_DQ_LOW': lows,
        'S_DQ_VOLUME': volumes / 100,  # 调整单位
        'S_DQ_AMOUNT': amounts / 1000,  # 调整单位
        'S_DQ_PCTCHANGE': returns
    }, index=dates)

    return df


def main():
    print("Alpha#101 使用示例")
    print("=" * 50)

    # 创建示例数据
    # df = create_sample_data()
    df = getAlphaDataDF()
    print(f"数据形状: {df.shape}")
    print("\n前5行数据:")
    print(df.head())

    # 创建Alpha计算器实例
    alphas = Alphas(df)

    # 计算几个有代表性的Alpha因子
    print("\n计算Alpha因子:")

    # Alpha#22: (-1 * (delta(correlation(high, volume, 5), 5) * rank(stddev(close, 20))))
    alpha22 = alphas.alpha022()
    print(f"\nAlpha#22 (最后5个值):")
    print(alpha22.tail())

    # Alpha#01: (rank(Ts_ArgMax(SignedPower(((returns < 0) ? stddev(returns, 20) : close), 2.), 5)) -0.5)
    alpha01 = alphas.alpha001()
    print(f"\nAlpha#01 (最后5个值):")
    print(alpha01.tail())

    # Alpha#03: (-1 * correlation(rank(open), rank(volume), 10))
    alpha03 = alphas.alpha003()
    print(f"\nAlpha#03 (最后5个值):")
    print(alpha03.tail())

    print("\n示例完成!")


if __name__ == "__main__":
    main()
