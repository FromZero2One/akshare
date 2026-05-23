#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
策略基类 - 所有量化策略的基础类
"""

from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)


class BaseStrategy(ABC):
    """
    所有策略的基类
    
    Attributes:
        name (str): 策略名称
        params (Dict[str, Any]): 策略参数
        results (Dict[str, Any]): 回测结果
    """
    
    def __init__(self, name: str):
        """
        初始化策略
        
        Args:
            name: 策略名称
        """
        self.name = name
        self.params = {}
        self.results = {}
        self.signals = None
        self.trades = []
        self.metrics = {}
        
        logger.info(f"策略初始化: {name}")
    
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        生成交易信号 - 必须由子类实现
        
        Args:
            data: 股票数据，包含 OHLCV 数据
        
        Returns:
            pd.DataFrame: 交易信号DataFrame，包含 signal 列
                          1: 买入信号
                          -1: 卖出信号
                          0: 无操作
        """
        pass
    
    @abstractmethod
    def calculate_metrics(self, signals: pd.DataFrame, prices: pd.Series) -> Dict[str, float]:
        """
        计算策略性能指标 - 必须由子类实现
        
        Args:
            signals: 交易信号
            prices: 价格序列
        
        Returns:
            Dict[str, float]: 性能指标字典
        """
        pass
    
    def _calculate_basic_metrics(self, returns: pd.Series, trades: List[Dict]) -> Dict[str, float]:
        """
        计算基础性能指标
        
        Args:
            returns: 收益率序列
            trades: 交易记录列表
        
        Returns:
            Dict[str, float]: 基础指标
        """
        metrics = {}
        
        if len(returns) > 0:
            # 总收益率
            metrics['total_return'] = returns.iloc[-1] if len(returns) > 0 else 0.0
            
            # 年化收益率
            days = len(returns)
            if days > 0:
                years = days / 252  # 假设252个交易日/年
                metrics['annual_return'] = (1 + metrics['total_return']) ** (1 / years) - 1 if years > 0 else 0.0
            
            # 年化波动率
            metrics['volatility'] = returns.std() * np.sqrt(252) if len(returns) > 1 else 0.0
            
            # 夏普比率
            risk_free_rate = 0.03  # 假设无风险利率3%
            sharpe_ratio = (metrics['annual_return'] - risk_free_rate) / metrics['volatility'] if metrics['volatility'] > 0 else 0.0
            metrics['sharpe_ratio'] = sharpe_ratio
            
            # 最大回撤
            cumulative_returns = (1 + returns).cumprod()
            running_max = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - running_max) / running_max
            metrics['max_drawdown'] = drawdown.min()
            
            # 胜率
            if len(trades) > 0:
                profitable_trades = sum(1 for trade in trades if trade.get('pnl', 0) > 0)
                metrics['win_rate'] = profitable_trades / len(trades)
            else:
                metrics['win_rate'] = 0.0
            
            # 交易次数
            metrics['total_trades'] = len(trades)
            
            # 平均交易收益
            if len(trades) > 0:
                metrics['avg_trade_return'] = np.mean([trade.get('return', 0) for trade in trades])
            else:
                metrics['avg_trade_return'] = 0.0
        
        return metrics
    
    def _execute_trades(self, signals: pd.DataFrame, prices: pd.Series, 
                       initial_capital: float = 100000) -> List[Dict[str, Any]]:
        """
        执行模拟交易
        
        Args:
            signals: 交易信号
            prices: 价格序列
            initial_capital: 初始资金
        
        Returns:
            List[Dict]: 交易记录列表
        """
        trades = []
        position = 0  # 当前持仓数量
        cash = initial_capital
        portfolio_value = []
        
        # 手续费率
        commission_rate = 0.0005  # 0.05%
        
        for i, (date, signal) in enumerate(zip(signals.index, signals['signal'])):
            current_price = prices.iloc[i]
            
            if signal == 1 and position == 0:  # 买入信号
                # 计算买入数量
                available_cash = cash * 0.8  # 使用80%资金
                buy_quantity = int(available_cash / current_price)
                
                if buy_quantity > 0:
                    # 计算手续费
                    commission = buy_quantity * current_price * commission_rate
                    total_cost = buy_quantity * current_price + commission
                    
                    if total_cost <= cash:
                        position = buy_quantity
                        cash -= total_cost
                        
                        trade_record = {
                            'date': date,
                            'type': 'BUY',
                            'price': current_price,
                            'quantity': buy_quantity,
                            'amount': total_cost,
                            'commission': commission,
                            'position': position
                        }
                        trades.append(trade_record)
                        
                        logger.debug(f"买入 {buy_quantity} 股 @ {current_price:.2f}")
            
            elif signal == -1 and position > 0:  # 卖出信号
                # 计算卖出收益
                sell_amount = position * current_price
                commission = sell_amount * commission_rate
                total_proceed = sell_amount - commission
                
                # 计算收益
                buy_cost = sum(trade['amount'] for trade in trades if trade['type'] == 'BUY')
                pnl = total_proceed - buy_cost
                return_pct = pnl / buy_cost if buy_cost > 0 else 0.0
                
                # 更新持仓和现金
                cash += total_proceed
                position = 0
                
                trade_record = {
                    'date': date,
                    'type': 'SELL',
                    'price': current_price,
                    'quantity': position + buy_quantity,
                    'amount': total_proceed,
                    'commission': commission,
                    'pnl': pnl,
                    'return': return_pct,
                    'position': position
                }
                trades.append(trade_record)
                
                logger.debug(f"卖出 {buy_quantity} 股 @ {current_price:.2f}, 收益: {pnl:.2f}")
        
        # 计算最终资产价值
        final_value = cash + position * prices.iloc[-1]
        total_return = (final_value - initial_capital) / initial_capital
        
        return trades
    
    def backtest(self, data: pd.DataFrame, initial_capital: float = 100000) -> Dict[str, Any]:
        """
        执行回测
        
        Args:
            data: 股票数据
            initial_capital: 初始资金
        
        Returns:
            Dict[str, Any]: 回测结果
        """
        logger.info(f"开始执行回测: {self.name}")
        
        # 数据验证
        required_columns = ['date', 'open', 'close', 'high', 'low', 'volume']
        for col in required_columns:
            if col not in data.columns:
                logger.error(f"数据缺少必要列: {col}")
                return {}
        
        # 确保数据按日期排序
        data = data.sort_values('date').reset_index(drop=True)
        
        # 生成交易信号
        try:
            self.signals = self.generate_signals(data)
            logger.info(f"生成信号完成，信号数量: {len(self.signals)}")
        except Exception as e:
            logger.error(f"生成信号失败: {e}")
            return {}
        
        # 执行模拟交易
        try:
            self.trades = self._execute_trades(
                self.signals, 
                data['close'], 
                initial_capital
            )
            logger.info(f"交易执行完成，交易次数: {len(self.trades)}")
        except Exception as e:
            logger.error(f"交易执行失败: {e}")
            return {}
        
        # 计算性能指标
        try:
            # 计算收益率序列
            returns = self._calculate_returns(data['close'])
            
            # 计算策略指标
            self.metrics = self.calculate_metrics(self.signals, data['close'])
            
            # 计算基础指标
            basic_metrics = self._calculate_basic_metrics(returns, self.trades)
            self.metrics.update(basic_metrics)
            
            logger.info("回测指标计算完成")
        except Exception as e:
            logger.error(f"指标计算失败: {e}")
            return {}
        
        # 构建结果
        results = {
            'strategy_name': self.name,
            'params': self.params,
            'signals': self.signals.to_dict() if self.signals is not None else {},
            'trades': self.trades,
            'metrics': self.metrics,
            'data_info': {
                'symbol': data.get('symbol', 'unknown'),
                'data_points': len(data),
                'date_range': {
                    'start': data['date'].min().strftime('%Y-%m-%d'),
                    'end': data['date'].max().strftime('%Y-%m-%d')
                }
            },
            'backtest_config': {
                'initial_capital': initial_capital,
                'commission_rate': 0.0005
            }
        }
        
        self.results = results
        logger.info(f"回测完成: {self.name}")
        return results
    
    def _calculate_returns(self, prices: pd.Series) -> pd.Series:
        """计算收益率序列"""
        return prices.pct_change().dropna()
    
    def plot_results(self, data: pd.DataFrame, save_path: Optional[str] = None):
        """
        绘制回测结果图表
        
        Args:
            data: 股票数据
            save_path: 图表保存路径
        """
        if not self.results:
            logger.warning("没有回测结果可绘制")
            return
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle(f'策略回测结果 - {self.name}', fontsize=16)
        
        # 1. 股价和信号
        ax1.plot(data['date'], data['close'], label='收盘价', alpha=0.7)
        
        # 绘制买入卖出点
        buy_signals = self.signals[self.signals['signal'] == 1]
        sell_signals = self.signals[self.signals['signal'] == -1]
        
        if not buy_signals.empty:
            buy_dates = data['date'][buy_signals.index]
            buy_prices = data['close'][buy_signals.index]
            ax1.scatter(buy_dates, buy_prices, color='red', marker='^', label='买入', s=100)
        
        if not sell_signals.empty:
            sell_dates = data['date'][sell_signals.index]
            sell_prices = data['close'][sell_signals.index]
            ax1.scatter(sell_dates, sell_prices, color='green', marker='v', label='卖出', s=100)
        
        ax1.set_title('股价和交易信号')
        ax1.set_xlabel('日期')
        ax1.set_ylabel('价格')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. 资金曲线
        if 'portfolio_value' in self.results:
            ax2.plot(self.results['portfolio_value'])
            ax2.set_title('资金曲线')
            ax2.set_xlabel('日期')
            ax2.set_ylabel('资金')
            ax2.grid(True, alpha=0.3)
        
        # 3. 交易统计
        if self.trades:
            buy_trades = [t for t in self.trades if t['type'] == 'BUY']
            sell_trades = [t for t in self.trades if t['type'] == 'SELL']
            
            trade_types = ['买入', '卖出']
            trade_counts = [len(buy_trades), len(sell_trades)]
            
            ax3.bar(trade_types, trade_counts, color=['red', 'green'])
            ax3.set_title('交易统计')
            ax3.set_ylabel('交易次数')
        
        # 4. 性能指标
        if self.metrics:
            metrics_names = list(self.metrics.keys())
            metrics_values = list(self.metrics.values())
            
            # 只显示数值型指标
            numeric_metrics = {}
            for name, value in self.metrics.items():
                if isinstance(value, (int, float)):
                    numeric_metrics[name] = value
            
            if numeric_metrics:
                metrics_names = list(numeric_metrics.keys())
                metrics_values = list(numeric_metrics.values())
                
                ax4.barh(range(len(metrics_names)), metrics_values)
                ax4.set_yticks(range(len(metrics_names)))
                ax4.set_yticklabels(metrics_names)
                ax4.set_title('性能指标')
                ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"图表已保存: {save_path}")
        else:
            plt.show()
        
        plt.close()
    
    def print_summary(self):
        """打印回测结果摘要"""
        if not self.results:
            print("暂无回测结果")
            return
        
        print(f"\n{'='*50}")
        print(f"策略名称: {self.results['strategy_name']}")
        print(f"{'='*50}")
        
        # 基础信息
        info = self.results['data_info']
        print(f"股票代码: {info['symbol']}")
        print(f"数据点数: {info['data_points']}")
        print(f"回测期间: {info['date_range']['start']} ~ {info['date_range']['end']}")
        print()
        
        # 性能指标
        print("性能指标:")
        for metric, value in self.metrics.items():
            if isinstance(value, (int, float)):
                print(f"  {metric}: {value:.4f}")
        print()
        
        # 交易统计
        print(f"交易统计:")
        print(f"  总交易次数: {len(self.trades)}")
        print(f"  买入次数: {len([t for t in self.trades if t['type'] == 'BUY'])}")
        print(f"  卖出次数: {len([t for t in self.trades if t['type'] == 'SELL'])}")
        
        if self.metrics.get('total_return'):
            print(f"  总收益率: {self.metrics['total_return']:.2%}")
        
        print(f"{'='*50}")


# 测试函数
def test_base_strategy():
    """测试策略基类"""
    from datetime import datetime, timedelta
    
    # 创建测试数据
    dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
    np.random.seed(42)
    
    # 生成模拟股价数据
    initial_price = 100
    returns = np.random.normal(0.001, 0.02, len(dates))
    prices = [initial_price]
    
    for ret in returns[1:]:
        prices.append(prices[-1] * (1 + ret))
    
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


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    test_base_strategy()