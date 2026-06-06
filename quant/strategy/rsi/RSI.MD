# RSI 相对强弱指标

## 1. 计算逻辑

`RSI`（Relative Strength Index，相对强弱指数）由 J. Welles Wilder Jr. 在 1978 年开发的技术分析指标。

**基本计算步骤：**

1. **计算价格变化**：当前收盘价 - 前一收盘价，记为 Δ
2. **拆分涨跌**：`U = max(Δ, 0)`、`D = max(-Δ, 0)`
3. **平滑均值**（Wilder 平滑：α=1/period 的 EMA）：`AvgU = EMA(U)`、`AvgD = EMA(D)`
4. **相对强度**：`RS = AvgU / AvgD`
5. **RSI**：`RSI = 100 - 100 / (1 + RS)`

值域 [0, 100]：
- `RSI > 70` 超买，可能回调
- `RSI < 30` 超卖，可能反弹
- `RSI` 在 50 上下反映多空力量对比

## 2. 策略实现

本模块提供两个事件循环策略（Backtrader）：

| 类 | 路径 | 触发逻辑 | 适用场景 |
|---|---|---|---|
| `RsiCross` | `rsi/strategy/RsiCross.py` | RSI < rsi_lower 买入；RSI > rsi_upper 卖出 | 震荡市 / 反转捕捉 |
| `RsiCrossEnhanced` | `rsi/strategy/RsiCrossEnhanced.py` | 加 SMA(sma_period) 趋势过滤；超买 OR 跌破趋势均线 即卖出 | 趋势市过滤假信号 |

两个类都**继承 `BaseStrategy`**，仓位管理**统一交给 `DynamicSizer`**，next() 中不传 size。

## 3. 执行入口

```python
from quant.strategy.rsi import strategy_back_trader, RsiCross, RsiCrossEnhanced

# 默认 RsiCross + 600519 茅台
strategy_back_trader()

# 切换到优化版
strategy_back_trader(strategy=RsiCrossEnhanced)

# 自定义参数（透传到策略 params，同时写入 params_json 落库）
strategy_back_trader(
    strategy=RsiCross,
    rsi_period=14,
    rsi_upper=75,
    rsi_lower=25,
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
PYTHONPATH=/home/wsm/codes/akshare python quant/strategy/rsi/RsiStrategyScript.py
```

## 4. 推荐参数

| 参数 | 默认 | 建议范围 | 说明 |
|---|---|---|---|
| `rsi_period` | 10 | 6-21 | 周期越短越敏感，假信号越多 |
| `rsi_upper` | 70 (RsiCross) / 75 (Enhanced) | 65-80 | 强趋势市可放宽到 80 |
| `rsi_lower` | 30 (RsiCross) / 25 (Enhanced) | 20-35 | 强趋势市可放宽到 20 |
| `sma_period`（仅 Enhanced） | 20 | 10-60 | 趋势过滤均线周期 |

## 5. 向量化版本

`vectorized_rsi.py` 是**纯 pandas 实现的快速回测**：
- 速度：每只股票 ~5ms（vs Backtrader ~3s，**600x 提升**）
- 用途：5000 只股票全量扫描找候选
- 限制：无订单簿细节、无滑点/印花税精度、止盈/止损需手动实现
- 与事件循环版行为对齐（默认参数下 RsiCrossEnhanced 逻辑一致）

使用：
```python
from quant.strategy.rsi.vectorized_rsi import run_vectorized_backtest
run_vectorized_backtest(df, symbol="600519", stock_name="贵州茅台")
```

## 6. 注意事项

- RSI 在强趋势中可长时间停留在超买/超卖区，单独使用易接刀
- `RsiCrossEnhanced` 需 SMA 暖机期（默认 20 根 K 线），数据不足时不交易
- 落库需 `backtest_result_entity` 表有 `params_json` 列；首次运行 `RsiStrategyScript` 会自动 `ALTER TABLE`（幂等）
