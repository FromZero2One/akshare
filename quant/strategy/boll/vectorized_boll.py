#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2026/5/30 (Rev: 2026/6/6)
Desc: Bollinger Bands 策略向量化回测（替代 Backtrader 事件循环）

相比 Backtrader 版本（BollStrategyScript）：
  - 每只股票从 ~3s 降到 ~5ms（**600x 提升**）
  - 5000 只全量从 ~4h 降到 ~30s
  - 用途：**大批量初筛**找候选股，最终决策仍用事件循环版精确回测

策略逻辑（与 BollCross 一致）：
  - 买入：收盘价跌破下轨 (SMA - devfactor * std)
  - 卖出：收盘价突破上轨 (SMA + devfactor * std)
  - 仓位：position_pct 比例资金（**与 DynamicSizer.position_pct 命名对齐**）

⚠️ 与事件循环版的结果差异（已知）：
  - 向量化版**无订单簿**：按 close 价瞬时成交，无撮合延迟
  - 向量化版**无滑点/印花税精度**：仅扣 commission 比例
  - 向量化版**无止盈/止损**：本函数不实现 stop_loss/take_profit 逻辑
  - 向量化版**整百股**：`int(cash * position_pct / price)`，A 股最小 100 股约束未强校
  - 因此在 **T+1 撮合 / 资金冻结 / 止盈止损** 等场景下，结果可能与事件循环版不同

注意：本文件形参 `position_pct` 与 quant/utils/sizer.py 的 `DynamicSizer.position_pct` 命名一致；
quant/strategy/ta_lib/vectorized_ta_lib.py 仍沿用旧名 `position_size`，未统一（不在本轮范围）。
"""

from datetime import datetime

import pandas as pd

from quant.utils.backtest_result_store import append_result, build_result_dict


def run_vectorized_backtest(
    df: pd.DataFrame,
    symbol: str,
    stock_name: str = "",
    fromdate: datetime = datetime(2020, 1, 1),
    todate: datetime = None,
    start_cash: float = 100000,
    commission: float = 0.0005,
    period: int = 20,
    devfactor: float = 2.0,
    position_pct: float = 0.8,
    printlog: bool = False,
    is_save_result: bool = True,
) -> dict:
    """
    向量化 Bollinger Bands 回测（纯 pandas，无 Backtrader 依赖）

    与 BollCross 行为一致：
      - 买入：收盘价 <= 下轨
      - 卖出：收盘价 >= 上轨

    Args:
        df: 日线数据，需包含 date、close 列
        symbol: 股票代码
        stock_name: 股票名称
        fromdate: 回测起始日期（默认 2020-01-01）
        todate: 回测截止日期（默认今天）
        start_cash: 初始资金
        commission: 手续费比例
        period: 布林线周期
        devfactor: 标准差倍数
        position_pct: 每次买入使用的资金比例（与 DynamicSizer.position_pct 命名一致）
        printlog: 是否打印交易日志
        is_save_result: 是否保存回测结果

    Returns:
        包含回测结果的 dict，失败返回 None
    """
    if todate is None:
        todate = datetime.now()

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])

    # ============================================================
    # 1. 向量化布林带计算（使用完整数据，包括 fromdate 之前的数据）
    # ============================================================
    sma = df["close"].rolling(period).mean()
    std = df["close"].rolling(period).std(ddof=0)
    upper = sma + devfactor * std
    lower = sma - devfactor * std

    # ============================================================
    # 2. 买入 / 卖出信号（同样在完整数据上计算）
    # ============================================================
    buy_signal = df["close"] <= lower
    sell_signal = df["close"] >= upper

    # ============================================================
    # 3. 过滤日期范围
    # ============================================================
    mask = (df["date"] >= fromdate) & (df["date"] <= todate)
    df = df[mask].reset_index(drop=True)
    buy_signal = buy_signal[mask].reset_index(drop=True)
    sell_signal = sell_signal[mask].reset_index(drop=True)

    if len(df) < 1:
        return None

    # ============================================================
    # 4. 快速模拟持仓
    # ============================================================
    cash = start_cash
    shares = 0

    for i in range(len(df)):
        if shares == 0:
            if buy_signal.iloc[i]:
                price = df.loc[i, "close"]
                shares = int(cash * position_pct / price)
                cost = shares * price * (1 + commission)
                cash -= cost
                if printlog:
                    print(f'{df.loc[i, "date"]} BUY, Price: {price:.2f} (跌破下轨)')
        else:
            if sell_signal.iloc[i]:
                price = df.loc[i, "close"]
                revenue = shares * price * (1 - commission)
                cash += revenue
                if printlog:
                    print(f'{df.loc[i, "date"]} SELL, Price: {price:.2f} (突破上轨)')
                shares = 0

    if shares > 0:
        final_price = df.loc[len(df) - 1, "close"]
        cash += shares * final_price * (1 - commission)
        shares = 0

    # ============================================================
    # 5. 计算收益
    # ============================================================
    final_value = cash
    net_profit = final_value - start_cash
    returns_pct = (net_profit / start_cash) * 100

    print("--------------------------------")
    print(f"策略名: Bollinger (向量化)")
    print(f"股票代码: {symbol}")
    print(f"初始资金: {round(start_cash, 2)}")
    print(f"总资金: {round(final_value, 2)}")
    print(f"净收益: {round(net_profit, 2)}")
    print(f"收益率: {round(returns_pct, 2)}%")

    if is_save_result:
        result_data = build_result_dict(
            symbol=symbol,
            stock_name=stock_name,
            strategy_name="布林线交易策略(BollCross)",
            initial_cash=start_cash,
            final_value=final_value,
            net_profit=net_profit,
            returns=returns_pct,
            commission=commission,
            start_date=fromdate,
            end_date=todate,
        )
        append_result(result_data)

    return {
        "symbol": symbol,
        "stock_name": stock_name,
        "start_cash": start_cash,
        "final_value": final_value,
        "net_profit": net_profit,
        "returns_pct": returns_pct,
    }
