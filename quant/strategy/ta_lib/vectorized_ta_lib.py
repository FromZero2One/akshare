#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2026/5/30
Desc: RSI + MACD 组合策略向量化回测（替代 Backtrader 事件循环）

策略逻辑（与 TaLibStrategy 一致）：
  - 买入：RSI < rsi_lower（超卖）AND MACD 上穿信号线（金叉）
  - 卖出：RSI > rsi_upper（超买）AND MACD 下穿信号线（死叉）
  - 仓位：position_size 比例资金
"""

from datetime import datetime

import pandas as pd

from quant.utils.backtest_result_store import append_result, build_result_dict


def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """
    Wilder's RSI 计算（与 Backtrader 的 bt.indicators.RSI 一致）。
    """
    delta = series.diff()
    gain = delta.clip(lower=0).fillna(0)
    loss = (-delta).clip(lower=0).fillna(0)

    avg_gain = gain.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()

    rs = avg_gain / avg_loss.replace(0, float("nan"))
    rsi = 100 - (100 / (1 + rs))
    return rsi


def compute_macd(
    series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
) -> tuple:
    """
    MACD 计算（与 Backtrader 的 bt.indicators.MACD 一致）。

    Returns:
        (macd_line, signal_line, histogram)
    """
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def run_vectorized_backtest(
    df: pd.DataFrame,
    symbol: str,
    stock_name: str = "",
    fromdate: datetime = datetime(2020, 1, 1),
    todate: datetime = None,
    start_cash: float = 100000,
    commission: float = 0.0005,
    rsi_period: int = 14,
    macd_fast: int = 12,
    macd_slow: int = 26,
    macd_signal: int = 9,
    rsi_upper: float = 70,
    rsi_lower: float = 30,
    position_size: float = 0.8,
    printlog: bool = False,
    is_save_result: bool = True,
) -> dict:
    """
    向量化 RSI + MACD 组合回测（纯 pandas，无 Backtrader 依赖）

    与 TaLibStrategy 行为一致：
      - 买入：RSI < rsi_lower AND MACD 金叉
      - 卖出：RSI > rsi_upper AND MACD 死叉

    Args:
        df: 日线数据，需包含 date、close 列
        symbol: 股票代码
        stock_name: 股票名称
        fromdate: 回测起始日期（默认 2020-01-01）
        todate: 回测截止日期（默认今天）
        start_cash: 初始资金
        commission: 手续费比例
        rsi_period: RSI 计算周期
        macd_fast: MACD 快线周期
        macd_slow: MACD 慢线周期
        macd_signal: MACD 信号线周期
        rsi_upper: 超买阈值
        rsi_lower: 超卖阈值
        position_size: 每次买入使用的资金比例
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
    # 1. 向量化指标计算（使用完整数据）
    # ============================================================
    rsi = compute_rsi(df["close"], rsi_period)
    macd_line, signal_line, _ = compute_macd(
        df["close"], macd_fast, macd_slow, macd_signal
    )

    # ============================================================
    # 2. 买入 / 卖出信号（完整数据上计算，确保 shift(1) 正确）
    # ============================================================
    # MACD 金叉：前一日 macd <= signal，今日 macd > signal
    macd_golden = (macd_line > signal_line) & (
        macd_line.shift(1) <= signal_line.shift(1)
    )
    # MACD 死叉：前一日 macd >= signal，今日 macd < signal
    macd_death = (macd_line < signal_line) & (
        macd_line.shift(1) >= signal_line.shift(1)
    )

    # 买入：RSI 低于下限 AND MACD 金叉
    buy_signal = (rsi < rsi_lower) & macd_golden
    # 卖出：RSI 高于上限 AND MACD 死叉
    sell_signal = (rsi > rsi_upper) & macd_death

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
                shares = int(cash * position_size / price)
                cost = shares * price * (1 + commission)
                cash -= cost
                if printlog:
                    print(f'{df.loc[i, "date"]} BUY, Price: {price:.2f} (RSI+MACD金叉)')
        else:
            if sell_signal.iloc[i]:
                price = df.loc[i, "close"]
                revenue = shares * price * (1 - commission)
                cash += revenue
                if printlog:
                    print(f'{df.loc[i, "date"]} SELL, Price: {price:.2f} (RSI+MACD死叉)')
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
    print(f"策略名: RSI+MACD (向量化)")
    print(f"股票代码: {symbol}")
    print(f"初始资金: {round(start_cash, 2)}")
    print(f"总资金: {round(final_value, 2)}")
    print(f"净收益: {round(net_profit, 2)}")
    print(f"收益率: {round(returns_pct, 2)}%")

    if is_save_result:
        result_data = build_result_dict(
            symbol=symbol,
            stock_name=stock_name,
            strategy_name="RSI+MACD 组合策略",
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
