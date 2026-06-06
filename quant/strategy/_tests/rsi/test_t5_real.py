"""
T5 真实数据回测：600519 贵州茅台 2020-2024

运行方式（从仓库根）:
    python quant/strategy/_tests/rsi/test_t5_real.py
"""
import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_ROOT))

from datetime import datetime
from quant.strategy.rsi.RsiStrategyScript import strategy_back_trader
from quant.strategy.rsi.strategy.RsiCross import RsiCross
from quant.strategy.rsi.strategy.RsiCrossEnhanced import RsiCrossEnhanced

print("=" * 60)
print("T5.1 RsiCross 600519 茅台 2020-2024")
print("=" * 60)
m1 = strategy_back_trader(
    symbol="600519", stock_name="贵州茅台",
    fromdate=datetime(2020, 1, 1), todate=datetime(2024, 12, 31),
    startcash=100_000, commission=0.0005,
    strategy=RsiCross,
    is_save_result=True, is_plot=False,
)
print()

print("=" * 60)
print("T5.2 RsiCrossEnhanced 600519 茅台 2020-2024")
print("=" * 60)
m2 = strategy_back_trader(
    symbol="600519", stock_name="贵州茅台",
    fromdate=datetime(2020, 1, 1), todate=datetime(2024, 12, 31),
    startcash=100_000, commission=0.0005,
    strategy=RsiCrossEnhanced,
    is_save_result=True, is_plot=False,
)
print()

print("=" * 60)
print("对比总结")
print("=" * 60)
print(f"  RsiCross:        收益 {m1['returns_pct']:>6.2f}%  夏普 {m1['sharpe_ratio']}  回撤 {m1['max_drawdown']}  胜率 {m1['win_rate']:.1f}%  交易 {m1['total_trades']}")
print(f"  RsiCrossEnhanced: 收益 {m2['returns_pct']:>6.2f}%  夏普 {m2['sharpe_ratio']}  回撤 {m2['max_drawdown']}  胜率 {m2['win_rate']:.1f}%  交易 {m2['total_trades']}")
