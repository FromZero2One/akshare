#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2025/1/15
Desc: 每日更新功能快速测试脚本
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from quant.entity.script.daily_stock_updater import DailyStockDataUpdater
from quant.utils.logger_config import get_quant_logger

logger = get_quant_logger()


def test_basic_functionality():
    """测试基本功能"""
    print("\n" + "=" * 70)
    print("🧪 测试1: 基本功能验证")
    print("=" * 70)
    
    # 创建更新器
    updater = DailyStockDataUpdater(
        adjust="qfq",
        max_workers=2,
        delay_between_requests=0.3,
        isDel=False
    )
    
    print("✅ 更新器创建成功")
    print(f"   - 复权类型: {updater.adjust}")
    print(f"   - 并发线程: {updater.max_workers}")
    print(f"   - 请求间隔: {updater.delay_between_requests}秒")
    
    return True


def test_get_symbols():
    """测试获取股票代码"""
    print("\n" + "=" * 70)
    print("🧪 测试2: 获取股票代码")
    print("=" * 70)
    
    updater = DailyStockDataUpdater()
    
    try:
        symbols = updater.get_all_stock_symbols()
        print(f"✅ 成功获取 {len(symbols)} 只股票代码")
        print(f"   - 示例: {symbols[:5]}")
        return True
    except Exception as e:
        print(f"❌ 获取股票代码失败: {e}")
        return False


def test_single_stock_update():
    """测试单只股票更新"""
    print("\n" + "=" * 70)
    print("🧪 测试3: 单只股票更新")
    print("=" * 70)
    
    updater = DailyStockDataUpdater(
        adjust="qfq",
        max_workers=1,
        delay_between_requests=0.3
    )
    
    # 测试工商银行
    test_symbol = "601398"
    
    try:
        result = updater.update_single_stock(test_symbol)
        print(f"✅ 股票 {test_symbol} 更新结果:")
        print(f"   - 状态: {result['status']}")
        print(f"   - 消息: {result['message']}")
        return result['status'] == 'success'
    except Exception as e:
        print(f"❌ 更新失败: {e}")
        return False


def test_batch_update():
    """测试批量更新（少量股票）"""
    print("\n" + "=" * 70)
    print("🧪 测试4: 批量更新（3只股票）")
    print("=" * 70)
    
    updater = DailyStockDataUpdater(
        adjust="qfq",
        max_workers=2,
        delay_between_requests=0.3
    )
    
    # 测试3只股票
    test_symbols = ["601398", "600036", "000001"]
    
    try:
        report = updater.update_stocks_batch(test_symbols)
        
        print(f"✅ 批量更新完成:")
        print(f"   - 总数: {report['total']}")
        print(f"   - 成功: {report['success']}")
        print(f"   - 失败: {report['failed']}")
        print(f"   - 耗时: {report['elapsed_time']:.2f}秒")
        print(f"   - 平均速度: {report['avg_time_per_stock']:.2f}秒/股")
        
        return report['failed'] == 0
    except Exception as e:
        print(f"❌ 批量更新失败: {e}")
        return False


def test_full_run():
    """测试完整运行流程（测试模式）"""
    print("\n" + "=" * 70)
    print("🧪 测试5: 完整运行流程（测试模式，5只股票）")
    print("=" * 70)
    
    updater = DailyStockDataUpdater(
        adjust="qfq",
        max_workers=2,
        delay_between_requests=0.3
    )
    
    try:
        updater.run(test_mode=True, test_count=5)
        print("✅ 完整流程测试通过")
        return True
    except Exception as e:
        print(f"❌ 完整流程测试失败: {e}")
        return False


def main():
    """运行所有测试"""
    print("\n" + "🧪" * 35)
    print("  每日股票数据增量更新 - 功能测试")
    print("🧪" * 35)
    
    tests = [
        ("基本功能", test_basic_functionality),
        ("获取股票代码", test_get_symbols),
        ("单只股票更新", test_single_stock_update),
        ("批量更新", test_batch_update),
        ("完整流程", test_full_run),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} 测试异常: {e}")
            results.append((test_name, False))
    
    # 汇总结果
    print("\n" + "=" * 70)
    print("📊 测试结果汇总")
    print("=" * 70)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {test_name}")
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！可以开始使用了。")
        print("\n💡 使用建议:")
        print("   1. 首次使用先运行测试模式:")
        print("      python quant/entity/script/daily_stock_updater.py --test")
        print("   2. 确认无误后运行全量更新:")
        print("      python quant/entity/script/daily_stock_updater.py")
        print("   3. 生产环境建议使用定时任务:")
        print("      python quant/entity/script/scheduler.py")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败，请检查错误信息")
        return 1


if __name__ == '__main__':
    sys.exit(main())
