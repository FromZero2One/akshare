#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2025/1/15
Desc: 数据库环境切换工具
用于在开发环境和生产环境之间快速切换
"""

import sys
import os

# 将项目根目录添加到Python路径中
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def switch_to_pro():
    """切换到生产环境"""
    config_file = "quant/utils/db_connection.py"
    
    print("=" * 70)
    print("🔄 切换到生产环境数据库")
    print("=" * 70)
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替换配置
        if 'use_pro=False' in content:
            content = content.replace('use_pro=False', 'use_pro=True')
            
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("✅ 已切换到生产环境数据库")
            print("   - 主机: 8.137.104.120")
            print("   - 端口: 3306")
            print("   - 数据库: akshare")
            print("\n⚠️  请重启Python进程以使更改生效")
        else:
            print("ℹ️  当前已是生产环境配置")
            
    except Exception as e:
        print(f"❌ 切换失败: {e}")
        return False
    
    return True


def switch_to_dev():
    """切换到开发环境"""
    config_file = "quant/utils/db_connection.py"
    
    print("=" * 70)
    print("🔄 切换到开发环境数据库")
    print("=" * 70)
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替换配置
        if 'use_pro=True' in content:
            content = content.replace('use_pro=True', 'use_pro=False')
            
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("✅ 已切换到开发环境数据库")
            print("   - 主机: localhost")
            print("   - 端口: 3306")
            print("   - 数据库: akshare")
            print("\n⚠️  请重启Python进程以使更改生效")
        else:
            print("ℹ️  当前已是开发环境配置")
            
    except Exception as e:
        print(f"❌ 切换失败: {e}")
        return False
    
    return True


def check_current_env():
    """检查当前环境"""
    config_file = "quant/utils/db_connection.py"
    
    print("=" * 70)
    print("📊 当前数据库环境")
    print("=" * 70)
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'use_pro=True' in content:
            print("✅ 当前环境: 生产环境")
            print("   - 主机: 8.137.104.120")
            print("   - 端口: 3306")
            print("   - 数据库: akshare")
        elif 'use_pro=False' in content:
            print("✅ 当前环境: 开发环境")
            print("   - 主机: localhost")
            print("   - 端口: 3306")
            print("   - 数据库: akshare")
        else:
            print("❌ 无法识别当前环境配置")
            
    except Exception as e:
        print(f"❌ 检查失败: {e}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='数据库环境切换工具')
    parser.add_argument('--to', type=str, choices=['pro', 'dev', 'check'], 
                       default='check',
                       help='目标环境: pro=生产环境, dev=开发环境, check=检查当前环境')
    
    args = parser.parse_args()
    
    if args.to == 'pro':
        switch_to_pro()
    elif args.to == 'dev':
        switch_to_dev()
    else:
        check_current_env()


if __name__ == '__main__':
    main()
