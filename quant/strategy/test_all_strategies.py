#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2026/5/15
Desc: Strategy模块综合测试脚本
测试所有策略的功能和回测效果
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from datetime import datetime
import pandas as pd
import quant.utils.db_orm as db_orm
from quant.entity.StockHistoryDailyInfoEntity import StockHistoryDailyInfoEntity
from quant.strategy.sma.strategy.SmaCross import SmaCross
from quant.strategy.boll.BollStrategy import BollStrategy
from quant.strategy.rsi.RSIStrategy import RSIStrategy


def test_get_stock_data(symbol="601398", adjust="qfq"):
    """测试获取股票数据"""
    print("\n" + "="*70)
    print("测试1: 获取股票数据")
    print("="*70)
    
    try:
        df = db_orm.get_mysql_data_to_df(
            orm_class=StockHistoryDailyInfoEntity, 
            adjust=adjust, 
            symbol=symbol
        )
        
        if df.empty:
            print(f"❌ 数据库中没有股票 {symbol} 的数据")
            return None
        
        print(f"✅ 成功获取股票 {symbol} 数据")
        print(f"   数据条数: {len(df)}")
        print(f"   日期范围: {df['date'].min()} 至 {df['date'].max()}")
        print(f"   列名: {list(df.columns)}")
        print(f"\n前5条数据:")
        print(df.head())
        
        return df
        
    except Exception as e:
        print(f"❌ 获取数据失败: {e}")
        return None


def test_sma_strategy(symbol="601398", adjust="qfq"):
    """测试SMA双均线策略"""
    print("\n" + "="*70)
    print("测试2: SMA双均线交叉策略")
    print("="*70)
    
    try:
        from quant.strategy.sma.SmaStrategyScript import strategy_back_trader
        
        print(f"📊 股票代码: {symbol}")
        print(f"📈 策略名称: {SmaCross.strategy_name}")
        print(f"⚙️  参数: pfast=5, pslow=20, stop_loss=5%, take_profit=10%")
        
        # 执行回测
        strategy_back_trader(
            symbol=symbol,
            stock_name="测试股票",
            adjust=adjust,
            fromdate=datetime(2024, 1, 1),
            todate=datetime.now(),
            startcash=100000,
            commission=0.0005,
            strategy=SmaCross,
            printlog=False,
            is_plot=False,
            is_save_result=False  # 测试时不保存结果
        )
        
        print("✅ SMA策略回测完成")
        return True
        
    except Exception as e:
        print(f"❌ SMA策略测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_boll_strategy(symbol="601398", adjust="qfq"):
    """测试布林线策略"""
    print("\n" + "="*70)
    print("测试3: 布林线交易策略")
    print("="*70)
    
    try:
        import backtrader as bt
        import akshare as ak
        
        # 获取数据
        try:
            df = db_orm.get_mysql_data_to_df(
                orm_class=StockHistoryDailyInfoEntity, 
                adjust=adjust, 
                symbol=symbol
            )
            df = df.iloc[:, 2:8]
        except:
            df = ak.stock_zh_a_hist_orm(symbol=symbol, adjust=adjust)
            df = df.iloc[:, :6]
        
        # 处理字段
        df.columns = ['date', 'open', 'close', 'high', 'low', 'volume']
        df.index = pd.to_datetime(df['date'])
        
        print(f"📊 股票代码: {symbol}")
        print(f"📈 策略名称: {BollStrategy.strategy_name}")
        print(f"⚙️  参数: size=1800, period=20")
        
        # 创建回测系统
        cerebro = bt.Cerebro()
        data = bt.feeds.PandasData(
            dataname=df, 
            fromdate=datetime(2024, 1, 1), 
            todate=datetime.now()
        )
        cerebro.adddata(data)
        cerebro.addstrategy(BollStrategy)
        cerebro.broker.setcash(100000)
        cerebro.broker.setcommission(commission=0.001)
        
        startcash = cerebro.broker.getvalue()
        cerebro.run()
        endcash = cerebro.broker.getvalue()
        
        pnl = endcash - startcash
        returns_pct = (pnl / startcash) * 100
        
        print(f"\n💰 初始资金: {startcash:.2f}")
        print(f"💰 最终资金: {endcash:.2f}")
        print(f"📈 净收益: {pnl:.2f}")
        print(f"📊 收益率: {returns_pct:.2f}%")
        
        print("✅ 布林线策略回测完成")
        return True
        
    except Exception as e:
        print(f"❌ 布林线策略测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_rsi_strategy(symbol="600519", adjust="qfq"):
    """测试RSI策略"""
    print("\n" + "="*70)
    print("测试4: RSI相对强弱指标策略")
    print("="*70)
    
    try:
        import backtrader as bt
        import akshare as ak
        
        # 获取数据
        try:
            df = db_orm.get_mysql_data_to_df(
                orm_class=StockHistoryDailyInfoEntity, 
                adjust=adjust, 
                symbol=symbol
            )
            if len(df) == 0:
                raise Exception("没有数据")
            df = df.iloc[:, 2:8]
        except:
            df = ak.stock_zh_a_hist_orm(symbol=symbol, adjust=adjust)
            df = df.iloc[:, :6]
        
        # 处理字段
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        print(f"📊 股票代码: {symbol}")
        print(f"📈 策略名称: {RSIStrategy.strategy_name}")
        print(f"⚙️  参数: rsi_period=14, rsi_upper=70, rsi_lower=30")
        
        # 创建回测系统
        cerebro = bt.Cerebro()
        cerebro.addstrategy(RSIStrategy, printlog=False)
        
        data = bt.feeds.PandasData(
            dataname=df, 
            fromdate=datetime(2024, 1, 1), 
            todate=datetime.now()
        )
        cerebro.adddata(data)
        cerebro.broker.setcash(100000)
        cerebro.broker.setcommission(commission=0.001)
        cerebro.addsizer(bt.sizers.FixedSize, stake=100)
        
        startcash = cerebro.broker.getvalue()
        print(f"💰 初始资金: {startcash:.2f}")
        
        cerebro.run()
        
        endcash = cerebro.broker.getvalue()
        pnl = endcash - startcash
        returns_pct = (pnl / startcash) * 100
        
        print(f"💰 最终资金: {endcash:.2f}")
        print(f"📈 净收益: {pnl:.2f}")
        print(f"📊 收益率: {returns_pct:.2f}%")
        
        print("✅ RSI策略回测完成")
        return True
        
    except Exception as e:
        print(f"❌ RSI策略测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_all_strategies():
    """测试所有策略"""
    print("\n" + "="*70)
    print("🚀 Strategy模块综合测试")
    print("="*70)
    
    results = {}
    
    # 测试1: 数据获取
    df = test_get_stock_data(symbol="601398", adjust="qfq")
    results['数据获取'] = df is not None
    
    if df is None:
        print("\n⚠️  由于无法获取数据，跳过后续策略测试")
        return results
    
    # 测试2: SMA策略
    results['SMA策略'] = test_sma_strategy(symbol="601398", adjust="qfq")
    
    # 测试3: 布林线策略
    results['布林线策略'] = test_boll_strategy(symbol="601398", adjust="qfq")
    
    # 测试4: RSI策略
    results['RSI策略'] = test_rsi_strategy(symbol="600519", adjust="qfq")
    
    # 打印总结
    print("\n" + "="*70)
    print("📊 测试总结")
    print("="*70)
    
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:15s}: {status}")
    
    passed = sum(results.values())
    total = len(results)
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！")
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败，请检查错误信息")
    
    return results


if __name__ == '__main__':
    test_all_strategies()
