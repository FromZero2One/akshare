# BOLL 布林线指标

## 1. 计算逻辑

**布林带（Bollinger Bands）** 由 John Bollinger 在 1980 年代提出，由三条线组成：

1. **中轨**：`MID = SMA(period)`（默认 20 日均线）
2. **上轨**：`TOP = MID + devfactor * STD(period)`（默认 2 倍标准差）
3. **下轨**：`BOT = MID - devfactor * STD(period)`

`STD` 用 `ddof=0`（总体标准差，与 backtrader `BollingerBands` 默认一致）。

## 2. 策略实现

本模块提供事件循环策略（Backtrader）：

| 类 | 路径 | 触发逻辑 | 适用场景 |
|---|---|---|---|
| `BollCross` | `boll/strategy/BollCross.py` | 跌破下轨买入；突破上轨卖出 | 震荡市 / 反转捕捉 |

继承 `BaseStrategy`，仓位管理**统一交给 `DynamicSizer`**，next() 中不传 size。

## 3. 执行入口

```python
from quant.strategy.boll import strategy_back_trader, BollCross

# 默认 BollCross + 601398 工行
strategy_back_trader()

# 自定义参数（透传到策略 params，同时写入 params_json 落库）
strategy_back_trader(
    strategy=BollCross,
    period=20,
    devfactor=2.0,
)

# 自定义股票 / 资金 / 滑点
strategy_back_trader(
    symbol="000001",
    startcash=200000,
    enable_slippage=True,
    slippage_perc=0.002,
)
```

CLI 入口：
```bash
PYTHONPATH=/home/wsm/codes/akshare python quant/strategy/boll/BollStrategyScript.py
```

## 4. 推荐参数

| 参数 | 默认 | 建议范围 | 说明 |
|---|---|---|---|
| `period` | 20 | 10-30 | 布林线周期，越短越敏感 |
| `devfactor` | 2.0 | 1.5-2.5 | 标准差倍数，越小越敏感 |

## 5. 向量化版本

`vectorized_boll.py` 是**纯 pandas 实现的快速回测**：
- 速度：每只股票 ~5ms（vs Backtrader ~3s，**600x 提升**）
- 用途：5000 只股票全量扫描找候选
- 限制：无订单簿细节、无滑点/印花税精度、止盈/止损需手动实现
- 与事件循环版行为对齐（默认参数下 BollCross 逻辑一致）

使用：
```python
from quant.strategy.boll.vectorized_boll import run_vectorized_backtest
run_vectorized_backtest(df, symbol="601398", stock_name="工商银行")
```

## 6. 注意事项

- 布林带在强趋势中**会持续被突破/跌破**，单独使用易接刀
- 布林带宽度（TOP-BOT）反映波动率，窄带变宽带常预示大行情
- 落库需 `backtest_result_entity` 表有 `params_json` 列；首次运行 `BollStrategyScript` 会自动 `ALTER TABLE`（幂等）
- 与 SMA / RSI 模块共用同一套 `BaseStrategy` / `DynamicSizer` / `params_json` 落库
