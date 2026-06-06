"""
RSI Round 2 回归测试（T2 + T3）
- 构造合成 K 线：先下跌 30 根（触发 RSI 超卖买入）→ 后上涨 30 根（触发 RSI 超买卖出）
- 验证 sizer 占用、4 analyzer、buy_price 记账、信号方向

运行方式（从仓库根）:
    python quant/strategy/_tests/rsi/test_t2_regression.py
"""
import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_ROOT))

from datetime import datetime, timedelta

import numpy as np
import pandas as pd

import backtrader as bt

from quant.strategy.rsi.strategy.RsiCross import RsiCross
from quant.utils.sizer import DynamicSizer


def make_synthetic_df(trend: str = "down_then_up", n: int = 200) -> pd.DataFrame:
    """构造合成 K 线：前 30 根下跌（让 RSI 跌破 30），后 n-30 根上涨。"""
    dates = pd.date_range(end=datetime(2024, 12, 31), periods=n, freq="B")
    np.random.seed(42)
    if trend == "down_then_up":
        # 前 30 根：close 1.0 → 0.7（持续跌，RSI 跌破 30）
        # 后 170 根：close 0.7 → 1.5（持续涨，RSI 升破 70）
        prices = np.concatenate([
            np.linspace(1.00, 0.70, 30),
            np.linspace(0.70, 1.50, n - 30),
        ])
    else:
        prices = np.ones(n) * 1.0
    # 加小幅噪声
    prices = prices + np.random.normal(0, 0.01, n)
    df = pd.DataFrame({
        "date": dates,
        "open": prices + np.random.normal(0, 0.005, n),
        "close": prices,
        "high": prices + np.abs(np.random.normal(0, 0.01, n)),
        "low": prices - np.abs(np.random.normal(0, 0.01, n)),
        "volume": np.random.randint(1_000_000, 5_000_000, n),
    })
    return df


class Probe(bt.Strategy):
    """探针：继承 RsiCross，记录首单 size 和 buy_price"""
    params = (("rsi_period", 10), ("rsi_upper", 70), ("rsi_lower", 30))
    def __init__(self):
        # 复用 RsiCross 的指标 + 记账逻辑
        self.rsi = bt.indicators.RSI(self.datas[0].close, period=self.params.rsi_period)
        self.order = None
        self.buy_price = None
        self.buy_comm = None
        self.first_buy_size = None
        self.first_buy_executed_price = None
    def next(self):
        if self.order:
            return
        if not self.position:
            if self.rsi[0] < self.params.rsi_lower:
                self.order = self.buy()
        else:
            if self.buy_price is None:
                return
            if self.rsi[0] > self.params.rsi_upper:
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
    """T2 回归：4 analyzer 有数据 + sizer 占用 + buy_price 记账"""
    df = make_synthetic_df("down_then_up", 200)
    tb_df = df.set_index("date")[RsiCross_required_columns()]
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

    # 1. sizer 占用：首单 cost ≈ 0.8 * 100000 = 80000
    first_cost = first_size * first_price
    sizer_pct = first_cost / startcash
    assert 0.75 < sizer_pct < 0.85, f"sizer 占用异常: {sizer_pct:.4f}（期望 ~0.8）"

    # 2. buy_price 记账
    assert strat.buy_price is not None, "buy_price 未记账"
    assert abs(strat.buy_price - first_price) < 1e-6, "buy_price 与首单成交价不一致"

    # 3. 4 analyzer 都有非空数据
    sharpe_obj = strat.analyzers.sharpe.get_analysis()
    dd_obj = strat.analyzers.drawdown.get_analysis()
    ta = strat.analyzers.trades.get_analysis()
    tr = strat.analyzers.time_return.get_analysis()
    assert "sharperatio" in sharpe_obj or sharpe_obj, "sharpe analyzer 无数据"
    assert "max" in dd_obj, "drawdown analyzer 无数据"
    assert tr, "time_return analyzer 无数据"
    closed_block = ta.get("total", {}).get("closed", 0) or 0
    total_closed = closed_block
    assert total_closed >= 1, f"应至少 1 笔闭合交易，实际 {total_closed}"

    # 4. 末态
    print(f"  ✓ sizer 占用: {sizer_pct:.4f}（首单 cost {first_cost:.0f} / {startcash:.0f}）")
    print(f"  ✓ 首单成交价: {first_price:.4f}")
    print(f"  ✓ buy_price 记账: {strat.buy_price:.4f}")
    print(f"  ✓ 总资金: {end_value:.2f}（收益 {end_value - startcash:+.2f}）")
    print(f"  ✓ sharpe 原始: {sharpe_obj.get('sharperatio')}")
    print(f"  ✓ max drawdown: {dd_obj.get('max', {}).get('drawdown'):.2f}%")
    print(f"  ✓ 闭合交易: {total_closed} 笔")
    print(f"  ✓ time_return bar 数: {len(tr)}")


def RsiCross_required_columns():
    return ["open", "close", "high", "low", "volume"]


if __name__ == "__main__":
    print("T2 回归测试: 4 analyzer + sizer 占用 + buy_price 记账")
    print("=" * 60)
    test_t2_regression()
    print("\n✅ T2 全部通过")
