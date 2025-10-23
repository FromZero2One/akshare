from quant.strategy.sma.SmaCross import SmaCross

from quant.strategy.sma.SmaStrategyScript import strategy_back_trader

if __name__ == '__main__':
    # 获取所有symbol列表

    strategy_back_trader(strategy=SmaCross)
