#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2026/5/15
Desc: 动态仓位管理器 - 基于 Backtrader 的 Sizer 组件
提供多种仓位计算策略，统一管理交易下单数量
"""

import backtrader as bt


class DynamicSizer(bt.Sizer):
    """
    动态仓位管理器
    
    根据账户总资金和预设比例计算下单数量
    """
    params = (
        ('position_pct', 0.8),  # 每次交易使用的资金比例 (默认 80%)
        ('min_stake', 100),     # 最小下单手数 (A股通常为100)
    )

    def __init__(self):
        pass

    def _getsizing(self, comminfo, cash, data, isbuy):
        """
        计算下单数量
        
        Args:
            comminfo: 佣金信息对象
            cash: 当前可用现金
            data: 数据馈送对象
            isbuy: 是否为买入操作
            
        Returns:
            int: 建议的下单数量
        """
        if isbuy:
            current_price = data.close[0]
            if current_price <= 0:
                return 0
            
            # 计算理论可买数量
            target_value = cash * self.params.position_pct
            size = int(target_value / current_price)
            
            # A股必须是100的整数倍
            size = (size // self.params.min_stake) * self.params.min_stake
            
            # 确保至少为最小手数（如果资金足够）
            if size < self.params.min_stake and cash > current_price * self.params.min_stake:
                size = self.params.min_stake
                
            return size
        else:
            # 卖出时返回当前持仓全部数量
            return self.broker.getposition(data).size


class VolatilityAdjustedSizer(bt.Sizer):
    """
    波动率调整仓位管理器 (ATR Based)
    
    根据市场波动率动态调整仓位：波动越大，仓位越小
    """
    params = (
        ('base_position_pct', 0.5),  # 基础仓位比例
        ('atr_period', 14),          # ATR 计算周期
        ('risk_factor', 0.02),       # 风险系数 (每笔交易最大亏损占总资金的比例)
    )

    def __init__(self):
        self.atr = bt.indicators.ATR(self.data, period=self.params.atr_period)

    def _getsizing(self, comminfo, cash, data, isbuy):
        if isbuy:
            current_price = data.close[0]
            atr_value = self.atr[0]
            
            if current_price <= 0 or atr_value <= 0:
                return 0
            
            # 基于风险系数的仓位计算：Size = (Cash * Risk_Factor) / ATR
            size = int((cash * self.params.risk_factor) / atr_value)
            
            # 限制在基础仓位比例以内
            max_size = int((cash * self.params.base_position_pct) / current_price)
            size = min(size, max_size)
            
            # A股 100 整数倍处理
            size = (size // 100) * 100
            
            return size
        else:
            return self.broker.getposition(data).size
