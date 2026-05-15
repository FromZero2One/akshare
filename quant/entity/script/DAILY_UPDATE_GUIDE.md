# 每日股票数据增量更新使用指南

## 📋 功能说明

本模块实现了**每日自动从数据库获取所有股票代码，批量拉取当日个股数据并增量保存**的功能。

### 核心特性

- ✅ **自动化**: 从数据库自动获取股票列表，无需手动配置
- ✅ **增量更新**: 只保存最新数据，避免重复存储
- ✅ **并发处理**: 支持多线程并发，大幅提升更新速度
- ✅ **智能限流**: 自动添加请求间隔，避免API限流
- ✅ **容错机制**: 单个股票失败不影响其他股票
- ✅ **详细日志**: 完整的执行日志和统计报告
- ✅ **定时任务**: 支持APScheduler自动调度（可选）

---

## 🚀 快速开始

### 方式1: 命令行直接运行（推荐）

#### 基本用法

```bash
# 更新所有股票数据（前复权）
python quant/entity/script/daily_stock_updater.py

# 指定后复权
python quant/entity/script/daily_stock_updater.py --adjust hfq

# 测试模式（只处理10只股票）
python quant/entity/script/daily_stock_updater.py --test
```

#### 高级参数

```bash
# 自定义并发数和请求间隔
python quant/entity/script/daily_stock_updater.py \
    --workers 8 \
    --delay 0.3 \
    --adjust qfq

# 删除旧数据后重新保存
python quant/entity/script/daily_stock_updater.py --isDel

# 测试模式处理50只股票
python quant/entity/script/daily_stock_updater.py --test --test-count 50
```

#### 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--adjust` | str | qfq | 复权类型: qfq(前复权), hfq(后复权), ''(不复权) |
| `--workers` | int | 5 | 并发线程数（建议3-10） |
| `--delay` | float | 0.5 | 请求间隔时间（秒） |
| `--isDel` | flag | False | 是否删除旧数据 |
| `--test` | flag | False | 测试模式（只处理少量股票） |
| `--test-count` | int | 10 | 测试模式下的股票数量 |

---

### 方式2: Python代码调用

```python
from quant.entity.script.daily_stock_updater import DailyStockDataUpdater

# 创建更新器
updater = DailyStockDataUpdater(
    adjust="qfq",              # 前复权
    max_workers=5,             # 5个并发线程
    delay_between_requests=0.5, # 0.5秒间隔
    isDel=False                # 不删除旧数据
)

# 执行更新（生产模式）
updater.run(test_mode=False)

# 或者测试模式（只处理10只股票）
updater.run(test_mode=True, test_count=10)
```

---

### 方式3: 定时任务（自动执行）

#### 安装依赖

```bash
pip install apscheduler
```

#### 启动调度器

```bash
# 启动定时任务（前台运行）
python quant/entity/script/scheduler.py

# 后台运行（Linux/Mac）
nohup python quant/entity/script/scheduler.py > scheduler.log 2>&1 &

# 后台运行（Windows PowerShell）
Start-Process python -ArgumentList "quant/entity/script/scheduler.py" -WindowStyle Hidden
```

#### 定时任务配置

编辑 `scheduler.py` 文件，修改执行时间：

```python
# 每日更新任务：交易日下午4点执行
scheduler.add_job(
    func=daily_update_job,
    trigger=CronTrigger(day_of_week='mon-fri', hour=16, minute=0),
    id='daily_stock_update',
    name='每日股票数据更新'
)
```

**常用Cron表达式示例**:

```python
# 每个交易日16:00执行
CronTrigger(day_of_week='mon-fri', hour=16, minute=0)

# 每小时执行一次（测试用）
CronTrigger(minute=0)

# 每天9:30开盘时执行
CronTrigger(day_of_week='mon-fri', hour=9, minute=30)

# 每30分钟执行一次
CronTrigger(minute='0,30')
```

---

## 📊 输出示例

### 控制台日志

```
======================================================================
🚀 开始执行每日股票数据增量更新
📅 更新时间: 2025-01-15 16:00:00
🔧 复权类型: qfq
🔧 并发线程: 5
🔧 删除旧数据: False
======================================================================
正在从数据库获取所有股票代码...
✅ 获取到 5000 只股票代码
开始批量更新 5000 只股票数据...
并发线程数: 5, 请求间隔: 0.5秒
📊 进度: 10/5000 (0.2%) | 成功: 10 | 失败: 0 | 预计剩余: 2500秒
📊 进度: 20/5000 (0.4%) | 成功: 20 | 失败: 0 | 预计剩余: 2480秒
...
📊 进度: 5000/5000 (100.0%) | 成功: 4985 | 失败: 15 | 预计剩余: 0秒
======================================================================
📊 每日股票数据更新报告
======================================================================
总股票数:     5000
成功更新:     4985 ✅
更新失败:     15 ❌
耗时:         2500.50 秒
平均速度:     0.50 秒/股
成功率:       99.7%

失败的股票示例（前20个）:
  1. 600001
  2. 600002
  ...
======================================================================
⚠️  有 15 只股票更新失败，请检查日志
📝 更新日志已保存到: quant/logs/daily_update_log.txt
```

### 日志文件

位置: `quant/logs/daily_update_log.txt`

```
======================================================================
更新时间: 2025-01-15 16:00:00
总股票数: 5000
成功: 4985
失败: 15
耗时: 2500.50秒
成功率: 99.7%
失败股票: 600001, 600002, 600003, ...
======================================================================
```

---

## ⚙️ 性能优化建议

### 1. 调整并发线程数

```python
# 网络带宽充足，可以适当增加并发
updater = DailyStockDataUpdater(max_workers=10)

# 网络较慢或API限流严格，减少并发
updater = DailyStockDataUpdater(max_workers=3)
```

**建议范围**: 3-10个线程

### 2. 调整请求间隔

```python
# API限流宽松，可以减少间隔
updater = DailyStockDataUpdater(delay_between_requests=0.2)

# API限流严格，增加间隔
updater = DailyStockDataUpdater(delay_between_requests=1.0)
```

**建议范围**: 0.2-1.0秒

### 3. 估算更新时间

```
总时间 ≈ 股票数量 × 请求间隔 / 并发线程数

例如：
5000只股票 × 0.5秒 / 5线程 = 500秒 ≈ 8.3分钟
```

---

## 🔍 故障排查

### 问题1: 数据库中没有股票数据

**现象**: 提示"数据库中无股票数据"

**解决**:
```python
# 先执行一次全量保存
from quant.entity.script.stock_data_save_script import stock_name_and_save
stock_name_and_save(reBuild=True)
```

### 问题2: 大量股票更新失败

**可能原因**:
1. API限流
2. 网络连接问题
3. 并发数过高

**解决方案**:
```python
# 降低并发数，增加请求间隔
updater = DailyStockDataUpdater(
    max_workers=3,
    delay_between_requests=1.0
)
```

### 问题3: 更新速度太慢

**解决方案**:
```python
# 增加并发数，减少请求间隔
updater = DailyStockDataUpdater(
    max_workers=10,
    delay_between_requests=0.2
)
```

### 问题4: 内存占用过高

**原因**: 并发线程过多

**解决方案**:
```python
# 减少并发数
updater = DailyStockDataUpdater(max_workers=3)
```

---

## 📝 最佳实践

### 1. 首次初始化

```bash
# 第1步：保存所有股票名称
python -c "from quant.entity.script.stock_data_save_script import stock_name_and_save; stock_name_and_save(reBuild=True)"

# 第2步：测试模式验证（10只股票）
python quant/entity/script/daily_stock_updater.py --test

# 第3步：小批量测试（100只股票）
python quant/entity/script/daily_stock_updater.py --test --test-count 100

# 第4步：全量更新
python quant/entity/script/daily_stock_updater.py
```

### 2. 日常更新

```bash
# 方式1：手动执行
python quant/entity/script/daily_stock_updater.py

# 方式2：定时任务（推荐）
python quant/entity/script/scheduler.py
```

### 3. 监控和告警

创建监控脚本 `monitor_update.py`:

```python
import os
from datetime import datetime, timedelta

def check_update_status():
    """检查最近一次更新状态"""
    log_file = "quant/logs/daily_update_log.txt"
    
    if not os.path.exists(log_file):
        print("❌ 未找到更新日志文件")
        return False
    
    # 读取最后一行
    with open(log_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        last_line = lines[-1] if lines else ""
    
    # 检查是否有最近的更新记录
    # 这里可以根据实际情况定制检查逻辑
    print(f"最近一次更新: {last_line}")
    return True

if __name__ == '__main__':
    check_update_status()
```

---

## 🎯 使用场景

### 场景1: 个人量化研究

```bash
# 每周更新一次即可
python quant/entity/script/daily_stock_updater.py --workers 3 --delay 1.0
```

### 场景2: 生产环境部署

```bash
# 使用定时任务，每日收盘后自动更新
python quant/entity/script/scheduler.py

# 或使用系统cron（Linux）
# crontab -e
# 0 16 * * 1-5 cd /path/to/akshare && python quant/entity/script/daily_stock_updater.py
```

### 场景3: 实时数据监控

```python
# 高频更新（每30分钟）
from quant.entity.script.daily_stock_updater import DailyStockDataUpdater

updater = DailyStockDataUpdater(
    max_workers=10,
    delay_between_requests=0.2
)

# 只更新关注的股票
focus_stocks = ['601398', '600036', '000001']
for symbol in focus_stocks:
    updater.update_single_stock(symbol)
```

---

## 📚 相关文档

- [stock_data_save_script.py](stock_data_save_script.py) - 基础数据保存脚本
- [STOCK_DATA_SCRIPT_TEST_REPORT.md](../../../STOCK_DATA_SCRIPT_TEST_REPORT.md) - 测试报告
- [quant/README_QUANT.md](../../README_QUANT.md) - 量化模块说明

---

## 💡 常见问题

### Q1: 如何只更新特定板块的股票？

**A**: 修改 `get_all_stock_symbols()` 方法，添加过滤条件：

```python
def get_filtered_symbols(self, market: str = "sh"):
    """获取特定市场的股票"""
    df = get_mysql_data_to_df(orm_class=StockNameEntity)
    # 过滤上海市场股票
    symbols = df[df['symbol'].str.startswith(market)]['symbol'].tolist()
    return symbols
```

### Q2: 如何实现断点续传？

**A**: 当前版本已自动跳过已更新的股票（增量更新特性）。如需更精细控制，可以：

```python
# 记录已处理的股票
processed_symbols = set()

for symbol in symbols:
    if symbol in processed_symbols:
        continue
    updater.update_single_stock(symbol)
    processed_symbols.add(symbol)
```

### Q3: 如何发送更新完成通知？

**A**: 在 `run()` 方法末尾添加通知逻辑：

```python
import smtplib
from email.mime.text import MIMEText

def send_notification(self, report: dict):
    """发送邮件通知"""
    msg = MIMEText(f"更新完成:\n成功: {report['success']}\n失败: {report['failed']}")
    msg['Subject'] = '股票数据更新完成'
    msg['From'] = 'sender@example.com'
    msg['To'] = 'receiver@example.com'
    
    with smtplib.SMTP('smtp.example.com') as server:
        server.send_message(msg)
```

---

## ✨ 总结

本模块提供了**完整、高效、可靠**的每日股票数据增量更新方案：

- ✅ **简单易用**: 一行命令即可启动
- ✅ **高性能**: 支持并发处理，速度快
- ✅ **高可靠**: 完善的错误处理和日志记录
- ✅ **可扩展**: 易于定制和扩展功能

**立即开始使用吧！** 🚀
