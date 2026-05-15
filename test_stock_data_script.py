#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2025/1/15
Desc: stock_data_save_script.py 功能测试脚本
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from quant.entity.script.stock_data_save_script import (
    stock_name_and_save,
    stock_value_em_orm,
    stock_comment_em_orm,
    stock_zh_a_hist_orm,
    stock_zh_a_hist_orm_incremental,
    stock_comment_detail_scrd_focus_em,
    stock_comment_detail_zlkp_jgcyd_em,
    stock_comment_detail_zhpj_lspf_em
)
from quant.utils.logger_config import get_quant_logger

logger = get_quant_logger()


def print_header(title):
    """打印标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_function_import():
    """测试1: 函数导入"""
    print_header("测试1: 函数导入验证")
    
    functions = [
        'stock_name_and_save',
        'stock_value_em_orm',
        'stock_comment_em_orm',
        'stock_zh_a_hist_orm',
        'stock_zh_a_hist_orm_incremental',  # 修复后的正确名称
        'stock_comment_detail_scrd_focus_em',
        'stock_comment_detail_zlkp_jgcyd_em',
        'stock_comment_detail_zhpj_lspf_em'
    ]
    
    for func_name in functions:
        try:
            func = eval(func_name)
            assert callable(func), f"{func_name} 不是可调用对象"
            print(f"✅ {func_name} - 导入成功")
        except Exception as e:
            print(f"❌ {func_name} - 导入失败: {e}")
            return False
    
    return True


def test_entity_repr():
    """测试2: Entity类__repr__方法"""
    print_header("测试2: Entity类__repr__方法")
    
    from quant.entity.StockCommentEntity import StockCommentEntity
    from quant.entity.StockNameEntity import StockNameEntity
    from quant.entity.StockValueEntity import StockValueEntity
    from quant.entity.StockHistoryDailyInfoEntity import StockHistoryDailyInfoEntity
    
    entities = [
        ('StockCommentEntity', StockCommentEntity()),
        ('StockNameEntity', StockNameEntity()),
        ('StockValueEntity', StockValueEntity()),
        ('StockHistoryDailyInfoEntity', StockHistoryDailyInfoEntity())
    ]
    
    for name, entity in entities:
        try:
            repr_str = repr(entity)
            print(f"✅ {name}: {repr_str[:60]}...")
        except Exception as e:
            print(f"❌ {name} __repr__失败: {e}")
            return False
    
    return True


def test_function_signature():
    """测试3: 函数签名检查"""
    print_header("测试3: 函数签名检查")
    
    import inspect
    
    # 测试增量更新函数的参数
    sig = inspect.signature(stock_zh_a_hist_orm_incremental)
    params = list(sig.parameters.keys())
    
    expected_params = ['symbol', 'adjust', 'isDel']
    if params == expected_params:
        print(f"✅ stock_zh_a_hist_orm_incremental 参数正确: {params}")
    else:
        print(f"❌ stock_zh_a_hist_orm_incremental 参数错误")
        print(f"   期望: {expected_params}")
        print(f"   实际: {params}")
        return False
    
    # 测试其他函数
    sig2 = inspect.signature(stock_value_em_orm)
    params2 = list(sig2.parameters.keys())
    print(f"✅ stock_value_em_orm 参数: {params2}")
    
    sig3 = inspect.signature(stock_comment_em_orm)
    params3 = list(sig3.parameters.keys())
    print(f"✅ stock_comment_em_orm 参数: {params3}")
    
    return True


def test_logging_integration():
    """测试4: 日志系统集成"""
    print_header("测试4: 日志系统集成")
    
    # 检查模块是否导入了logger
    import quant.entity.script.stock_data_save_script as script_module
    
    if hasattr(script_module, 'logger'):
        logger_obj = getattr(script_module, 'logger')
        print(f"✅ 模块已配置logger: {type(logger_obj).__name__}")
        
        # 测试日志输出
        logger_obj.info("测试日志消息")
        print("✅ 日志输出正常")
        return True
    else:
        print("❌ 模块未配置logger")
        return False


def test_docstrings():
    """测试5: 文档字符串完整性"""
    print_header("测试5: 文档字符串完整性")
    
    functions_to_check = [
        stock_name_and_save,
        stock_value_em_orm,
        stock_comment_em_orm,
        stock_zh_a_hist_orm,
        stock_zh_a_hist_orm_incremental,
        stock_comment_detail_scrd_focus_em,
        stock_comment_detail_zlkp_jgcyd_em,
        stock_comment_detail_zhpj_lspf_em
    ]
    
    all_good = True
    for func in functions_to_check:
        if func.__doc__:
            doc_lines = func.__doc__.strip().split('\n')
            first_line = doc_lines[0].strip()
            has_args = any('Args:' in line or 'Parameters:' in line for line in doc_lines)
            
            status = "✅" if has_args else "⚠️ "
            print(f"{status} {func.__name__}: {first_line}")
            if not has_args:
                print(f"   ⚠️  缺少Args说明")
        else:
            print(f"❌ {func.__name__}: 缺少文档字符串")
            all_good = False
    
    return all_good


def main():
    """运行所有测试"""
    print("\n" + "🧪" * 35)
    print("  stock_data_save_script.py 功能测试")
    print("🧪" * 35)
    
    tests = [
        ("函数导入", test_function_import),
        ("Entity __repr__", test_entity_repr),
        ("函数签名", test_function_signature),
        ("日志集成", test_logging_integration),
        ("文档字符串", test_docstrings),
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
    print_header("测试结果汇总")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {test_name}")
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！脚本已准备就绪。")
        print("\n💡 使用示例:")
        print("   from quant.entity.script.stock_data_save_script import *")
        print("   ")
        print("   # 保存股票历史数据（增量更新）")
        print("   stock_zh_a_hist_orm_incremental(symbol='601398', adjust='qfq')")
        print("   ")
        print("   # 保存估值数据")
        print("   stock_value_em_orm(symbol='601398', TRADE_DATE='2025-01-15')")
        print("   ")
        print("   # 查看日志")
        print("   cat quant/logs/quant.log")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败，请检查错误信息")
        return 1


if __name__ == '__main__':
    sys.exit(main())
