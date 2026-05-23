#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
结果管理器 - 管理回测结果的保存、加载和分析
"""

import os
import json
import pickle
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns

from .data_fetcher import DataFetcher

logger = logging.getLogger(__name__)


class ResultManager:
    """
    结果管理器 - 保存、加载和分析回测结果
    
    功能：
    - 多格式结果保存（JSON、Parquet、CSV）
    - 结果查询和筛选
    - 性能分析和对比
    - 报告生成
    - 可视化图表
    """
    
    def __init__(self, results_dir: str = None, save_format: str = "json"):
        """
        初始化结果管理器
        
        Args:
            results_dir: 结果保存目录
            save_format: 保存格式 (json, parquet, csv)
        """
        if results_dir is None:
            results_dir = os.path.join(os.path.dirname(__file__), "../../backtest_results")
        
        self.results_dir = results_dir
        self.save_format = save_format.lower()
        
        # 确保目录存在
        os.makedirs(self.results_dir, exist_ok=True)
        
        # 创建子目录
        self.json_dir = os.path.join(results_dir, "json")
        self.parquet_dir = os.path.join(results_dir, "parquet")
        self.csv_dir = os.path.join(results_dir, "csv")
        self.charts_dir = os.path.join(results_dir, "charts")
        
        for dir_path in [self.json_dir, self.parquet_dir, self.csv_dir, self.charts_dir]:
            os.makedirs(dir_path, exist_ok=True)
        
        # 结果缓存
        self.results_cache = {}
        self.cache_expiry = timedelta(hours=1)
        
        # 加载索引
        self.result_index = self._load_result_index()
        
        logger.info(f"结果管理器初始化完成 - 保存格式: {save_format}, 结果目录: {results_dir}")
    
    def _load_result_index(self) -> List[Dict[str, Any]]:
        """加载结果索引"""
        index_file = os.path.join(self.results_dir, "result_index.json")
        
        if os.path.exists(index_file):
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    index = json.load(f)
                    logger.info(f"加载结果索引: {len(index)} 个结果")
                    return index
            except Exception as e:
                logger.warning(f"加载结果索引失败: {e}")
        
        return []
    
    def _save_result_index(self):
        """保存结果索引"""
        index_file = os.path.join(self.results_dir, "result_index.json")
        
        try:
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(self.result_index, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            logger.error(f"保存结果索引失败: {e}")
    
    def _get_result_filename(self, symbol: str, strategy_name: str, timestamp: str = None) -> str:
        """获取结果文件名"""
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        return f"{symbol}_{strategy_name}_{timestamp}"
    
    def _get_cache_key(self, symbol: str, strategy_name: str, adjust: str = "qfq") -> str:
        """生成缓存键"""
        return f"{symbol}_{strategy_name}_{adjust}"
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """检查缓存是否有效"""
        if cache_key not in self.results_cache:
            return False
        
        cache_time = self.results_cache[cache_key]['timestamp']
        return datetime.now() - cache_time < self.cache_expiry
    
    def save_results(self, symbol: str, strategy_name: str, results: Dict[str, Any], 
                    adjust: str = "qfq", timestamp: str = None) -> str:
        """
        保存回测结果
        
        Args:
            symbol: 股票代码
            strategy_name: 策略名称
            results: 回测结果
            adjust: 复权方式
            timestamp: 时间戳
        
        Returns:
            str: 保存的文件路径
        """
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 生成唯一ID
        result_id = f"{symbol}_{strategy_name}_{timestamp}"
        
        # 添加元数据
        metadata = {
            'result_id': result_id,
            'symbol': symbol,
            'strategy_name': strategy_name,
            'adjust': adjust,
            'save_time': timestamp,
            'file_format': self.save_format
        }
        
        # 更新结果元数据
        results['metadata'] = metadata
        
        # 根据格式保存
        if self.save_format == "json":
            filepath = os.path.join(self.json_dir, f"{result_id}.json")
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2, default=str)
        
        elif self.save_format == "parquet":
            # 将结果转换为DataFrame
            results_df = self._convert_to_dataframe(results)
            filepath = os.path.join(self.parquet_dir, f"{result_id}.parquet")
            results_df.to_parquet(filepath, index=False)
        
        elif self.save_format == "csv":
            results_df = self._convert_to_dataframe(results)
            filepath = os.path.join(self.csv_dir, f"{result_id}.csv")
            results_df.to_csv(filepath, index=False, encoding='utf-8-sig')
        
        else:
            raise ValueError(f"不支持的保存格式: {self.save_format}")
        
        # 更新索引
        self.result_index.append(metadata)
        self._save_result_index()
        
        # 更新缓存
        cache_key = self._get_cache_key(symbol, strategy_name, adjust)
        self.results_cache[cache_key] = {
            'results': results,
            'filepath': filepath,
            'timestamp': datetime.now()
        }
        
        logger.info(f"结果保存成功: {filepath}")
        return filepath
    
    def _convert_to_dataframe(self, results: Dict[str, Any]) -> pd.DataFrame:
        """将结果转换为DataFrame格式"""
        # 提取关键指标
        metrics = results.get('metrics', {})
        trades = results.get('trades', [])
        
        # 创建基础数据
        data = {
            'symbol': [results['metadata']['symbol']],
            'strategy_name': [results['metadata']['strategy_name']],
            'adjust': [results['metadata']['adjust']],
            'save_time': [results['metadata']['save_time']],
            'total_return': [metrics.get('total_return', 0)],
            'annual_return': [metrics.get('annual_return', 0)],
            'volatility': [metrics.get('volatility', 0)],
            'sharpe_ratio': [metrics.get('sharpe_ratio', 0)],
            'max_drawdown': [metrics.get('max_drawdown', 0)],
            'win_rate': [metrics.get('win_rate', 0)],
            'total_trades': [metrics.get('total_trades', 0)],
            'initial_capital': [results.get('backtest_config', {}).get('initial_capital', 0)]
        }
        
        return pd.DataFrame(data)
    
    def load_results(self, symbol: str = None, strategy_name: str = None, 
                    adjust: str = "qfq", limit: int = None) -> List[Dict[str, Any]]:
        """
        加载回测结果
        
        Args:
            symbol: 股票代码
            strategy_name: 策略名称
            adjust: 复权方式
            limit: 限制返回数量
        
        Returns:
            List[Dict[str, Any]]: 结果列表
        """
        # 检查缓存
        cache_key = self._get_cache_key(symbol or "", strategy_name or "", adjust)
        
        if symbol and strategy_name and self._is_cache_valid(cache_key):
            return [self.results_cache[cache_key]['results']]
        
        # 筛选结果
        filtered_results = []
        
        for result_meta in self.result_index:
            # 筛选条件
            if symbol and result_meta['symbol'] != symbol:
                continue
            
            if strategy_name and result_meta['strategy_name'] != strategy_name:
                continue
            
            if adjust and result_meta['adjust'] != adjust:
                continue
            
            # 加载具体结果文件
            try:
                result = self._load_result_file(result_meta)
                if result:
                    filtered_results.append(result)
                    
                    # 更新缓存
                    if symbol and strategy_name:
                        self.results_cache[cache_key] = {
                            'results': result,
                            'filepath': result_meta['filepath'],
                            'timestamp': datetime.now()
                        }
                    
            except Exception as e:
                logger.error(f"加载结果文件失败 {result_meta['result_id']}: {e}")
        
        # 按时间排序
        filtered_results.sort(key=lambda x: x['metadata']['save_time'], reverse=True)
        
        # 限制数量
        if limit:
            filtered_results = filtered_results[:limit]
        
        return filtered_results
    
    def _load_result_file(self, metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """加载结果文件"""
        file_id = metadata['result_id']
        file_format = metadata['file_format']
        
        try:
            if file_format == "json":
                filepath = os.path.join(self.json_dir, f"{file_id}.json")
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            elif file_format == "parquet":
                filepath = os.path.join(self.parquet_dir, f"{file_id}.parquet")
                df = pd.read_parquet(filepath)
                return df.to_dict('records')[0] if len(df) > 0 else None
            
            elif file_format == "csv":
                filepath = os.path.join(self.csv_dir, f"{file_id}.csv")
                df = pd.read_csv(filepath)
                return df.to_dict('records')[0] if len(df) > 0 else None
        
        except Exception as e:
            logger.error(f"加载结果文件失败 {file_id}: {e}")
            return None
    
    def generate_summary_report(self, results: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        生成汇总报告
        
        Args:
            results: 结果列表，如果为None则加载所有结果
        
        Returns:
            Dict[str, Any]: 汇总报告
        """
        if results is None:
            results = self.load_results()
        
        if not results:
            return {'error': '没有结果数据'}
        
        # 基础统计
        total_results = len(results)
        unique_symbols = len(set(r['metadata']['symbol'] for r in results))
        unique_strategies = len(set(r['metadata']['strategy_name'] for r in results))
        
        # 性能指标
        metrics_list = [r.get('metrics', {}) for r in results]
        
        # 收益率统计
        returns = [m.get('total_return', 0) for m in metrics_list]
        positive_returns = [r for r in returns if r > 0]
        
        summary = {
            'total_results': total_results,
            'unique_symbols': unique_symbols,
            'unique_strategies': unique_strategies,
            'performance_stats': {
                'total_return_avg': np.mean(returns) if returns else 0,
                'total_return_median': np.median(returns) if returns else 0,
                'total_return_std': np.std(returns) if len(returns) > 1 else 0,
                'positive_return_count': len(positive_returns),
                'positive_return_rate': len(positive_returns) / total_results if total_results > 0 else 0,
                'best_return': max(returns) if returns else 0,
                'worst_return': min(returns) if returns else 0
            },
            'strategy_performance': self._analyze_strategy_performance(metrics_list),
            'symbol_performance': self._analyze_symbol_performance(results),
            'recent_results': results[:5]  # 最近5个结果
        }
        
        return summary
    
    def _analyze_strategy_performance(self, metrics_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析策略性能"""
        if not metrics_list:
            return {}
        
        # 按策略分组
        strategy_metrics = {}
        for metrics in metrics_list:
            strategy_name = metrics.get('strategy_name', 'unknown')
            if strategy_name not in strategy_metrics:
                strategy_metrics[strategy_name] = []
            strategy_metrics[strategy_name].append(metrics)
        
        # 计算每个策略的平均性能
        strategy_performance = {}
        for strategy_name, metrics in strategy_metrics.items():
            returns = [m.get('total_return', 0) for m in metrics]
            sharpe_ratios = [m.get('sharpe_ratio', 0) for m in metrics]
            
            strategy_performance[strategy_name] = {
                'avg_return': np.mean(returns),
                'median_return': np.median(returns),
                'std_return': np.std(returns) if len(returns) > 1 else 0,
                'win_rate': np.mean([1 for r in returns if r > 0]) if returns else 0,
                'avg_sharpe': np.mean(sharpe_ratios) if sharpe_ratios else 0,
                'sample_count': len(returns)
            }
        
        return strategy_performance
    
    def _analyze_symbol_performance(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析股票性能"""
        if not results:
            return {}
        
        # 按股票分组
        symbol_metrics = {}
        for result in results:
            symbol = result['metadata']['symbol']
            metrics = result.get('metrics', {})
            
            if symbol not in symbol_metrics:
                symbol_metrics[symbol] = []
            symbol_metrics[symbol].append(metrics)
        
        # 计算每个股票的平均性能
        symbol_performance = {}
        for symbol, metrics in symbol_metrics.items():
            returns = [m.get('total_return', 0) for m in metrics]
            
            best_metric = max(metrics, key=lambda x: x.get('total_return', 0)) if metrics else {'strategy_name': 'unknown'}
            symbol_performance[symbol] = {
                'avg_return': np.mean(returns),
                'median_return': np.median(returns),
                'std_return': np.std(returns) if len(returns) > 1 else 0,
                'win_rate': np.mean([1 for r in returns if r > 0]) if returns else 0,
                'best_strategy': best_metric.get('strategy_name', 'unknown'),
                'sample_count': len(returns)
            }
        
        return symbol_performance
    
    def generate_comparison_chart(self, results: List[Dict[str, Any]], 
                                 save_path: str = None) -> str:
        """
        生成比较图表
        
        Args:
            results: 结果列表
            save_path: 保存路径
        
        Returns:
            str: 图表保存路径
        """
        if not results:
            return ""
        
        # 准备数据
        data = []
        for result in results:
            metrics = result.get('metrics', {})
            data.append({
                'symbol': result['metadata']['symbol'],
                'strategy': result['metadata']['strategy_name'],
                'return': metrics.get('total_return', 0),
                'sharpe': metrics.get('sharpe_ratio', 0),
                'drawdown': metrics.get('max_drawdown', 0),
                'win_rate': metrics.get('win_rate', 0)
            })
        
        df = pd.DataFrame(data)
        
        # 创建图表
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('策略性能比较', fontsize=16)
        
        # 1. 收益率分布
        axes[0, 0].scatter(df['symbol'], df['return'], alpha=0.6, s=100)
        axes[0, 0].set_title('各股票收益率')
        axes[0, 0].set_xlabel('股票代码')
        axes[0, 0].set_ylabel('收益率')
        axes[0, 0].tick_params(axis='x', rotation=45)
        
        # 2. 夏普比率 vs 收益率
        axes[0, 1].scatter(df['return'], df['sharpe'], alpha=0.6, s=100)
        axes[0, 1].set_title('夏普比率 vs 收益率')
        axes[0, 1].set_xlabel('收益率')
        axes[0, 1].set_ylabel('夏普比率')
        
        # 3. 最大回撤分布
        axes[1, 0].hist(df['drawdown'], bins=20, alpha=0.7, edgecolor='black')
        axes[1, 0].set_title('最大回撤分布')
        axes[1, 0].set_xlabel('回撤比例')
        axes[1, 0].set_ylabel('频数')
        
        # 4. 胜率分布
        axes[1, 1].hist(df['win_rate'], bins=20, alpha=0.7, edgecolor='black', color='green')
        axes[1, 1].set_title('胜率分布')
        axes[1, 1].set_xlabel('胜率')
        axes[1, 1].set_ylabel('频数')
        
        plt.tight_layout()
        
        # 保存图表
        if save_path is None:
            save_path = os.path.join(self.charts_dir, f"comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"比较图表已保存: {save_path}")
        return save_path
    
    def export_results(self, results: List[Dict[str, Any]], 
                      export_format: str = "excel", 
                      output_path: str = None) -> str:
        """
        导出结果到文件
        
        Args:
            results: 结果列表
            export_format: 导出格式 (excel, csv, json)
            output_path: 输出路径
        
        Returns:
            str: 导出文件路径
        """
        if not results:
            return ""
        
        # 准备数据
        data = []
        for result in results:
            metrics = result.get('metrics', {})
            data.append({
                'symbol': result['metadata']['symbol'],
                'strategy_name': result['metadata']['strategy_name'],
                'adjust': result['metadata']['adjust'],
                'save_time': result['metadata']['save_time'],
                'total_return': metrics.get('total_return', 0),
                'annual_return': metrics.get('annual_return', 0),
                'volatility': metrics.get('volatility', 0),
                'sharpe_ratio': metrics.get('sharpe_ratio', 0),
                'max_drawdown': metrics.get('max_drawdown', 0),
                'win_rate': metrics.get('win_rate', 0),
                'total_trades': metrics.get('total_trades', 0),
                'initial_capital': result.get('backtest_config', {}).get('initial_capital', 0)
            })
        
        df = pd.DataFrame(data)
        
        # 生成输出路径
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = os.path.join(self.results_dir, f"export_{timestamp}.{export_format}")
        
        # 导出
        if export_format == "excel":
            df.to_excel(output_path, index=False)
        elif export_format == "csv":
            df.to_csv(output_path, index=False, encoding='utf-8-sig')
        elif export_format == "json":
            df.to_json(output_path, orient='records', force_ascii=False, indent=2)
        else:
            raise ValueError(f"不支持的导出格式: {export_format}")
        
        logger.info(f"结果导出成功: {output_path}")
        return output_path
    
    def cleanup_old_results(self, days: int = 30):
        """
        清理旧结果
        
        Args:
            days: 保留天数
        """
        cutoff_time = datetime.now() - timedelta(days=days)
        
        # 清理索引
        new_index = []
        cleaned_count = 0
        
        for meta in self.result_index:
            save_time = datetime.strptime(meta['save_time'], '%Y%m%d_%H%M%S')
            
            if save_time > cutoff_time:
                new_index.append(meta)
            else:
                cleaned_count += 1
                # 删除文件
                file_id = meta['result_id']
                file_format = meta['file_format']
                
                if file_format == "json":
                    filepath = os.path.join(self.json_dir, f"{file_id}.json")
                elif file_format == "parquet":
                    filepath = os.path.join(self.parquet_dir, f"{file_id}.parquet")
                elif file_format == "csv":
                    filepath = os.path.join(self.csv_dir, f"{file_id}.csv")
                
                if os.path.exists(filepath):
                    os.remove(filepath)
        
        self.result_index = new_index
        self._save_result_index()
        
        logger.info(f"清理旧结果完成: 清理了 {cleaned_count} 个旧结果")
    
    def get_storage_info(self) -> Dict[str, Any]:
        """获取存储信息"""
        info = {
            'results_dir': self.results_dir,
            'save_format': self.save_format,
            'total_results': len(self.result_index),
            'cache_size': len(self.results_cache),
            'directories': {
                'json': self.json_dir,
                'parquet': self.parquet_dir,
                'csv': self.csv_dir,
                'charts': self.charts_dir
            },
            'file_counts': {}
        }
        
        # 统计各格式文件数量
        for format_name, dir_path in info['directories'].items():
            if os.path.exists(dir_path):
                info['file_counts'][format_name] = len([f for f in os.listdir(dir_path) if f.endswith(('.json', '.parquet', '.csv')[:3])])
        
        return info


# 测试函数
def test_result_manager():
    """测试结果管理器"""
    # 创建测试数据
    test_result = {
        'strategy_name': '双均线交叉',
        'metrics': {
            'total_return': 0.15,
            'annual_return': 0.12,
            'volatility': 0.18,
            'sharpe_ratio': 0.67,
            'max_drawdown': -0.08,
            'win_rate': 0.65,
            'total_trades': 25
        },
        'metadata': {
            'symbol': '000001',
            'strategy_name': '双均线交叉',
            'adjust': 'qfq',
            'save_time': datetime.now().strftime('%Y%m%d_%H%M%S')
        }
    }
    
    # 创建结果管理器
    manager = ResultManager(save_format="json")
    
    # 保存结果
    print("测试结果保存...")
    filepath = manager.save_results("000001", "双均线交叉", test_result)
    print(f"结果已保存: {filepath}")
    
    # 加载结果
    print("\n测试结果加载...")
    results = manager.load_results(symbol="000001")
    print(f"加载到 {len(results)} 个结果")
    
    # 生成汇总报告
    print("\n生成汇总报告...")
    summary = manager.generate_summary_report(results)
    print(f"汇总报告: {summary}")
    
    # 显示存储信息
    print("\n存储信息:")
    storage_info = manager.get_storage_info()
    for key, value in storage_info.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    test_result_manager()