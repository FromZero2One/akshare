#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
双均线交叉策略 - 基于简单移动平均线的交易策略
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Any
from .base import BaseStrategy

logger = logging.getLogger(__name__)


class SMACrossStrategy(BaseStrategy):
    """
    双均线交叉策略
    
    策略逻辑：
    - 快线上穿慢线时买入（金叉）
    - 快线下穿慢线时卖出（死叉）
    - 支持止损和止盈
    
    参数：
    - fast_ma: 快速均线周期
    - slow_ma: 慢速均线周期
    - stop_loss: 止损百分比
    - take_profit: 止盈百分比
    - max_position: 最大仓位比例
    """
    
    def __init__(self, fast_ma: int = 7, slow_ma: int = 30, 
                 stop_loss: float = 0.05, take_profit: float = 0.15,
                 max_position: float = 0.8):
        """
        初始化双均线策略
        
        Args:
            fast_ma: 快速均线周期（默认7日）
            slow_ma: 慢速均线周期（默认30日）
            stop_loss: 止损百分比（默认5%）
            take_profit: 止盈百分比（默认15%）
            max_position: 最大仓位比例（默认80%）
        """
        super().__init__("双均线交叉")
        
        # 设置策略参数
        self.params = {
            'fast_ma': fast_ma,
            'slow_ma': slow_ma,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'max_position': max_position
        }
        
        logger.info(f"双均线策略初始化完成 - 快线: {fast_ma}, 慢线: {slow_ma}")
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        生成双均线交易信号
        
        Args:
            data: 包含 OHLCV 数据的 DataFrame
        
        Returns:
            pd.DataFrame: 包含 signal 列的交易信号
        """
        # 确保数据按日期排序
        data = data.sort_values('date').reset_index(drop=True)
        
        # 计算移动平均线
        data['ma_fast'] = data['close'].rolling(window=self.params['fast_ma'], min_periods=1).mean()
        data['ma_slow'] = data['close'].rolling(window=self.params['slow_ma'], min_periods=1).mean()
        
        # 初始化信号
        signals = pd.DataFrame(index=data.index, columns=['signal'], data=0)
        
        # 生成交易信号
        for i in range(1, len(data)):
            # 检查是否有有效数据
            if pd.isna(data['ma_fast'].iloc[i]) or pd.isna(data['ma_slow'].iloc[i]):
                continue
            
            current_fast = data['ma_fast'].iloc[i]
            current_slow = data['ma_slow'].iloc[i]
            prev_fast = data['ma_fast'].iloc[i-1]
            prev_slow = data['ma_slow'].iloc[i-1]
            
            # 金叉买入：快线上穿慢线
            if (current_fast > current_slow and prev_fast <= prev_slow):
                signals.iloc[i] = 1
            
            # 死叉卖出：快线下穿慢线
            elif (current_fast < current_slow and prev_fast >= prev_slow):
                signals.iloc[i] = -1
        
        # 数据清洗：去除无效信号
        signals['signal'] = signals['signal'].fillna(0).astype(int)
        
        logger.info(f"生成信号完成 - 总信号数: {len(signals)}, 买入: {(signals['signal'] == 1).sum()}, 卖出: {(signals['signal'] == -1).sum()}")
        
        return signals
    
    def calculate_metrics(self, signals: pd.DataFrame, prices: pd.Series) -> Dict[str, float]:
        """
        计算双均线策略的性能指标
        
        Args:
            signals: 交易信号
            prices: 价格序列
        
        Returns:
            Dict[str, float]: 策略指标
        """
        metrics = {}
        
        # 计算基本指标
        returns = prices.pct_change().dropna()
        
        if len(returns) > 0:
            # 基础收益率指标
            metrics['total_return'] = returns.sum()
            
            # 年化收益率
            trading_days = len(returns)
            if trading_days > 0:
                years = trading_days / 252
                metrics['annual_return'] = (1 + metrics['total_return']) ** (1 / years) - 1 if years > 0 else 0.0
            
            # 波动率和风险指标
            metrics['volatility'] = returns.std() * np.sqrt(252) if len(returns) > 1 else 0.0
            
            # 夏普比率
            risk_free_rate = 0.03
            if metrics['volatility'] > 0:
                metrics['sharpe_ratio'] = (metrics['annual_return'] - risk_free_rate) / metrics['volatility']
            else:
                metrics['sharpe_ratio'] = 0.0
            
            # 最大回撤
            cumulative_returns = (1 + returns).cumprod()
            running_max = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - running_max) / running_max
            metrics['max_drawdown'] = drawdown.min()
            
            # 卡玛比率
            if metrics['max_drawdown'] < 0:
                metrics['calmar_ratio'] = metrics['annual_return'] / abs(metrics['max_drawdown'])
            else:
                metrics['calmar_ratio'] = 0.0
            
            # 交易频率
            total_signals = len(signals[signals['signal'] != 0])
            if trading_days > 0:
                metrics['trade_frequency'] = total_signals / trading_days * 252  # 年化交易次数
            
            # 趋势强度指标
            fast_ma_trend = self._calculate_trend_strength(prices, self.params['fast_ma'])
            slow_ma_trend = self._calculate_trend_strength(prices, self.params['slow_ma'])
            metrics['fast_ma_trend'] = fast_ma_trend
            metrics['slow_ma_trend'] = slow_ma_trend
        
        return metrics
    
    def _calculate_trend_strength(self, prices: pd.Series, period: int) -> float:
        """
        计算趋势强度
        
        Args:
            prices: 价格序列
            period: 周期
        
        Returns:
            float: 趋势强度指标
        """
        if len(prices) < period:
            return 0.0
        
        # 计算价格变化趋势
        recent_prices = prices.tail(period)
        price_change = (recent_prices.iloc[-1] - recent_prices.iloc[0]) / recent_prices.iloc[0]
        
        # 计算波动率
        volatility = recent_prices.pct_change().std()
        
        # 趋势强度 = 价格变化 / 波动率
        if volatility > 0:
            trend_strength = price_change / volatility
        else:
            trend_strength = 0.0
        
        return trend_strength
    
    def get_detailed_analysis(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        获取详细的策略分析
        
        Args:
            data: 股票数据
        
        Returns:
            Dict[str, Any]: 详细分析结果
        """
        analysis = {}
        
        # 计算均线数据
        data['ma_fast'] = data['close'].rolling(window=self.params['fast_ma'], min_periods=1).mean()
        data['ma_slow'] = data['close'].rolling(window=self.params['slow_ma'], min_periods=1).mean()
        
        # 计算均线间距
        data['ma_spread'] = data['ma_fast'] - data['ma_slow']
        
        # 分析市场状态
        analysis['market_regime'] = self._analyze_market_regime(data)
        
        # 分析均线交叉点
        analysis['crossover_points'] = self._analyze_crossovers(data)
        
        # 分析均线距离
        analysis['ma_distance_stats'] = {
            'mean': data['ma_spread'].mean(),
            'std': data['ma_spread'].std(),
            'max': data['ma_spread'].max(),
            'min': data['ma_spread'].min(),
            'positive_ratio': (data['ma_spread'] > 0).mean()
        }
        
        return analysis
    
    def _analyze_market_regime(self, data: pd.DataFrame) -> Dict[str, float]:
        """
        分析市场状态
        
        Args:
            data: 包含均线数据的 DataFrame
        
        Returns:
            Dict[str, float]: 市场状态指标
        """
        regime = {}
        
        # 快线在慢线上方的天数比例
        regime['fast_above_slow'] = (data['ma_fast'] > data['ma_slow']).mean()
        
        # 均线发散程度
        regime['divergence'] = data['ma_spread'].std()
        
        # 均线收敛程度
        regime['convergence'] = 1 / (1 + regime['divergence']) if regime['divergence'] > 0 else 0
        
        # 趋势强度
        recent_spread = data['ma_spread'].tail(20).mean()
        regime['recent_trend'] = 'bullish' if recent_spread > 0 else 'bearish' if recent_spread < 0 else 'neutral'
        
        return regime
    
    def _analyze_crossovers(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        分析均线交叉点
        
        Args:
            data: 包含均线数据的 DataFrame
        
        Returns:
            List[Dict[str, Any]]: 交叉点列表
        """
        crossovers = []
        
        for i in range(1, len(data)):
            if pd.isna(data['ma_fast'].iloc[i]) or pd.isna(data['ma_fast'].iloc[i-1]):
                continue
            
            current_fast = data['ma_fast'].iloc[i]
            current_slow = data['ma_slow'].iloc[i]
            prev_fast = data['ma_fast'].iloc[i-1]
            prev_slow = data['ma_slow'].iloc[i-1]
            
            # 金叉
            if current_fast > current_slow and prev_fast <= prev_slow:
                crossovers.append({
                    'date': data['date'].iloc[i],
                    'type': 'golden_cross',
                    'price': data['close'].iloc[i],
                    'ma_fast': current_fast,
                    'ma_slow': current_slow,
                    'spread': current_fast - current_slow
                })
            
            # 死叉
            elif current_fast < current_slow and prev_fast >= prev_slow:
                crossovers.append({
                    'date': data['date'].iloc[i],
                    'type': 'death_cross',
                    'price': data['close'].iloc[i],
                    'ma_fast': current_fast,
                    'ma_slow': current_slow,
                    'spread': current_fast - current_slow
                })
        
        return crossovers


# 增强版双均线策略
class SMACrossEnhancedStrategy(SMACrossStrategy):
    """
    增强版双均线策略 - 包含更多技术指标
    """
    
    def __init__(self, fast_ma: int = 7, slow_ma: int = 30, 
                 stop_loss: float = 0.05, take_profit: float = 0.15,
                 max_position: float = 0.8,
                 volume_filter: bool = True,
                 trend_filter: bool = True):
        """
        初始化增强版双均线策略
        
        Args:
            fast_ma: 快速均线周期
            slow_ma: 慢速均线周期
            stop_loss: 止损百分比
            take_profit: 止盈百分比
            max_position: 最大仓位比例
            volume_filter: 是否启用成交量过滤
            trend_filter: 是否启用趋势过滤
        """
        super().__init__(fast_ma, slow_ma, stop_loss, take_profit, max_position)
        
        self.params.update({
            'volume_filter': volume_filter,
            'trend_filter': trend_filter
        })
        
        self.name = "增强双均线交叉"
        logger.info("增强版双均线策略初始化完成")
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        生成增强版交易信号
        
        Args:
            data: 包含 OHLCV 数据的 DataFrame
        
        Returns:
            pd.DataFrame: 包含 signal 列的交易信号
        """
        # 先获取基础信号
        signals = super().generate_signals(data)
        
        # 应用成交量过滤
        if self.params['volume_filter']:
            signals = self._apply_volume_filter(data, signals)
        
        # 应用趋势过滤
        if self.params['trend_filter']:
            signals = self._apply_trend_filter(data, signals)
        
        logger.info(f"增强信号生成完成 - 总信号数: {len(signals)}, 最终买入: {(signals['signal'] == 1).sum()}, 最终卖出: {(signals['signal'] == -1).sum()}")
        
        return signals
    
    def _apply_volume_filter(self, data: pd.DataFrame, signals: pd.DataFrame) -> pd.DataFrame:
        """应用成交量过滤"""
        # 计算成交量均线
        volume_ma = data['volume'].rolling(window=20, min_periods=1).mean()
        
        # 只在成交量高于均量时执行交易
        volume_mask = data['volume'] > volume_ma * 0.8
        
        # 过滤信号
        filtered_signals = signals.copy()
        filtered_signals.loc[~volume_mask & (signals['signal'] != 0), 'signal'] = 0
        
        return filtered_signals
    
    def _apply_trend_filter(self, data: pd.DataFrame, signals: pd.DataFrame) -> pd.DataFrame:
        """应用趋势过滤"""
        # 计算长期趋势（60日均线）
        data['ma_60'] = data['close'].rolling(window=60, min_periods=1).mean()
        
        # 只在长期上升趋势中买入
        trend_mask = data['close'] > data['ma_60']
        
        # 只买入符合趋势条件的信号
        filtered_signals = signals.copy()
        filtered_signals.loc[~trend_mask & (signals['signal'] == 1), 'signal'] = 0
        
        return filtered_signals


# 测试函数
def test_sma_cross_strategy():
    """测试双均线策略"""
    import numpy as np
    from datetime import datetime, timedelta
    
    # 创建测试数据
    dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
    np.random.seed(42)
    
    # 生成模拟股价数据（有趋势性）
    initial_price = 100
    trend = 0.0005  # 上升趋势
    volatility = 0.02
    
    prices = [initial_price]
    for i in range(1, len(dates)):
        # 添加趋势和随机波动
        daily_return = trend + np.random.normal(0, volatility)
        prices.append(prices[-1] * (1 + daily_return))
    
    test_data = pd.DataFrame({
        'date': dates,
        'open': prices,
        'close': prices,
        'high': [p * 1.02 for p in prices],
        'low': [p * 0.98 for p in prices],
        'volume': np.random.randint(1000000, 10000000, len(dates))
    })
    
    print("测试数据创建完成")
    print(f"数据形状: {test_data.shape}")
    print(f"价格范围: {test_data['close'].min():.2f} ~ {test_data['close'].max():.2f}")
    
    # 测试基本策略
    print("\n测试基本双均线策略...")
    strategy = SMACrossStrategy(fast_ma=7, slow_ma=30)
    results = strategy.backtest(test_data)
    
    if results:
        strategy.print_summary()
    
    # 测试增强策略
    print("\n测试增强双均线策略...")
    enhanced_strategy = SMACrossEnhancedStrategy(fast_ma=7, slow_ma=30)
    enhanced_results = enhanced_strategy.backtest(test_data)
    
    if enhanced_results:
        enhanced_strategy.print_summary()


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    test_sma_cross_strategy()