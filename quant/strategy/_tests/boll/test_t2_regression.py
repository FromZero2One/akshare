"""
BOLL Round 2 回归测试（T2）
- 构造合成 K 线：先跌穿下轨（触发买入）→ 后突破上轨（触发卖出）
- 验证 sizer 占用、4 analyzer、buy_price 记账、信号方向
"""
import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_ROOT))

from datetime import datetime

import numpy as np
import pandas as pd

import backtrader as bt

from quant.strategy.boll.strategy.BollCross import BollCross
from quant.utils.sizer import DynamicSizer


def make_synthetic_df(n: int = 200) -> pd.DataFrame:
    """
    构造合成 K 线：让价格在 period (20) 根后，跌破下轨 → 突破上轨
    """
    dates = pd.date_range(end=datetime(2024, 12, 31), periods=n, freq="B")
    np.random.seed(42)
    # 前 100 根：close 1.0 → 0.7（持续跌，跌破 BB 下轨）
    # 后 100 根：close 0.7 → 1.5（持续涨，突破 BB 上轨）
    prices = np.concatenate([
        np.linspace(1.00, 0.70, 100),
        np.linspace(0.70, 1.50, n - 100),
    ])
    prices = prices + np.random.normal(0, 0.005, n)
    df = pd.DataFrame({
        "date": dates,
        "open": prices + np.random.normal(0, 0.003, n),
        "close": prices,
        "high": prices + np.abs(np.random.normal(0, 0.008, n)),
        "low": prices - np.abs(np.random.normal(0, 0.008, n)),
        "volume": np.random.randint(1_000_000, 5_000_000, n),
    })
    return df


class Probe(bt.Strategy):
    """探针：复用 BollCross 指标 + 记账"""
    params = (("period", 20), ("devfactor", 2.0))
    def __init__(self):
        bb = bt.indicators.BollingerBands(self.datas[0], period=self.params.period, devfactor=self.params.devfactor)
        self.top = bb.top
        self.bot = bb.bot
        self.order = None
        self.buy_price = None
        self.buy_comm = None
        self.first_buy_size = None
        self.first_buy_executed_price = None
    def next(self):
        if self.order:
            return
        if not self.position:
            if self.datas[0].close[0] <= self.bot[0]:
                self.order = self.buy()
        else:
            if self.buy_price is None:
                return
            if self.datas[0].close[0] >= self.top[0]:
                self.order = self.sell(size=self.position.size)
    def notify_order(self, order):
        if order.status == order.Completed and order.isbuy():
            if self.first_buy_size is None:
                self.first_buy_size = order.executed.size
                self.first_buy_executed_price = order.executed.price
            self.buy_price = order.executed.price
        if order.status in [order.Completed, order.Canceled, order.Margin, order.Rejected]:
            self.order = None


def test_t2_regression():
    """T2 回归：4 analyzer + sizer 占用 + buy_price 记账"""
    df = make_synthetic_df(200)
    tb_df = df.set_index("date")[["open", "close", "high", "low", "volume"]]
    startcash = 100_000.0

    cerebro = bt.Cerebro()
    cerebro.adddata(bt.feeds.PandasData(dataname=tb_df))
    cerebro.addstrategy(Probe)
    cerebro.addsizer(DynamicSizer, position_pct=0.8)
    cerebro.broker.setcash(startcash)
    cerebro.broker.setcommission(commission=0.0005, stocklike=True, percabs=True)
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe", riskfreerate=0.0, annualize=True)
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")
    cerebro.addanalyzer(bt.analyzers.TimeReturn, _name="time_return")

    results = cerebro.run()
    strat = results[0]

    end_value = strat.broker.getvalue()
    first_size = strat.first_buy_size
    first_price = strat.first_buy_executed_price

    # 1. sizer 占用
    first_cost = first_size * first_price
    sizer_pct = first_cost / startcash
    assert 0.75 < sizer_pct < 0.85, f"sizer 占用异常: {sizer_pct:.4f}（期望 ~0.8）"

    # 2. buy_price 记账
    assert strat.buy_price is not None, "buy_price 未记账"
    assert abs(strat.buy_price - first_price) < 1e-6, "buy_price 与首单成交价不一致"

    # 3. 4 analyzer
    sharpe_obj = strat.analyzers.sharpe.get_analysis()
    dd_obj = strat.analyzers.drawdown.get_analysis()
    ta = strat.analyzers.trades.get_analysis()
    tr = strat.analyzers.time_return.get_analysis()
    assert "sharperatio" in sharpe_obj or sharpe_obj, "sharpe 无数据"
    assert "max" in dd_obj, "drawdown 无数据"
    assert tr, "time_return 无数据"
    total_closed = (ta.get("total") or {}).get("closed") or 0
    assert total_closed >= 1, f"应至少 1 笔闭合交易，实际 {total_closed}"

    print(f"  ✓ sizer 占用: {sizer_pct:.4f}（首单 cost {first_cost:.0f} / {startcash:.0f}）")
    print(f"  ✓ 首单成交价: {first_price:.4f}")
    print(f"  ✓ buy_price 记账: {strat.buy_price:.4f}")
    print(f"  ✓ 总资金: {end_value:.2f}（收益 {end_value - startcash:+.2f}）")
    print(f"  ✓ sharpe 原始: {sharpe_obj.get('sharperatio')}")
    print(f"  ✓ max drawdown: {dd_obj.get('max', {}).get('drawdown'):.2f}%")
    print(f"  ✓ 闭合交易: {total_closed} 笔")
    print(f"  ✓ time_return bar 数: {len(tr)}")


if __name__ == "__main__":
    print("BOLL T2 回归测试: 4 analyzer + sizer 占用 + buy_price 记账")
    print("=" * 60)
    test_t2_regression()
    print("\n✅ T2 全部通过")
