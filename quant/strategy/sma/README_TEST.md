# SMA双均线策略测试指南

## 快速开始

### 1. 离线测试（推荐 - 无需网络和数据库）

```bash
cd /home/wsm/codes/akshare
export PYTHONPATH=/home/wsm/codes/akshare:$PYTHONPATH
python quant/strategy/sma/test_sma_offline.py
```

这个测试使用模拟数据，可以验证策略核心逻辑是否正常工作。

### 2. 完整测试（需要数据库和网络）

确保以下配置正确：

#### 数据库配置
编辑 `.env` 文件，设置正确的数据库连接信息：

```bash
DB_PRO_HOST=your_host
DB_PRO_PORT=3306
DB_PRO_USER=root
DB_PRO_PASSWORD=your_password
DB_PRO_NAME=akshare
```

#### 运行测试
```bash
cd /home/wsm/codes/akshare
export PYTHONPATH=/home/wsm/codes/akshare:$PYTHONPATH
python quant/strategy/sma/sma_cross_test.py
```

## 测试文件说明

| 文件名 | 描述 | 依赖 |
|--------|------|------|
| `sma_cross_test.py` | 原始批量回测脚本 | 数据库 + 网络 |
| `test_sma_simple.py` | 简化版单股票测试 | 仅网络 |
| `test_sma_offline.py` | 离线模拟数据测试 | 无 |

## 常见问题

### Q1: 数据库连接失败
**错误**: `Access denied for user 'root'@'xxx'`

**解决**:
1. 检查 `.env` 文件中的密码是否正确
2. 确认数据库服务器允许远程连接
3. 检查IP白名单配置

### Q2: 网络请求失败
**错误**: `Remote end closed connection without response`

**解决**:
1. 检查网络连接
2. 稍后重试（可能被限流）
3. 考虑使用代理或VPN

### Q3: ModuleNotFoundError: No module named 'quant'
**解决**:
```bash
export PYTHONPATH=/home/wsm/codes/akshare:$PYTHONPATH
```

或者在项目根目录运行：
```bash
cd /home/wsm/codes/akshare
python -m quant.strategy.sma.test_sma_offline
```

## 策略参数说明

双均线策略 (`SmaCross`) 的参数：

- `pfast`: 短期均线周期（默认7天）
- `pslow`: 长期均线周期（默认30天）
- `stop_loss`: 止损百分比（默认5%）
- `take_profit`: 止盈百分比（默认15%）
- `max`: 最大资金使用比例（默认80%）

可以在 `strategy/SmaCross.py` 中修改这些参数。

## 查看测试结果

回测结果保存在：
```
data/cache/backtest_results.parquet
```

可以使用以下代码读取：
```python
import pandas as pd
df = pd.read_parquet('data/cache/backtest_results.parquet')
print(df)
```

## 更多信息

详细测试报告请查看：[TEST_REPORT.md](./TEST_REPORT.md)
