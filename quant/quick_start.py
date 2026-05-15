#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2025/1/15
Desc: 量化模块快速启动和验证脚本
一键验证所有优化是否正常工作
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def print_header(title):
    """打印标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_success(message):
    """打印成功信息"""
    print(f"✅ {message}")


def print_error(message):
    """打印错误信息"""
    print(f"❌ {message}")


def print_info(message):
    """打印普通信息"""
    print(f"ℹ️  {message}")


def check_dependencies():
    """检查依赖包"""
    print_header("步骤1: 检查依赖包")
    
    required_packages = [
        'sqlalchemy',
        'pandas',
        'pymysql',
    ]
    
    optional_packages = [
        'backtrader',
        'dotenv',
    ]
    
    all_ok = True
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print_success(f"{package} 已安装")
        except ImportError:
            print_error(f"{package} 未安装")
            all_ok = False
    
    print_info("\n可选包:")
    for package in optional_packages:
        try:
            __import__(package.replace('-', '_'))
            print_success(f"{package} 已安装")
        except ImportError:
            print_info(f"{package} 未安装（可选）")
    
    return all_ok


def test_logger():
    """测试日志系统"""
    print_header("步骤2: 测试日志系统")
    
    try:
        from quant.utils.logger_config import get_quant_logger
        
        logger = get_quant_logger()
        logger.info("日志系统工作正常")
        
        print_success("日志系统初始化成功")
        print_info("日志文件位置: quant/logs/quant.log")
        return True
    except Exception as e:
        print_error(f"日志系统测试失败: {e}")
        return False


def test_db_connection():
    """测试数据库连接"""
    print_header("步骤3: 测试数据库连接管理器")
    
    try:
        from quant.utils.db_connection import get_engine, db_manager
        
        engine = get_engine()
        
        # 测试单例
        engine2 = get_engine()
        assert engine is engine2, "引擎应该是同一个实例"
        
        print_success("数据库连接管理器初始化成功")
        print_info(f"引擎类型: {type(engine).__name__}")
        print_info(f"连接池大小: {engine.pool.size()}")
        return True
    except Exception as e:
        print_error(f"数据库连接测试失败: {e}")
        return False


def test_cache():
    """测试缓存系统"""
    print_header("步骤4: 测试缓存系统")
    
    try:
        from quant.utils.cache import query_cache, cache_result
        
        # 测试基本缓存
        query_cache.set("test_key", "test_value", ttl=60)
        value = query_cache.get("test_key")
        
        assert value == "test_value", "缓存值不匹配"
        
        # 测试统计
        stats = query_cache.stats()
        
        print_success("缓存系统工作正常")
        print_info(f"缓存大小: {stats['size']}/{stats['max_size']}")
        print_info(f"使用率: {stats['utilization']:.1f}%")
        return True
    except Exception as e:
        print_error(f"缓存系统测试失败: {e}")
        return False


def test_performance_monitor():
    """测试性能监控"""
    print_header("步骤5: 测试性能监控")
    
    try:
        from quant.utils.performance_monitor import Timer
        
        with Timer("测试操作"):
            import time
            time.sleep(0.1)
        
        print_success("性能监控系统工作正常")
        return True
    except Exception as e:
        print_error(f"性能监控测试失败: {e}")
        return False


def test_entities():
    """测试Entity类"""
    print_header("步骤6: 测试Entity类")
    
    try:
        from quant.entity.StockNameEntity import StockNameEntity
        from quant.entity.StockValueEntity import StockValueEntity
        from quant.entity.StockHistoryDailyInfoEntity import StockHistoryDailyInfoEntity
        
        # 测试StockNameEntity
        entity = StockNameEntity()
        entity.symbol = "601398"
        repr_str = repr(entity)
        assert "symbol='601398'" in repr_str
        
        print_success("所有Entity类工作正常")
        print_info(f"StockNameEntity示例: {repr_str[:50]}...")
        return True
    except Exception as e:
        print_error(f"Entity类测试失败: {e}")
        return False


def show_summary():
    """显示总结"""
    print_header("优化验证完成")
    
    print("""
🎉 恭喜！量化模块优化验证完成！

📚 下一步建议:

1. 查看使用指南:
   - quant/USAGE_GUIDE.md

2. 运行性能示例:
   - python quant/examples/performance_example.py

3. 查看详细优化记录:
   - quant/OPTIMIZATION_RECORD.md

4. 开始使用:
   ```python
   from quant.utils.db_orm import save_to_mysql_orm, get_mysql_data_to_df
   from quant.entity.StockHistoryDailyInfoEntity import StockHistoryDailyInfoEntity
   
   # 保存数据
   save_to_mysql_orm(df=data, orm_class=StockHistoryDailyInfoEntity)
   
   # 查询数据
   data = get_mysql_data_to_df(orm_class=StockHistoryDailyInfoEntity, symbol="601398")
   ```

✨ 主要特性:
   ✅ 智能数据库连接管理（单例+连接池）
   ✅ 专业日志系统（控制台+文件）
   ✅ 性能监控（装饰器+计时器）
   ✅ LRU缓存机制（自动过期）
   ✅ 完整的数据验证
   ✅ 环境变量配置支持

⚠️  注意事项:
   - 首次使用请安装依赖: pip install sqlalchemy pandas pymysql backtrader
   - 建议配置环境变量: cp .env.example .env
   - 日志文件位置: quant/logs/quant.log
    """)


def main():
    """主函数"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║         AKShare 量化模块优化验证工具 v2.0                 ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    results = []
    
    # 执行各项测试
    results.append(("依赖检查", check_dependencies()))
    results.append(("日志系统", test_logger()))
    results.append(("数据库连接", test_db_connection()))
    results.append(("缓存系统", test_cache()))
    results.append(("性能监控", test_performance_monitor()))
    results.append(("Entity类", test_entities()))
    
    # 显示结果汇总
    print_header("测试结果汇总")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        show_summary()
        return 0
    else:
        print_error(f"\n{total - passed} 个测试失败，请检查错误信息")
        print_info("建议: 查看 REQUIREMENTS.md 安装缺失的依赖")
        return 1


if __name__ == "__main__":
    exit(main())
