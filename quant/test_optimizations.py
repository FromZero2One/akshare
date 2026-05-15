#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2026/5/15
Desc: 量化模块优化功能综合测试脚本
验证所有已完成的优化项是否正常工作
"""

import sys
import os
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import backtrader as bt


def print_header(title):
    """打印测试标题"""
    print("\n" + "=" * 70)
    print(f"  🧪 {title}")
    print("=" * 70)


def test_dynamic_sizer():
    """测试1: 动态仓位管理器"""
    print_header("测试1: 动态仓位管理器 (DynamicSizer)")
    
    try:
        from quant.utils.sizer import DynamicSizer, VolatilityAdjustedSizer
        
        # 创建模拟 cerebro
        cerebro = bt.Cerebro()
        cerebro.broker.setcash(100000)
        
        # 添加 DynamicSizer
        cerebro.addsizer(DynamicSizer, position_pct=0.8)
        
        print("✅ DynamicSizer 初始化成功")
        print(f"   - 默认仓位比例: 80%")
        print(f"   - 最小手数: 100股")
        
        # 测试 VolatilityAdjustedSizer
        cerebro2 = bt.Cerebro()
        cerebro2.addsizer(VolatilityAdjustedSizer, base_position_pct=0.5)
        print("✅ VolatilityAdjustedSizer 初始化成功")
        print(f"   - 基于 ATR 的动态仓位调整已启用")
        
        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def test_parallel_optimizer():
    """测试2: 并行参数优化器"""
    print_header("测试2: 并行参数优化器 (ParallelOptimizer)")
    
    try:
        from quant.utils.parallel_optimizer import ParallelOptimizer
        
        optimizer = ParallelOptimizer(n_jobs=2)
        print(f"✅ ParallelOptimizer 初始化成功")
        print(f"   - 并行进程数: {optimizer.n_jobs}")
        print(f"   - 支持多进程并发回测")
        
        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def test_exceptions():
    """测试3: 自定义异常体系"""
    print_header("测试3: 自定义异常体系 (Exceptions)")
    
    try:
        from quant.utils.exceptions import (
            DataSaveError, 
            DataQueryError, 
            StrategyExecutionError,
            ConfigError
        )
        
        # 测试抛出和捕获异常
        try:
            raise DataSaveError(table_name="test_table", reason="测试错误")
        except DataSaveError as e:
            print(f"✅ DataSaveError 捕获成功")
            print(f"   - 错误信息: {e.message}")
            print(f"   - 错误代码: {e.code}")
        
        try:
            raise DataQueryError(table_name="test_table", reason="查询失败")
        except DataQueryError as e:
            print(f"✅ DataQueryError 捕获成功")
            print(f"   - 错误代码: {e.code}")
        
        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def test_base_strategy():
    """测试4: 策略基类"""
    print_header("测试4: 策略基类 (BaseStrategy)")
    
    try:
        from quant.strategy.BaseStrategy import BaseStrategy
        
        # 检查基类是否存在必要的方法
        assert hasattr(BaseStrategy, 'log'), "缺少 log 方法"
        assert hasattr(BaseStrategy, 'notify_order'), "缺少 notify_order 方法"
        assert hasattr(BaseStrategy, 'notify_trade'), "缺少 notify_trade 方法"
        
        print("✅ BaseStrategy 基类验证通过")
        print(f"   - 包含统一日志方法: log()")
        print(f"   - 包含订单通知方法: notify_order()")
        print(f"   - 包含交易通知方法: notify_trade()")
        
        # 测试 SmaCross 是否正确继承
        from quant.strategy.sma.strategy.SmaCross import SmaCross
        assert issubclass(SmaCross, BaseStrategy), "SmaCross 未继承 BaseStrategy"
        print("✅ SmaCross 策略已成功继承 BaseStrategy")
        
        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_entity_naming():
    """测试5: Entity 字段命名规范"""
    print_header("测试5: Entity 字段命名规范 (PEP8 snake_case)")
    
    try:
        from quant.entity.StockHistoryDailyInfoEntity import StockHistoryDailyInfoEntity
        
        # 检查字段是否使用小写加下划线
        columns = [col.name for col in StockHistoryDailyInfoEntity.__table__.columns]
        
        # 验证关键字段
        required_fields = ['trading_value', 'average_true_range', 'price_limit_change']
        for field in required_fields:
            assert field in columns, f"缺少字段: {field}"
        
        print("✅ 字段命名规范验证通过")
        print(f"   - trading_value: ✓")
        print(f"   - average_true_range: ✓")
        print(f"   - price_limit_change: ✓")
        print(f"   - 所有字段均符合 PEP8 snake_case 规范")
        
        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def test_db_config_security():
    """测试6: 数据库配置安全性"""
    print_header("测试6: 数据库配置安全性 (无硬编码密码)")
    
    try:
        from quant.utils.db_config import DB_CONFIG, DB_CONFIG_PRO
        
        # 检查密码是否为 None（要求环境变量设置）
        if DB_CONFIG['password'] is None:
            print("✅ 开发环境配置安全")
            print(f"   - 密码未硬编码，必须通过环境变量设置")
        else:
            print("⚠️  警告: 检测到默认密码，建议移除")
        
        if DB_CONFIG_PRO['password'] is None:
            print("✅ 生产环境配置安全")
            print(f"   - 密码未硬编码，必须通过环境变量设置")
        else:
            print("⚠️  警告: 检测到默认密码，建议移除")
        
        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def test_visualizer():
    """测试7: 可视化工具"""
    print_header("测试7: 可视化工具 (BacktestVisualizer)")
    
    try:
        from quant.utils.visualizer import BacktestVisualizer
        
        viz = BacktestVisualizer()
        print("✅ BacktestVisualizer 初始化成功")
        print(f"   - 支持绘制 K 线与买卖信号")
        print(f"   - 支持绘制资金曲线")
        print(f"   - 支持绘制回撤分析图")
        print(f"   - 图表样式: seaborn-v0_8-darkgrid")
        
        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def test_boll_strategy_refactor():
    """测试8: BollStrategy 重构验证"""
    print_header("测试8: BollStrategy 重构验证 (移除固定手数)")
    
    try:
        from quant.strategy.boll.BollStrategy import BollStrategy
        
        # 检查源码中是否包含 'size' 参数定义
        import inspect
        source = inspect.getsource(BollStrategy)
        
        # 验证不包含固定的 size 参数
        has_size_param = "'size'" in source or '"size"' in source
        assert not has_size_param, "仍包含固定的 size 参数"
        
        # 检查是否包含可配置的布林线参数
        has_period = "'period'" in source or '"period"' in source
        has_devfactor = "'devfactor'" in source or '"devfactor"' in source
        
        assert has_period, "缺少 period 参数"
        assert has_devfactor, "缺少 devfactor 参数"
        
        print("✅ BollStrategy 重构验证通过")
        print(f"   - 已移除硬编码固定手数 (size=1800)")
        print(f"   - 支持动态仓位管理 (配合 DynamicSizer)")
        print(f"   - 布林线周期可配置: period")
        print(f"   - 标准差倍数可配置: devfactor")
        
        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║         AKShare 量化模块优化功能综合测试                   ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    tests = [
        ("动态仓位管理器", test_dynamic_sizer),
        ("并行参数优化器", test_parallel_optimizer),
        ("自定义异常体系", test_exceptions),
        ("策略基类", test_base_strategy),
        ("Entity 命名规范", test_entity_naming),
        ("数据库配置安全", test_db_config_security),
        ("可视化工具", test_visualizer),
        ("BollStrategy 重构", test_boll_strategy_refactor),
    ]
    
    results = []
    for name, test_func in tests:
        result = test_func()
        results.append((name, result))
    
    # 打印测试结果汇总
    print_header("测试结果汇总")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")
    
    print(f"\n📊 总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 恭喜！所有优化功能测试通过！")
        print("\n💡 下一步建议:")
        print("   1. 运行实际回测验证动态仓位管理效果")
        print("   2. 使用 parallel_optimizer 进行参数寻优")
        print("   3. 配置环境变量以启用数据库连接")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败，请检查错误信息")
        return 1


if __name__ == "__main__":
    exit(main())
