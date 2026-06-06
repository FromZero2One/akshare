"""
T5 真实数据回测：601398 工商银行 2020-2024

运行方式（从仓库根）:
    python quant/strategy/_tests/boll/test_t5_real.py
"""
import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_ROOT))

from datetime import datetime
from quant.strategy.boll.BollStrategyScript import strategy_back_trader
from quant.strategy.boll.strategy.BollCross import BollCross

print("=" * 60)
print("BOLL T5.1 BollCross 601398 工行 2020-2024")
print("=" * 60)
m = strategy_back_trader(
    symbol="601398", stock_name="工商银行",
    fromdate=datetime(2020, 1, 1), todate=datetime(2024, 12, 31),
    startcash=100_000, commission=0.0005,
    strategy=BollCross,
    is_save_result=True, is_plot=False,
)
print()

print("=" * 60)
print("BOLL T5.2 BollCross 工行 自定义参数 (period=14, devfactor=1.5)")
print("=" * 60)
m2 = strategy_back_trader(
    symbol="601398", stock_name="工商银行",
    fromdate=datetime(2020, 1, 1), todate=datetime(2024, 12, 31),
    startcash=100_000, commission=0.0005,
    strategy=BollCross,
    is_save_result=True, is_plot=False,
    period=14, devfactor=1.5,
)
print()

print("=" * 60)
print("对比总结")
print("=" * 60)
print(f"  BollCross 默认参数:   收益 {m['returns_pct']:>6.2f}%  夏普 {m['sharpe_ratio']}  回撤 {m['max_drawdown']}  胜率 {m['win_rate']:.1f}%  交易 {m['total_trades']}")
print(f"  BollCross 紧带参数:   收益 {m2['returns_pct']:>6.2f}%  夏普 {m2['sharpe_ratio']}  回撤 {m2['max_drawdown']}  胜率 {m2['win_rate']:.1f}%  交易 {m2['total_trades']}")
