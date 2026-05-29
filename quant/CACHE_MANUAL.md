# 量化缓存系统操作手册

> **两层缓存架构** — Redis (L1) → MySQL (L2)

---

## 目录

- [1. 架构概述](#1-架构概述)
- [2. 环境搭建](#2-环境搭建)
- [3. 自动适配机制](#3-自动适配机制)
- [4. 使用指南](#4-使用指南)
- [5. 缓存管理](#5-缓存管理)
- [6. 监控与统计](#6-监控与统计)
- [7. Redis 运维](#7-redis-运维)
- [8. 性能基准](#8-性能基准)
- [9. 故障处理](#9-故障处理)
- [10. 设计原理](#10-设计原理)
- [附录](#附录)

---

## 1. 架构概述

> **当前版本**: `quant/utils/stock_cache.py` — `_create_cache_manager()`
> **数据序列化**: DataFrame → Parquet 压缩字节 → Redis，利用已安装的 `pyarrow`

### 1.1 两层架构

```
  回测策略 / 查询脚本
          │
          ▼
  get_mysql_data_to_df(symbol, use_cache=True)
          │
          ▼
  ╔══════════════════════════╗
  ║      CacheManager        ║
  ║  Redis 命中 → 直接返回   ║
  ║  未命中 → 走 MySQL 兜底   ║
  ╚═══════════╤══════════════╝
              │
     ┌────────┴────────┐
     │                 │
  ┌──▼─────┐    ┌─────▼──────┐
  │ Redis  │    │   MySQL    │
  │ (L1)   │    │  (L2)      │
  │        │    │            │
  │ 内存   │    │ 远程网络    │
  │ ~0.2ms │    │ ~1-4s      │
  │ 热数据  │    │ 兜底/冷数据 │
  └────────┘    └────────────┘
  ↑ 自动回填      ↑ Redis 不可用时
```

### 1.2 层级对比

| 层级 | 存储介质 | 典型延迟 | 作用 |
|------|---------|---------|------|
| **L1: Redis** | 内存 (Docker) | **~0.2 ms** | 热数据，日常查询和批量回测首选 |
| **L2: MySQL** | 远程服务器 | **1~4 s** | 兜底存储，Redis 未命中或不可用时的回退 |

### 1.3 数据流

```
首次查询（缓存未命中）:
  get_mysql_data_to_df('601398')
    → CacheManager.get()
        → Redis.get() → MISS
    → MySQL 查询（1~4 秒）
    → 回填 Redis ✓
    → 返回 DataFrame

后续查询（缓存命中）:
  get_mysql_data_to_df('601398')
    → CacheManager.get()
        → Redis.get() → HIT → 返回（0.2 ms）
```

### 1.4 模块依赖

```
quant/utils/
├── redis_cache.py     # RedisStockDataCache — Redis 缓存实现
├── stock_cache.py     # CacheManager — 缓存管理器 + stock_cache 全局单例
└── db_orm.py          # get_mysql_data_to_df() — 入口函数（自动缓存路由）
```

---

## 2. 环境搭建

### 2.1 前提条件

- Docker 已安装运行
- `redis-py` Python 包

### 2.2 安装 Redis

```bash
# 启动 Redis 容器（密码: 1314）
docker run -d \
  --name redis \
  -p 6379:6379 \
  redis:latest \
  redis-server --requirepass 1314

# 验证
docker ps | grep redis
```

### 2.3 安装 Python 依赖

```bash
pip install redis
```

### 2.4 验证环境

```python
from redis import Redis

r = Redis(host='localhost', port=6379, password='1314')
print(r.ping())  # 应输出 True
```

---

## 3. 自动适配机制

系统启动时**自动检测** Redis 可用性，无需手动配置。

```python
# 导入 stock_cache 时自动检测
from quant.utils.stock_cache import stock_cache

# 成功检测到 Redis 时
#   日志输出: "Redis 可用 ✓ 缓存架构: Redis (L1) → MySQL (L2)"
#   stock_cache.redis = RedisStockDataCache 实例

# Redis 不可用时
#   日志输出: "Redis 不可用，直查 MySQL（无缓存）"
#   stock_cache.redis = None
#   所有查询直走 MySQL，功能完全不受影响
```

### 降级策略

| 场景 | 行为 | 对用户影响 |
|------|------|-----------|
| Redis 正常运行 | Redis 命中 → 返回，未命中 → MySQL → 回填 Redis | 最快性能 |
| Redis 宕机/网络中断 | 自动跳过，直查 MySQL | 功能正常，性能降为 DB 直查 |
| Redis 恢复 | 下次调用自动重新连接 | 自动恢复加速 |

---

## 4. 使用指南

### 4.1 日常查询（零代码变更）

现有代码**无需任何修改**，缓存自动生效：

```python
from quant.utils.db_orm import get_mysql_data_to_df
from quant.entity.StockHistoryDailyInfoEntity import StockHistoryDailyInfoEntity

# 首次 → MySQL 查，自动回填 Redis
df = get_mysql_data_to_df(StockHistoryDailyInfoEntity, symbol='601398', adjust='qfq')
print(len(df))

# 后续 → Redis 命中（< 0.2ms）
df = get_mysql_data_to_df(StockHistoryDailyInfoEntity, symbol='601398', adjust='qfq')
print(len(df))
```

### 4.2 跳过缓存

```python
# 跳过缓存，强制查 MySQL
df = get_mysql_data_to_df(
    StockHistoryDailyInfoEntity,
    symbol='601398',
    adjust='qfq',
    use_cache=False
)
```

### 4.3 直接操作缓存

```python
from quant.utils.stock_cache import stock_cache

# 读取缓存
df = stock_cache.get('601398', 'qfq')

# 写入缓存
stock_cache.put('601398', 'qfq', df)

# 读取 + 自动回填
df = stock_cache.get_or_fetch('601398', 'qfq', fetch_func=my_db_query)

# 强制刷新（重新从 MySQL 拉取并更新 Redis）
df = stock_cache.get_or_fetch('601398', 'qfq', fetch_func=my_db_query, force_refresh=True)
```

### 4.4 单独操作 Redis

```python
rcache = stock_cache.redis  # None 表示 Redis 不可用

if rcache:
    df = rcache.get('601398', 'qfq')
    print(rcache.ping())      # 检查连接
    print(rcache.stats())     # Redis 统计
```

---

## 5. 缓存管理

### 5.1 清除缓存

```python
from quant.utils.stock_cache import stock_cache

# 清除单只股票（单复权类型）
stock_cache.clear('601398', 'qfq')

# 清除单只股票（全部复权类型）
stock_cache.clear('601398')

# 清除全部 Redis 缓存
stock_cache.clear()
```

### 5.2 数据刷新

当 MySQL 中有新数据（如新的交易日），刷新缓存：

```python
# 方式一：清除再查（下次走 MySQL，自动回填 Redis）
stock_cache.clear('601398', 'qfq')
df = get_mysql_data_to_df(StockHistoryDailyInfoEntity, symbol='601398')

# 方式二：强制刷新
df = stock_cache.get_or_fetch(
    '601398', 'qfq',
    fetch_func=lambda: get_mysql_data_to_df(
        StockHistoryDailyInfoEntity, symbol='601398', use_cache=False
    ),
    force_refresh=True
)
```

### 5.3 缓存预热

批量回测前预热所有股票数据到 Redis：

```python
from quant.utils.stock_cache import stock_cache
from quant.utils.db_orm import get_mysql_data_to_df, execute_sql_query
from quant.entity.StockHistoryDailyInfoEntity import StockHistoryDailyInfoEntity

# 获取所有股票代码
symbols_df = execute_sql_query(
    "SELECT DISTINCT symbol FROM stock_history_daily_info_entity"
)
symbols = symbols_df['symbol'].tolist()

# 逐只预热
for i, symbol in enumerate(symbols):
    df = get_mysql_data_to_df(
        StockHistoryDailyInfoEntity, symbol=symbol,
        adjust='qfq', use_cache=True
    )
    if i % 100 == 0:
        print(f"预热进度: {i}/{len(symbols)}")
```

---

## 6. 监控与统计

### 6.1 缓存状态

```python
from quant.utils.stock_cache import stock_cache

stats = stock_cache.stats()
print(stats)
```

输出示例：

```json
{
  "available": true,
  "server_version": "8.8.0",
  "used_memory_mb": 15.2,
  "cache_size_mb": 10.5,
  "uptime_days": 3,
  "hits": 4520,
  "misses": 38
}
```

### 6.2 Redis 专项监控

```python
rcache = stock_cache.redis
if rcache:
    info = rcache.stats()
    print(f"可用: {info['available']}")
    print(f"版本: {info['server_version']}")
    print(f"内存: {info['used_memory_mb']} MB")
    print(f"缓存数据: {info['cache_size_mb']} MB")
    print(f"命中/未命中: {info['hits']}/{info['misses']}")
```

### 6.3 日志监控

```bash
# Redis 缓存操作
grep "Redis 缓存" quant/logs/quant.log

# 缓存命中
grep "Redis 缓存命中" quant/logs/quant.log

# 缓存未命中
grep "Redis 缓存未命中\|未命中" quant/logs/quant.log

# 降级事件
grep "Redis 不可用\|直查 MySQL" quant/logs/quant.log
```

---

## 7. Redis 运维

### 7.1 容器生命周期

```bash
# 查看状态
docker ps | grep redis

# 重启
docker restart redis

# 日志
docker logs redis

# 进入 CLI
docker exec -it redis redis-cli -a 1314

# 监控实时命令
docker exec -it redis redis-cli -a 1314 MONITOR

# 停止、启动
docker stop redis
docker start redis

# 删除并重建
docker rm -f redis
docker run -d --name redis -p 6379:6379 redis:latest redis-server --requirepass 1314
```

### 7.2 内存管理

```bash
# 查看 Redis 内存使用
docker exec redis redis-cli -a 1314 INFO memory

# 限制内存上限（如 4GB）
docker update redis --memory 4g

# 或启动时限制
docker run -d --name redis --memory 4g -p 6379:6379 redis:latest redis-server --requirepass 1314
```

### 7.3 数据清理

```bash
# 通过 Python 清理
python3 -c "
from quant.utils.stock_cache import stock_cache
stock_cache.clear()
"

# 通过 CLI 清理
docker exec redis redis-cli -a 1314 FLUSHDB

# 查看所有缓存 key
docker exec redis redis-cli -a 1314 KEYS 'stock_cache:*'
```

### 7.4 查看 Redis 数据

```bash
# 查看键总数
docker exec redis redis-cli -a 1314 DBSIZE

# 查看具体键大小
docker exec redis redis-cli -a 1314 STRLEN 'stock_cache:601398:qfq:data'

# 查看元数据
docker exec redis redis-cli -a 1314 GET 'stock_cache:601398:qfq:meta'
```

---

## 8. 性能基准

### 8.1 实测数据

| 测试项 | 工商银行 601398 | 贵州茅台 600519 | 平安银行 000001 |
|-------|----------------|----------------|----------------|
| **Redis (L1)** | **~2.0 ms**¹ | **~2.0 ms** | **~2.0 ms** |
| **MySQL (L2)** | **~335 ms** | **~2.4 s** | **~4.0 s** |
| 数据行数 | 4593 | 11568 | 16520 |
| 缓存大小 | 146.9 KB | 259.4 KB | 361.2 KB |

> ¹ 通过 `get_mysql_data_to_df()` 含函数调用开销；`RedisStockDataCache` 直读为 **~0.2 ms**

### 8.2 加速倍率

| 对比 | 加速比 |
|------|-------|
| MySQL → Redis (raw) | **~20,000×** |
| MySQL → Redis (via db_orm) | **~200×** |

### 8.3 全市场估算

| 指标 | MySQL 直查 | Redis 缓存 |
|------|-----------|-----------|
| **单次查询** | 1~4 秒 | **~0.2 ms** (raw) / **~2 ms** (db_orm) |
| **5000 只（串行预热）** | ~3 小时 | **~2 秒** |
| **全内存预热** | — | **~2 GB** |

### 8.4 自测性能

```bash
python3 << 'PYEOF'
import sys, time
sys.path.insert(0, '.')
from quant.utils.stock_cache import stock_cache
from quant.utils.db_orm import get_mysql_data_to_df
from quant.entity.StockHistoryDailyInfoEntity import StockHistoryDailyInfoEntity

symbol = '601398'
stock_cache.clear(symbol, 'qfq')

# MySQL (L2)
t0 = time.time()
df2 = get_mysql_data_to_df(StockHistoryDailyInfoEntity, symbol=symbol, use_cache=False)
t_mysql = time.time() - t0

# Redis (L1)
t0 = time.time()
df1 = stock_cache.get(symbol, 'qfq')
t_redis = time.time() - t0

print(f"MySQL(L2): {t_mysql*1000:>8.1f} ms")
print(f"Redis(L1): {t_redis*1000:>8.1f} ms  ({t_mysql/t_redis:.0f}x)")

stock_cache.clear()
PYEOF
```

---

## 9. 故障处理

### 9.1 Redis 连接失败

**现象**: 日志输出 `Redis ping 失败` / `Redis 连接不可用`

**原因**: Docker 容器未启动、密码错误、网络不通

**排查步骤**:

```bash
# 1. 检查容器状态
docker ps | grep redis

# 2. 尝试连接
docker exec redis redis-cli -a 1314 PING

# 3. 检查端口
ss -tlnp | grep 6379

# 4. 重启容器
docker restart redis
```

**影响**: 自动降级到直查 MySQL，功能不受影响，仅性能下降。

### 9.2 数据不一致

**现象**: Redis 缓存数据比 MySQL 旧

**原因**: MySQL 有新数据后缓存未刷新

**解决方案**:

```python
# 清除缓存 → 下次自动从 MySQL 获取最新
stock_cache.clear(symbol, 'qfq')
```

### 9.3 Redis 内存不足

**现象**: Redis 写入失败 / 系统 OOM

**原因**: 全市场 5000 只股票的日线数据约 2GB

**解决方案**:

```bash
# 1. 限制 Redis 内存上限
docker update redis --memory 2g

# 2. 定期清理
python3 -c "from quant.utils.stock_cache import stock_cache; stock_cache.clear()"

# 3. 不使用 Redis 时，停止容器即可，系统自动直查 MySQL
```

### 9.4 紧急重置

```python
from quant.utils.stock_cache import stock_cache

stock_cache.clear()
print("Redis 缓存已清空，下次查询自动从 MySQL 回填")
```

---

## 10. 设计原理

### 10.1 为什么用 Parquet 序列化 Redis 数据？

Redis 原生数据结构无法直接存储 DataFrame。采用 Parquet 字节序列化：

- **已有依赖**: `pyarrow` 已安装，无需新增
- **效率**: zstd 压缩，序列化/反序列化 < 1ms
- **体积**: 单只股票 ~147 KB，5000 只 ~2 GB
- **跨平台**: Parquet 是标准列存格式

### 10.2 为什么只有两层？

```
  Redis (内存, ~0.2ms)    ← 热数据，快速读写
    ↓ 未命中
  MySQL (远程, ~1-4s)     ← 兜底，可靠存储
```

- Redis 的 ~0.2ms 延迟已经足够快，不需要中间层
- 磁盘缓存（Parquet）增加复杂度和维护成本，收益有限
- Docker Redis 配置简单，重启自动恢复连接

### 10.3 线程安全性

| 组件 | 保护机制 |
|------|---------|
| `RedisStockDataCache` | Redis 单线程模型，`pipeline()` 保证原子性 |
| `CacheManager` | 无状态委托，天然线程安全 |

---

## 附录

### A. 文件清单

| 文件 | 行数 | 职责 |
|------|------|------|
| `quant/utils/redis_cache.py` | ~364 行 | `RedisStockDataCache` — Redis 缓存实现（序列化/反序列化） |
| `quant/utils/stock_cache.py` | ~298 行 | `CacheManager` 缓存管理器 + `stock_cache` 全局单例 |

> `StockDataCache`（本地 Parquet 缓存类）仍保留在 `stock_cache.py` 中作为参考，**不参与**当前缓存链。

### B. 配置参数

**Redis 连接参数** (`quant/utils/redis_cache.py`)

| 参数 | 默认值 | 说明 |
|------|-------|------|
| `host` | `localhost` | Redis 主机 |
| `port` | `6379` | Redis 端口 |
| `db` | `0` | 数据库编号 |
| `password` | `"1314"` | 密码 |
| `socket_timeout` | `2` | 读写超时（秒） |
| `socket_connect_timeout` | `2` | 连接超时（秒） |
| `compression` | `"zstd"` | Parquet 压缩算法 |

### C. 日志参考

```
# Redis 正常运行的日志
INFO - stock_cache.py:287 - Redis 可用 ✓ 缓存架构: Redis (L1) → MySQL (L2)
INFO - redis_cache.py:218 - Redis 缓存写入: 601398(qfq) 4593 行, 146.9 KB

# Redis 不可用的降级日志
INFO - stock_cache.py:290 - Redis 不可用，直查 MySQL（无缓存）
WARNING - redis_cache.py:100 - Redis ping 失败: ...

# 缓存命中
DEBUG - redis_cache.py:191 - Redis 缓存命中: 601398(qfq) 4593 行, 146.9 KB

# 缓存未命中
DEBUG - redis_cache.py:187 - Redis 缓存未命中: 601398(qfq)

# 清除缓存
INFO - redis_cache.py:295 - Redis 清除全部缓存
```

### D. Docker Compose 配置

如需持久化 Redis 数据：

```yaml
# docker-compose.yml
version: '3.8'
services:
  redis:
    image: redis:latest
    container_name: redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: redis-server --requirepass 1314 --appendonly yes
    restart: unless-stopped
    mem_limit: 4g

volumes:
  redis-data:
```

启动：

```bash
docker-compose up -d
```
