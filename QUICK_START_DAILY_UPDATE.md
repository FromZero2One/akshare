# 🚀 每日股票数据增量更新 - 快速开始

## ✨ 功能概述

实现了**每日自动从数据库获取所有股票代码，批量拉取当日个股数据并增量保存**的完整解决方案。

### 核心特性

- ✅ **自动化**: 从数据库自动获取股票列表
- ✅ **增量更新**: 只保存最新数据
- ✅ **并发处理**: 多线程并发，速度快
- ✅ **智能限流**: 避免API限流
- ✅ **容错机制**: 单个失败不影响整体
- ✅ **详细日志**: 完整的执行日志和统计
- ✅ **定时任务**: 支持APScheduler自动调度

---

## 📦 安装依赖

```bash
# 基础依赖（已安装）
pip install sqlalchemy pandas pymysql akshare

# 定时任务依赖（可选）
pip install apscheduler
```

---

## 🎯 三种使用方式

### 方式1: 命令行运行（最简单）⭐

```bash
# 进入项目根目录
cd e:\Project\akshare

# 测试模式（推荐首次使用，只处理10只股票）
python quant/entity/script/daily_stock_updater.py --test

# 全量更新（生产环境）
python quant/entity/script/daily_stock_updater.py

# 自定义参数
python quant/entity/script/daily_stock_updater.py \
    --workers 8 \
    --delay 0.3 \
    --adjust qfq
```

#### 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--adjust` | qfq | 复权类型: qfq/hfq/'' |
| `--workers` | 5 | 并发线程数（3-10） |
| `--delay` | 0.5 | 请求间隔（秒） |
| `--isDel` | False | 是否删除旧数据 |
| `--test` | False | 测试模式 |
| `--test-count` | 10 | 测试股票数量 |

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

# 执行更新
updater.run(test_mode=False)  # 生产模式
# updater.run(test_mode=True, test_count=10)  # 测试模式
```

---

### 方式3: 定时任务（全自动）⏰

```bash
# 启动定时任务调度器
python quant/entity/script/scheduler.py
```

**默认配置**:
- 📅 每日更新: 周一至周五 16:00（A股收盘后）
- 🧪 测试任务: 每小时 :30 执行

**修改执行时间**: 编辑 `scheduler.py` 文件

```python
# 交易日16:00执行
CronTrigger(day_of_week='mon-fri', hour=16, minute=0)
```

---

## 📊 运行效果

### 控制台输出

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
======================================================================
📊 每日股票数据更新报告
======================================================================
总股票数:     5000
成功更新:     4985 ✅
更新失败:     15 ❌
耗时:         2500.50 秒
平均速度:     0.50 秒/股
成功率:       99.7%
======================================================================
🎉 所有股票数据更新成功！
```

### 日志文件

位置: `quant/logs/daily_update_log.txt`

---

## 🧪 测试验证

```bash
# 运行完整测试套件
python test_daily_updater.py
```

测试内容:
1. ✅ 基本功能验证
2. ✅ 获取股票代码
3. ✅ 单只股票更新
4. ✅ 批量更新
5. ✅ 完整流程

---

## ⚙️ 性能优化

### 估算更新时间

```
总时间 ≈ 股票数量 × 请求间隔 / 并发线程数

示例:
5000只股票 × 0.5秒 / 5线程 = 500秒 ≈ 8.3分钟
```

### 调优建议

| 场景 | workers | delay | 预计时间 |
|------|---------|-------|----------|
| 保守模式 | 3 | 1.0 | ~28分钟 |
| 标准模式 | 5 | 0.5 | ~8分钟 |
| 快速模式 | 10 | 0.2 | ~2分钟 |

---

## 🔍 故障排查

### 问题1: ModuleNotFoundError: No module named 'quant'

**解决**: 确保在项目根目录运行
```bash
cd e:\Project\akshare
python quant/entity/script/daily_stock_updater.py --test
```

### 问题2: 数据库中无股票数据

**解决**: 先保存股票名称
```python
from quant.entity.script.stock_data_save_script import stock_name_and_save
stock_name_and_save(reBuild=True)
```

### 问题3: 大量股票更新失败

**解决**: 降低并发，增加间隔
```python
updater = DailyStockDataUpdater(
    max_workers=3,
    delay_between_requests=1.0
)
```

---

## 📚 相关文档

- [DAILY_UPDATE_GUIDE.md](quant/entity/script/DAILY_UPDATE_GUIDE.md) - 详细使用指南
- [stock_data_save_script.py](quant/entity/script/stock_data_save_script.py) - 基础数据保存脚本
- [STOCK_DATA_SCRIPT_TEST_REPORT.md](STOCK_DATA_SCRIPT_TEST_REPORT.md) - 测试报告

---

## 💡 使用建议

### 首次使用流程

```bash
# 第1步：保存所有股票名称
python -c "from quant.entity.script.stock_data_save_script import stock_name_and_save; stock_name_and_save(reBuild=True)"

# 第2步：测试模式验证
python quant/entity/script/daily_stock_updater.py --test

# 第3步：小批量测试
python quant/entity/script/daily_stock_updater.py --test --test-count 100

# 第4步：全量更新
python quant/entity/script/daily_stock_updater.py

# 第5步（可选）：设置定时任务
python quant/entity/script/scheduler.py
```

### 日常使用

```bash
# 手动执行
python quant/entity/script/daily_stock_updater.py

# 或自动执行（推荐）
python quant/entity/script/scheduler.py
```

---

## ✨ 总结

现在您可以：

1. ✅ **一键更新**: `python quant/entity/script/daily_stock_updater.py`
2. ✅ **自动调度**: `python quant/entity/script/scheduler.py`
3. ✅ **灵活配置**: 支持多种参数定制
4. ✅ **完整监控**: 详细日志和统计报告

**立即开始使用吧！** 🚀
