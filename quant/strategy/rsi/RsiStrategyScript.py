import json
from datetime import datetime
from typing import Type

import backtrader as bt
import pandas as pd

import quant.utils.db_orm as db_orm
from quant.data_fetch.stock_data_save_script import stock_zh_a_hist_orm_incremental
from quant.entity.StockHistoryDailyInfoEntity import StockHistoryDailyInfoEntity
from quant.strategy.rsi.strategy.RsiCross import RsiCross
from quant.utils.backtest_result_store import append_result, build_result_dict
from quant.utils.logger_config import get_quant_logger
from quant.utils.sizer import DynamicSizer
from quant.utils.visualizer import BacktestVisualizer

logger = get_quant_logger()

REQUIRED_COLUMNS = ['date', 'open', 'close', 'high', 'low', 'volume']

# 进程内缓存：params_json 列存在性只查一次 information_schema
_params_json_column_ensured = False


def _ensure_params_json_column():
    global _params_json_column_ensured
    if _params_json_column_ensured:
        return
    try:
        from quant.utils.backtest_result_store import ensure_params_json_column
        if ensure_params_json_column():
            _params_json_column_ensured = True
    except Exception as e:
        logger.warning(f"确保 params_json 列存在失败（写入可能报错）: {e}")


def _load_data(symbol: str, adjust: str, tb_df: pd.DataFrame | None) -> pd.DataFrame:
    """
    加载回测数据。优先用调用方传入的 tb_df；否则查 DB，DB 为空时走智能增量。
    返回的 DataFrame 索引为日期，且只含 REQUIRED_COLUMNS。
    """
    if tb_df is not None and not tb_df.empty:
        df = tb_df.copy()
    else:
        df = db_orm.get_mysql_data_to_df(orm_class=StockHistoryDailyInfoEntity, adjust=adjust, symbol=symbol)
        if df.empty:
            logger.info(f"DB 中无 {symbol}({adjust}) 数据，执行智能增量拉取")
            ok = stock_zh_a_hist_orm_incremental(symbol=symbol, adjust=adjust, isDel=False)
            if not ok:
                raise ValueError(f"无法从 akshare 拉取 {symbol} 数据")
            df = db_orm.get_mysql_data_to_df(orm_class=StockHistoryDailyInfoEntity, adjust=adjust, symbol=symbol)
            if df.empty:
                raise ValueError(f"增量拉取后仍无 {symbol} 数据")

    missing = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"输入数据缺少列: {missing}")
    out = df[REQUIRED_COLUMNS].copy()
    out.index = pd.to_datetime(out['date'])
    return out


def _build_cerebro(
        tb_df: pd.DataFrame, fromdate: datetime, todate: datetime,
        strategy: Type[bt.Strategy], startcash: float, commission: float,
        printlog: bool, *,
        sizer_cls: Type[bt.Sizer] = DynamicSizer, sizer_kwargs: dict | None = None,
        enable_slippage: bool = False, slippage_perc: float = 0.001,
        enable_stamp_duty: bool = False, stamp_duty: float = 0.001,
        strategy_params: dict | None = None,
) -> bt.Cerebro:
    """
    构建并配置 backtrader Cerebro。

    关键设计：
      - 默认不启用滑点/印花税（向后兼容）
      - 始终注册 4 个 analyzer：sharpe / drawdown / trades / time_return
      - sizer 默认为 DynamicSizer(position_pct=0.8)
    """
    data = bt.feeds.PandasData(dataname=tb_df, fromdate=fromdate, todate=todate)
    cerebro = bt.Cerebro()
    cerebro.adddata(data)
    addstrategy_kwargs = {"printlog": printlog, **(strategy_params or {})}
    cerebro.addstrategy(strategy, **addstrategy_kwargs)
    cerebro.addsizer(sizer_cls, **(sizer_kwargs or {"position_pct": 0.8}))

    cerebro.broker.setcommission(
        commission=commission,
        stocklike=True,
        percabs=True,
    )
    cerebro.broker.setcash(startcash)

    if enable_stamp_duty:
        logger.warning("enable_stamp_duty=True 当前未生效（A 股印花税需自定义 CommInfo，后续 P1 实现）")

    if enable_slippage:
        cerebro.broker.set_slippage_fixed(slippage_perc)

    cerebro.addobserver(bt.observers.Value)
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe', riskfreerate=0.0, annualize=True)
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='time_return')
    return cerebro


def _extract_metrics(strat, startcash: float, fromdate: datetime, todate: datetime) -> dict:
    end_value = strat.broker.getvalue()
    net_profit = end_value - startcash
    returns_pct = (net_profit / startcash) * 100

    sharpe_obj = strat.analyzers.sharpe.get_analysis()
    sharpe_raw = sharpe_obj.get('sharperatio')
    sharpe_ratio = float(sharpe_raw) if sharpe_raw is not None and sharpe_raw == sharpe_raw else None

    dd_obj = strat.analyzers.drawdown.get_analysis()
    max_drawdown = dd_obj.get('max', {}).get('drawdown')
    max_drawdown_len = dd_obj.get('max', {}).get('len')

    ta = strat.analyzers.trades.get_analysis()
    closed_block = ta.get('closed') or {}
    won_block = ta.get('won') or {}
    lost_block = ta.get('lost') or {}
    total_closed = closed_block.get('total', 0) or 0
    won = won_block.get('total', 0) or 0
    lost = lost_block.get('total', 0) or 0
    denom = total_closed if total_closed else (won + lost)
    win_rate = (won / denom * 100) if denom else 0.0

    return {
        'startcash': startcash,
        'end_value': end_value,
        'net_profit': net_profit,
        'returns_pct': returns_pct,
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': max_drawdown,
        'max_drawdown_len': max_drawdown_len,
        'total_trades': total_closed,
        'won': won,
        'lost': lost,
        'win_rate': win_rate,
        'fromdate': fromdate,
        'todate': todate,
    }


def _trade_summary_line(metrics: dict) -> str:
    total_closed = metrics['total_trades'] or 0
    won = metrics['won'] or 0
    lost = metrics['lost'] or 0
    actual_closed = total_closed if total_closed else (won + lost)
    if total_closed:
        return f'交易次数: {total_closed}  胜: {won}  负: {lost}'
    return f'交易次数(已闭合): {actual_closed}  胜: {won}  负: {lost}  [末期仍持仓]'


def _format_metrics_block(metrics: dict, symbol: str, strategy_name: str) -> str:
    def fmt_or_na(val, fmt):
        return fmt.format(val) if val is not None else 'N/A'

    lines = [
        '--------------------------------',
        f'策略名: {strategy_name}',
        f'股票代码: {symbol}',
        f'初始资金: {round(metrics["startcash"], 2)}',
        f'总资金: {round(metrics["end_value"], 2)}',
        f'净收益: {round(metrics["net_profit"], 2)}',
        f'收益率: {round(metrics["returns_pct"], 2)}%',
        f'夏普比率: {fmt_or_na(metrics["sharpe_ratio"], "{:.3f}")}',
        f'最大回撤: {fmt_or_na(metrics["max_drawdown"], "{:.2f}%")}',
        f'回撤持续(bar): {fmt_or_na(metrics["max_drawdown_len"], "{}")}',
        _trade_summary_line(metrics),
        f'胜率: {metrics["win_rate"]:.2f}%',
    ]
    return '\n'.join(lines)


def _dump_strategy_params(strategy_cls, **overrides) -> str | None:
    """
    把策略类（或实例）的 params 序列化为 JSON 字符串，overrides 覆盖默认值。
    backtrader 的 params 是元类生成的类，遍历其属性名提取默认值。
    """
    try:
        cls = strategy_cls if isinstance(strategy_cls, type) else type(strategy_cls)
        defaults = {
            name: getattr(cls.params, name)
            for name in dir(cls.params)
            if not name.startswith('_') and not callable(getattr(cls.params, name))
            and name not in ('isdefault', 'notdefault')
        }
    except Exception as e:
        logger.warning(f"提取策略参数默认值失败: {e}")
        defaults = {}
    merged = {**defaults, **overrides}
    try:
        return json.dumps(merged, ensure_ascii=False, default=str)
    except Exception as e:
        logger.warning(f"序列化策略参数失败: {e}")
        return None


def strategy_back_trader(symbol: str = "600519", stock_name: str = "", adjust: str = "qfq", tb_df: pd.DataFrame | None = None,
                         fromdate: datetime = datetime(2020, 1, 1), todate: datetime = datetime.now(),
                         startcash: float = 100000, commission: float = 0.0005,
                         strategy=RsiCross, printlog: bool = False,
                         is_plot: bool = False, is_save_result: bool = True,
                         *,
                         enable_slippage: bool = False, slippage_perc: float = 0.001,
                         enable_stamp_duty: bool = False, stamp_duty: float = 0.001,
                         sizer_cls: Type[bt.Sizer] = DynamicSizer, sizer_kwargs: dict | None = None,
                         **strategy_params):
    """
    symbol: 股票代码（默认 600519 贵州茅台）
    stock_name: 股票名称
    adjust: 复权方式 'qfq' 前复权 'hfq' 后复权 None 不复权
    tb_df: 数据框，如果为 None 则从数据库或 akshare 获取数据
    fromdate / todate: 回测起止日期
    startcash: 初始资金
    commission: 交易手续费 百分比 0.0005 = 0.05%
    strategy: 策略类引用（RsiCross 或 RsiCrossEnhanced），不接实例
    printlog: 是否打印策略内部日志
    is_plot: 是否绘图
    is_save_result: 是否落库到 BacktestResultEntity

    以下为 P0 之后新增（默认行为不变，向后兼容）：
    enable_slippage: 是否启用固定比例滑点
    slippage_perc: 滑点比例（默认 0.1%）
    enable_stamp_duty: 是否启用 A 股印花税（仅卖出收取）
    stamp_duty: 印花税比例（默认 0.1%）
    sizer_cls / sizer_kwargs: 自定义仓位管理器
    **strategy_params: 透传给策略的 params（如 rsi_period=14, rsi_lower=20）；同时写入 params_json 落库
    """
    if not isinstance(strategy, type):
        raise TypeError("strategy 必须传类引用（如 RsiCross），参数用 **strategy_params 传")
    tb_df = _load_data(symbol, adjust, tb_df)

    cerebro = _build_cerebro(
        tb_df, fromdate, todate, strategy, startcash, commission, printlog,
        sizer_cls=sizer_cls, sizer_kwargs=sizer_kwargs,
        enable_slippage=enable_slippage, slippage_perc=slippage_perc,
        enable_stamp_duty=enable_stamp_duty, stamp_duty=stamp_duty,
        strategy_params=strategy_params,
    )

    results = cerebro.run()
    strat = results[0]
    metrics = _extract_metrics(strat, startcash, fromdate, todate)

    text = _format_metrics_block(metrics, symbol, strategy.strategy_name)
    print(text)
    logger.debug(text)

    if is_plot:
        try:
            cerebro.plot(style='candlestick')
        except Exception as e:
            logger.warning(f"cerebro.plot 失败: {e}")

        try:
            viz = BacktestVisualizer()
            tr = strat.analyzers.time_return.get_analysis()
            if tr:
                ret_series = pd.Series(tr).sort_index()
                ret_series.index = pd.to_datetime(ret_series.index)
                portfolio_value = startcash * (1 + ret_series).cumprod()
            else:
                portfolio_value = pd.Series(dtype=float)
            trades = getattr(strat.broker, 'trades_history', []) or []
            viz.plot_strategy_performance(
                df_data=tb_df,
                trades=trades,
                portfolio_value=portfolio_value,
                title=f"{strategy.strategy_name} - {symbol}",
            )
        except Exception as e:
            print(f"⚠️ 自定义绘图失败: {e}")

    if is_save_result:
        _ensure_params_json_column()
        params_json = _dump_strategy_params(strategy, **strategy_params)
        result_data = build_result_dict(
            symbol=symbol, stock_name=stock_name, strategy_name=strategy.strategy_name,
            initial_cash=startcash, final_value=metrics['end_value'],
            net_profit=metrics['net_profit'], returns=metrics['returns_pct'],
            commission=commission,
            start_date=fromdate, end_date=todate,
            params_json=params_json,
        )
        append_result(result_data)

    return metrics


if __name__ == '__main__':
    """
    测试 RSI 策略（默认 RsiCross + 600519 茅台）
    """
    strategy_back_trader(strategy=RsiCross)
