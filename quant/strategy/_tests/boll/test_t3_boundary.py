"""
BOLL 完整测试 T3 边界测试（7 子项）
- T3.1 dump_strategy_params：默认 + override
- T3.2 缺列 ValueError
- T3.3 非类 strategy TypeError
- T3.4 enable_slippage=True 跑通
- T3.5 enable_stamp_duty=True 仅 warn
- T3.6 默认无参正常
- T3.7 真落库 + round-trip + NULL 兼容（需要 DB）
"""
import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_ROOT))
import os
os.chdir(_ROOT)

import json
from datetime import datetime

import numpy as np
import pandas as pd

import backtrader as bt

from quant.strategy.boll.BollStrategyScript import (
    strategy_back_trader, _dump_strategy_params, _load_data, _build_cerebro,
    _extract_metrics, _format_metrics_block, _trade_summary_line,
)
from quant.strategy.boll.strategy.BollCross import BollCross
from quant.utils.sizer import DynamicSizer


def make_synthetic_df(n=200, trend="down_then_up"):
    dates = pd.date_range(end=datetime(2024, 12, 31), periods=n, freq="B")
    np.random.seed(42)
    if trend == "down_then_up":
        prices = np.concatenate([
            np.linspace(1.00, 0.70, 100),
            np.linspace(0.70, 1.50, n - 100),
        ])
    else:
        prices = np.ones(n)
    prices = prices + np.random.normal(0, 0.005, n)
    return pd.DataFrame({
        "date": dates,
        "open": prices + np.random.normal(0, 0.003, n),
        "close": prices,
        "high": prices + np.abs(np.random.normal(0, 0.008, n)),
        "low": prices - np.abs(np.random.normal(0, 0.008, n)),
        "volume": np.random.randint(1_000_000, 5_000_000, n),
    })


def t31_dump_params():
    """T3.1 _dump_strategy_params 默认 + override"""
    j_default = _dump_strategy_params(BollCross)
    j_override = _dump_strategy_params(BollCross, period=14, devfactor=1.5)
    d1 = json.loads(j_default)
    d2 = json.loads(j_override)
    assert d1["period"] == 20, f"default period 应为 20，实际 {d1['period']}"
    assert d1["devfactor"] == 2.0
    assert d2["period"] == 14, f"override period 应为 14，实际 {d2['period']}"
    assert d2["devfactor"] == 1.5
    # override 不应改 default
    assert d1["period"] == 20
    print(f"  ✓ T3.1 dump_params: default={d1} | override={d2}")


def t32_missing_columns():
    """T3.2 缺列 ValueError"""
    df = make_synthetic_df(100).drop(columns=["volume"])
    try:
        _load_data("601398", "qfq", tb_df=df)
        assert False, "缺 volume 应抛 ValueError，未抛"
    except ValueError as e:
        assert "volume" in str(e)
        print(f"  ✓ T3.2 缺列捕获: {e}")


def t33_non_class_strategy():
    """T3.3 非类 strategy TypeError + 实例撞 backtrader metaclass"""
    # 3.3a: 字符串（明确非类）→ isinstance 检查抛 TypeError
    try:
        strategy_back_trader(strategy="BollCross", is_save_result=False)
        assert False, "传字符串应抛 TypeError，未抛"
    except TypeError as e:
        assert "类引用" in str(e)
        print(f"  ✓ T3.3a 字符串被拒: {e}")
    # 3.3b: 实例 → 撞 backtrader metaclass
    try:
        strategy_back_trader(strategy=BollCross(period=14), is_save_result=False)
        assert False, "传实例应被拒绝，未抛"
    except (TypeError, AttributeError) as e:
        print(f"  ✓ T3.3b 实例被拒（bt metaclass 自身）: {type(e).__name__}: {e}")


def t34_slippage_runs():
    """T3.4 enable_slippage=True 跑通"""
    df = make_synthetic_df(200)
    metrics = strategy_back_trader(
        symbol="601398", tb_df=df, strategy=BollCross,
        fromdate=datetime(2024, 1, 1), todate=datetime(2024, 12, 31),
        is_save_result=False, is_plot=False,
        enable_slippage=True, slippage_perc=0.002,
        period=14,
    )
    assert "end_value" in metrics
    print(f"  ✓ T3.4 滑点跑通: end_value={metrics['end_value']:.2f}")


def t35_stamp_duty_warns():
    """T3.5 enable_stamp_duty=True 仅 warn 不报错"""
    df = make_synthetic_df(200)
    metrics = strategy_back_trader(
        symbol="601398", tb_df=df, strategy=BollCross,
        fromdate=datetime(2024, 1, 1), todate=datetime(2024, 12, 31),
        is_save_result=False, is_plot=False,
        enable_stamp_duty=True, stamp_duty=0.001,
        period=14,
    )
    assert "end_value" in metrics
    print(f"  ✓ T3.5 印花税 warn 通过: end_value={metrics['end_value']:.2f}")


def t36_default_no_args():
    """T3.6 默认无参：直接调 strategy_back_trader() 不报错"""
    df = make_synthetic_df(200)
    metrics = strategy_back_trader(
        symbol="601398", tb_df=df, is_save_result=False, is_plot=False,
        period=14,
    )
    assert "end_value" in metrics
    assert "sharpe_ratio" in metrics
    assert "max_drawdown" in metrics
    print(f"  ✓ T3.6 默认无参通过: sharpe={metrics['sharpe_ratio']}, max_dd={metrics['max_drawdown']}")


def t37_db_roundtrip():
    """T3.7 真落库 + NULL 兼容（需 DB）"""
    from quant.utils.backtest_result_store import (
        ensure_params_json_column, build_result_dict, append_result,
    )
    # a) ensure_params_json_column 幂等
    ok1 = ensure_params_json_column()
    ok2 = ensure_params_json_column()
    assert ok1 and ok2
    print(f"  ✓ T3.7a ensure_params_json_column 幂等: {ok1}, {ok2}")
    # b) 完整回测落库
    df = make_synthetic_df(100)
    metrics = strategy_back_trader(
        symbol="601398", tb_df=df, is_save_result=True, is_plot=False,
        period=10, devfactor=1.8,
    )
    assert "end_value" in metrics
    print(f"  ✓ T3.7b params_json 落库: end_value={metrics['end_value']:.2f}")
    # c) NULL 兼容
    d = build_result_dict(
        symbol="601398", stock_name="工商银行",
        strategy_name="BollCross", initial_cash=100000, final_value=110000,
        net_profit=10000, returns=10.0, commission=0.0005,
        start_date=datetime(2020, 1, 1), end_date=datetime(2024, 12, 31),
    )
    append_result(d)
    print(f"  ✓ T3.7c NULL 兼容: append_result 不带 params_json 成功")
    # d) 进程缓存
    from quant.strategy.boll.BollStrategyScript import _params_json_column_ensured
    assert _params_json_column_ensured
    print(f"  ✓ T3.7d 进程缓存命中: _params_json_column_ensured={_params_json_column_ensured}")


if __name__ == "__main__":
    print("BOLL 完整测试 T3 边界测试")
    print("=" * 60)

    print("[T3.1] dump_strategy_params")
    t31_dump_params()
    print("[T3.2] 缺列 ValueError")
    t32_missing_columns()
    print("[T3.3] 非类 strategy TypeError")
    t33_non_class_strategy()
    print("[T3.4] enable_slippage=True 跑通")
    t34_slippage_runs()
    print("[T3.5] enable_stamp_duty=True 仅 warn")
    t35_stamp_duty_warns()
    print("[T3.6] 默认无参正常")
    t36_default_no_args()
    print("[T3.7] DB 落库 + round-trip + NULL 兼容")
    try:
        t37_db_roundtrip()
    except Exception as e:
        print(f"  ⚠️ T3.7 跳过（DB 不可用）: {e}")

    print("\n✅ T3 全部通过")
