# 量化模块使用指南

## 📚 目录

- [快速开始](#快速开始)
- [数据库操作](#数据库操作)
- [日志系统](#日志系统)
- [性能监控](#性能监控)
- [缓存机制](#缓存机制)
- [策略开发](#策略开发)
- [最佳实践](#最佳实践)

---

## 快速开始

### 1. 安装依赖

```bash
pip install sqlalchemy>=2.0.0 pandas>=2.0.0 pymysql>=1.0.0 backtrader>=1.9.76 python-dotenv>=1.0.0
```

### 2. 配置数据库

复制 `.env.example` 为 `.env` 并填写配置：

```bash
cp .env.example .env
```

编辑 `.env`:
```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=akshare
```

### 3. 基本使用

```python
import akshare as ak
from quant.utils.db_orm import save_to_mysql_orm, get_mysql_data_to_df
from quant.entity.StockHistoryDailyInfoEntity import StockHistoryDailyInfoEntity

# 获取股票数据
df = ak.stock_zh_a_hist_orm(symbol="601398", period="daily", adjust="qfq")

# 保存到数据库
save_to_mysql_orm(df=df, orm_class=StockHistoryDailyInfoEntity, reBuild=False)

# 从数据库读取
data = get_mysql_data_to_df(
    orm_class=StockHistoryDailyInfoEntity, 
    symbol="601398",
    adjust="qfq"
)
print(data.head())
```

---

## 数据库操作

### ORM 方式（推荐）

#### 保存数据

```python
from quant.utils.db_orm import save_to_mysql_orm, save_to_mysql_orm_incremental
from quant.entity.StockHistoryDailyInfoEntity import StockHistoryDailyInfoEntity

# 全量保存（重建表）
save_to_mysql_orm(df=data, orm_class=StockHistoryDailyInfoEntity, reBuild=True)

# 增量保存
save_to_mysql_orm_incremental(
    df=data, 
    orm_class=StockHistoryDailyInfoEntity, 
    symbol="601398",
    isDel=False  # False=追加，True=删除后插入
)
```

#### 查询数据

```python
from quant.utils.db_orm import get_mysql_data_to_df
from quant.entity.StockHistoryDailyInfoEntity import StockHistoryDailyInfoEntity

# 查询特定股票
df = get_mysql_data_to_df(
    orm_class=StockHistoryDailyInfoEntity,
    symbol="601398",
    adjust="qfq"
)

# 查询所有数据
df = get_mysql_data_to_df(
    table_name="stock_history_daily_info_entity"
)
```

### 直接使用连接管理器

```python
from quant.utils.db_connection import get_session
from sqlalchemy import text

with get_session() as session:
    result = session.execute(text("SELECT * FROM stock_history_daily_info_entity LIMIT 10"))
    rows = result.fetchall()
    for row in rows:
        print(row)
```

---

## 日志系统

### 基本使用

```python
from quant.utils.logger_config import get_quant_logger

logger = get_quant_logger()

logger.debug("调试信息")
logger.info("普通信息")
logger.warning("警告信息")
logger.error("错误信息")
```

### 自定义日志文件

```python
logger = get_quant_logger(
    level=logging.DEBUG,
    log_file="/path/to/custom.log"
)
```

### 日志格式

默认格式：
```
2025-01-15 10:30:45,123 - quant - INFO - db_orm.py:125 - 成功保存 100 条记录到表 stock_history_daily_info_entity
```

---

## 性能监控

### 使用装饰器监控函数

```python
from quant.utils.performance_monitor import performance_monitor, monitored_operation

@performance_monitor
def complex_calculation():
    # 复杂计算
    result = sum(range(1000000))
    return result

@monitored_operation("数据库查询")
def query_database():
    # 数据库查询
    pass
```

### 使用上下文管理器计时

```python
from quant.utils.performance_monitor import Timer

with Timer("数据加载"):
    data = load_large_dataset()

with Timer("模型训练"):
    model.train(data)
```

### 查看性能统计

```python
from quant.utils.performance_monitor import perf_stats

# 打印性能报告
perf_stats.print_report()

# 获取特定操作的统计
stats = perf_stats.get_summary("数据库查询")
print(f"平均耗时: {stats['average_time']:.3f}秒")
```

---

## 缓存机制

缓存系统采用两层架构：**Redis (L1) → MySQL (L2)**。

详细操作手册请见 [CACHE_MANUAL.md](CACHE_MANUAL.md)。

### 快速概览

```python
from quant.utils.db_orm import get_mysql_data_to_df
from quant.entity.StockHistoryDailyInfoEntity import StockHistoryDailyInfoEntity

# 首次调用：MySQL 查询，自动回填 Redis
df = get_mysql_data_to_df(StockHistoryDailyInfoEntity, symbol='601398', adjust='qfq')

# 后续调用：Redis 缓存命中（~0.2ms），自动加速
df = get_mysql_data_to_df(StockHistoryDailyInfoEntity, symbol='601398', adjust='qfq')
```

| 层级 | 介质 | 延迟 | 加速比 |
|------|------|------|--------|
| Redis (L1) | 内存 | ~0.2 ms | **×20,000** |
| MySQL (L2) | 远程 | ~1-4 s | ×1 |

### 缓存管理

```python
from quant.utils.stock_cache import stock_cache

# 查看缓存统计
stats = stock_cache.stats()
print(stats)

# 清除单只股票缓存
stock_cache.clear('601398', 'qfq')

# 清除全部缓存
stock_cache.clear()

# 跳过缓存，强制查 MySQL
df = get_mysql_data_to_df(
    StockHistoryDailyInfoEntity, symbol='601398',
    use_cache=False
)
```

更多操作细节 → **[CACHE_MANUAL.md](CACHE_MANUAL.md)**

---

## 策略开发

### SMA 双均线策略示例

```python
from quant.strategy.sma.SmaStrategyScript import strategy_back_trader
from quant.strategy.sma.strategy.SmaCross import SmaCross

# 运行回测
strategy_back_trader(
    symbol="601398",
    stock_name="工商银行",
    adjust="qfq",
    fromdate=datetime(2020, 1, 1),
    todate=datetime.now(),
    startcash=100000,
    commission=0.0005,
    strategy=SmaCross,
    printlog=False,
    is_plot=True,
    is_save_result=True
)
```

### 自定义策略

```python
import backtrader as bt

class MyCustomStrategy(bt.Strategy):
    strategy_name = '我的自定义策略'
    
    params = (
        ('period', 20),
        ('printlog', False),
    )
    
    def __init__(self):
        self.sma = bt.indicators.SimpleMovingAverage(
            self.datas[0].close, 
            period=self.params.period
        )
    
    def next(self):
        if not self.position:
            if self.data.close[0] > self.sma[0]:
                self.buy()
        else:
            if self.data.close[0] < self.sma[0]:
                self.sell()
```

---

## 最佳实践

### 1. 数据验证

```python
import pandas as pd

# 始终验证 DataFrame
if df is None or df.empty:
    logger.error("数据为空，无法保存")
    return

# 检查必要列
required_columns = ['date', 'open', 'close', 'high', 'low', 'volume']
missing = set(required_columns) - set(df.columns)
if missing:
    logger.error(f"缺少必要列: {missing}")
    return
```

### 2. 异常处理

```python
try:
    result = get_mysql_data_to_df(orm_class=MyEntity, symbol="601398")
except Exception as e:
    logger.error(f"查询失败: {e}", exc_info=True)
    # 降级处理
    result = pd.DataFrame()
```

### 3. 资源管理

```python
# ✅ 推荐：使用上下文管理器
with get_session() as session:
    session.query(...)

# ❌ 不推荐：手动管理
session = Session()
try:
    session.query(...)
    session.commit()
finally:
    session.close()
```

### 4. 性能优化

```python
# 使用缓存减少重复查询
@cache_result(ttl=300)
def get_frequently_used_data():
    return expensive_query()

# 监控慢查询
@monitored_operation("复杂查询")
def complex_query():
    return db.query(...)
```

### 5. 日志级别选择

```python
# DEBUG: 详细的调试信息（开发环境）
logger.debug(f"查询参数: symbol={symbol}, adjust={adjust}")

# INFO: 一般信息（生产环境默认）
logger.info("数据保存成功")

# WARNING: 警告信息
logger.warning("查询结果为空")

# ERROR: 错误信息
logger.error("数据库连接失败", exc_info=True)
```

---

## 常见问题

### Q1: 如何切换开发/生产环境？

```python
# 方法1: 修改环境变量
export DB_PRO_HOST=production-server.com

# 方法2: 代码中指定
from quant.utils.db_connection import DatabaseManager
db_manager = DatabaseManager(use_pro=True)
```

### Q2: 如何清理过期缓存？

```python
# 自动清理（LRU + TTL）
# 缓存会在访问时检查是否过期，过期自动删除

# 手动清理
from quant.utils.cache import clear_all_cache
clear_all_cache()
```

### Q3: 如何查看当前连接池状态？

```python
from quant.utils.db_connection import get_engine

engine = get_engine()
pool = engine.pool
print(f"当前连接数: {pool.checkedin()}")
print(f"使用中连接数: {pool.checkedout()}")
print(f"溢出连接数: {pool.overflow()}")
```

### Q4: 日志文件在哪里？

默认位置：`quant/logs/quant.log`

可以通过 `get_quant_logger(log_file='custom.log')` 自定义。

---

## 更多资源

- [策略对比](strategy/strategy_comparator.py) - 策略性能对比工具
- [参数优化](strategy/optimize_parameters.py) - 策略参数优化脚本
- [快速验证](quick_start.py) - 模块安装和功能验证

---

## 技术支持

如有问题，请查看：
1. 日志文件：`quant/logs/quant.log`
2. 运行验证：`python quant/quick_start.py`
3. 查阅文档：上述各章节
