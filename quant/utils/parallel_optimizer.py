#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2026/5/15
Desc: 并行参数优化器 - 利用多进程加速策略参数寻优
"""

import multiprocessing as mp
from itertools import product
from datetime import datetime
import pandas as pd
import backtrader as bt


def _run_single_backtest(args):
    """
    在子进程中运行单次回测的辅助函数
    
    Args:
        args: 包含 (strategy_class, data_df, fromdate, todate, startcash, commission, params) 的元组
    """
    strategy_class, data_df, fromdate, todate, startcash, commission, params = args
    
    try:
        cerebro = bt.Cerebro(optreturn=False)
        
        # 准备数据
        data = bt.feeds.PandasData(
            dataname=data_df,
            fromdate=fromdate,
            todate=todate
        )
        cerebro.adddata(data)
        
        # 添加策略和参数
        cerebro.optstrategy(strategy_class, **params)
        
        cerebro.broker.setcash(startcash)
        cerebro.broker.setcommission(commission=commission)
        
        # 运行回测
        results = cerebro.run()
        
        # 提取结果
        strategy = results[0][0]
        endcash = strategy.broker.getvalue()
        net_profit = endcash - startcash
        returns_pct = (net_profit / startcash) * 100
        
        return {
            'params': params,
            'endcash': endcash,
            'net_profit': net_profit,
            'returns_pct': returns_pct
        }
    except Exception as e:
        return {'params': params, 'error': str(e)}


class ParallelOptimizer:
    """
    并行参数优化器
    
    通过多进程池并行运行 Backtrader 回测，显著提升参数扫描速度。
    """
    
    def __init__(self, n_jobs=None):
        """
        Args:
            n_jobs: 并行进程数。默认为 None，使用 CPU 核心数。
        """
        self.n_jobs = n_jobs or mp.cpu_count()
        print(f"⚙️  初始化并行优化器，使用 {self.n_jobs} 个并行进程")

    def optimize(self, strategy_class, data_df, param_ranges, 
                 fromdate=datetime(2024, 1, 1), 
                 todate=datetime.now(),
                 startcash=100000, 
                 commission=0.0005):
        """
        执行并行网格搜索
        
        Args:
            strategy_class: Backtrader 策略类
            data_df: 预处理后的 Pandas DataFrame (索引为日期)
            param_ranges: 参数字典，如 {'pfast': [5, 7], 'pslow': [20, 30]}
            fromdate: 回测开始日期
            todate: 回测结束日期
            startcash: 初始资金
            commission: 手续费率
            
        Returns:
            list: 包含所有参数组合结果的列表，按收益率降序排列
        """
        # 生成所有参数组合
        param_names = list(param_ranges.keys())
        param_values = list(param_ranges.values())
        all_combinations = list(product(*param_values))
        
        # 构造任务列表
        tasks = [
            (strategy_class, data_df, fromdate, todate, startcash, commission, dict(zip(param_names, combo)))
            for combo in all_combinations
        ]
        
        total_tasks = len(tasks)
        print(f"🚀 开始并行优化，共 {total_tasks} 种参数组合...")
        
        # 使用进程池并行执行
        results = []
        with mp.Pool(processes=self.n_jobs) as pool:
            for i, result in enumerate(pool.imap_unordered(_run_single_backtest, tasks), 1):
                results.append(result)
                if i % 10 == 0:
                    print(f"   进度: {i}/{total_tasks} ({i/total_tasks*100:.1f}%)")
        
        # 过滤掉出错的结果并按收益率排序
        valid_results = [r for r in results if 'error' not in r]
        valid_results.sort(key=lambda x: x['returns_pct'], reverse=True)
        
        print(f"✅ 优化完成，有效结果: {len(valid_results)}/{total_tasks}")
        return valid_results
