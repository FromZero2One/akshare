#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2025/1/15
Desc: 网络诊断工具 - 检查AKShare API连接状态
"""

import sys
import os
import time
import socket

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def check_dns_resolution(hostname):
    """检查DNS解析"""
    print(f"\n{'='*60}")
    print(f"1. DNS解析测试: {hostname}")
    print('='*60)
    
    try:
        ip = socket.gethostbyname(hostname)
        print(f"✅ DNS解析成功: {hostname} -> {ip}")
        return True, ip
    except Exception as e:
        print(f"❌ DNS解析失败: {e}")
        return False, None


def check_port_connectivity(host, port, timeout=5):
    """检查端口连通性"""
    print(f"\n{'='*60}")
    print(f"2. 端口连通性测试: {host}:{port}")
    print('='*60)
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"✅ 端口 {port} 可连接")
            return True
        else:
            print(f"❌ 端口 {port} 无法连接 (错误码: {result})")
            return False
    except Exception as e:
        print(f"❌ 连接测试失败: {e}")
        return False


def check_http_access(url, timeout=10):
    """检查HTTP访问"""
    print(f"\n{'='*60}")
    print(f"3. HTTP访问测试: {url}")
    print('='*60)
    
    try:
        import requests
        
        # 禁用代理
        proxies = {'http': None, 'https': None}
        
        start_time = time.time()
        response = requests.get(url, timeout=timeout, proxies=proxies)
        elapsed = time.time() - start_time
        
        print(f"✅ HTTP访问成功")
        print(f"   - 状态码: {response.status_code}")
        print(f"   - 响应时间: {elapsed:.2f}秒")
        print(f"   - 响应大小: {len(response.content)} bytes")
        return True
    except Exception as e:
        print(f"❌ HTTP访问失败: {e}")
        return False


def check_akshare_api():
    """检查AKShare API"""
    print(f"\n{'='*60}")
    print(f"4. AKShare API测试")
    print('='*60)
    
    try:
        import akshare as ak
        
        # 测试获取单只股票数据
        print("正在测试获取股票 601398 的数据...")
        start_time = time.time()
        
        df = ak.stock_zh_a_hist(symbol="601398", period="daily", adjust="qfq")
        elapsed = time.time() - start_time
        
        print(f"✅ AKShare API调用成功")
        print(f"   - 获取数据行数: {len(df)}")
        print(f"   - 耗时: {elapsed:.2f}秒")
        print(f"   - 列名: {df.columns.tolist()}")
        return True
    except Exception as e:
        print(f"❌ AKShare API调用失败: {e}")
        return False


def check_proxy_settings():
    """检查代理设置"""
    print(f"\n{'='*60}")
    print(f"5. 代理设置检查")
    print('='*60)
    
    import os
    
    proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
    
    has_proxy = False
    for var in proxy_vars:
        value = os.environ.get(var)
        if value:
            print(f"⚠️  {var} = {value}")
            has_proxy = True
    
    if not has_proxy:
        print("✅ 未检测到代理设置")
    else:
        print("⚠️  检测到代理设置，可能影响连接")
        print("💡 建议: 运行 run_update_no_proxy.py 禁用代理")
    
    return not has_proxy


def main():
    """主函数"""
    print("\n" + "🔍" * 30)
    print("  AKShare API 网络诊断工具")
    print("🔍" * 30)
    
    # 目标API
    api_host = "push2his.eastmoney.com"
    api_port = 443
    test_url = f"https://{api_host}/api/qt/stock/kline/get?secid=1.601398&klt=101"
    
    results = []
    
    # 1. 检查代理设置
    results.append(("代理设置", check_proxy_settings()))
    
    # 2. DNS解析
    dns_ok, ip = check_dns_resolution(api_host)
    results.append(("DNS解析", dns_ok))
    
    if not dns_ok:
        print("\n❌ DNS解析失败，无法继续测试")
        return
    
    # 3. 端口连通性
    results.append(("端口连通性", check_port_connectivity(ip if ip else api_host, api_port)))
    
    # 4. HTTP访问
    results.append(("HTTP访问", check_http_access(test_url)))
    
    # 5. AKShare API
    results.append(("AKShare API", check_akshare_api()))
    
    # 汇总结果
    print(f"\n{'='*60}")
    print("📊 诊断结果汇总")
    print('='*60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {test_name}")
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！网络正常。")
        print("\n💡 建议: 现在可以运行数据更新脚本")
        print("   python run_update_no_proxy.py")
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败")
        print("\n💡 建议:")
        if not results[0][1]:
            print("   1. 禁用系统代理或使用 run_update_no_proxy.py")
        if not results[1][1]:
            print("   2. 检查DNS配置")
        if not results[2][1]:
            print("   3. 检查防火墙设置")
        if not results[3][1] or not results[4][1]:
            print("   4. API服务器可能暂时不可用，请稍后重试")
            print("   5. 考虑更换数据源或联系API提供方")


if __name__ == '__main__':
    main()
