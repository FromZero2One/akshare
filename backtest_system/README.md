# 个人量化回测系统

一个轻量级、模块化的个人量化交易回测系统，支持多种策略、并行执行、结果管理和可视化分析。

## 特性

- **数据库优先**：MySQL 数据库作为首选数据源，避免重复网络请求，大幅提升数据获取速度
- **多数据源降级**：数据库 → 缓存 → 东方财富 → 腾讯证券，自动降级保障数据可用性
- **模块化设计**：数据获取、策略执行、结果管理完全分离
- **多策略支持**：支持双均线、布林带、MACD等多种技术指标策略
- **并行优化**：多线程并发执行，大幅提升回测效率
- **智能缓存**：pickle 文件缓存机制，减少重复计算
- **自动入库**：API 拉取的数据自动保存到数据库，下次直接使用
- **结果管理**：支持 JSON/Parquet/CSV 多格式保存，提供详细的性能分析
- **配置驱动**：通过配置文件管理所有参数，易于使用和维护

## 项目结构

```
backtest_system/
├── config/                    # 配置文件
│   ├── backtest.ini          # 回测基础配置（含数据库配置）
│   ├── strategies.ini        # 策略参数配置
│   └── cache.ini             # 缓存配置
├── core/                     # 核心模块
│   ├── data_fetcher.py       # 数据获取器（支持数据库+多源降级）
│   ├── strategy_executor.py  # 策略执行器
│   └── result_manager.py     # 结果管理器
├── strategies/               # 策略模块
│   ├── base.py              # 策略基类
│   ├── sma_cross.py         # 双均线策略
│   └── custom_strategy.py   # 自定义策略模板
├── data/                    # 数据目录
│   ├── cache/               # 数据缓存（pickle）
│   └── logs/               # 日志文件
├── utils/                   # 工具模块
├── main.py                 # 主程序
└── README.md               # 说明文档
```

### 关键依赖模块

本系统依赖项目根目录下的 `quant` 模块实现数据库功能：

```
akshare/                     # 项目根目录
├── quant/                   # 量化工具模块（数据库核心依赖）
│   ├── utils/
│   │   ├── db_orm.py       # ORM 数据库查询/保存
│   │   ├── db_connection.py # 数据库连接管理（单例+连接池）
│   │   └── db_config.py    # 数据库配置
│   ├── entity/
│   │   └── StockHistoryDailyInfoEntity.py  # 股票日线数据 ORM 实体
│   │   └── script/
│   │       └── stock_data_save_script.py   # 多源降级参考脚本
│   └── strategy/
│       └── sma/
│           └── SmaStrategyScript.py        # 数据库优先参考策略
├── .env                     # 数据库密码配置
└── backtest_system/         # 回测系统（本目录）
```

## 安装依赖

### 基础依赖

```bash
pip install akshare pandas numpy matplotlib seaborn
```

### 数据库依赖（可选）

如需启用 MySQL 数据库功能，还需安装：

```bash
pip install sqlalchemy pymysql
```

> 注：如果未安装数据库依赖或 `quant` 模块不可用，系统会自动禁用数据库功能，退化为纯 API + 缓存模式。

### 数据库配置

1. 在项目根目录的 `.env` 文件中配置数据库连接信息：

```bash
# 开发环境
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=akshare

# 生产环境
DB_PRO_HOST=your_server_ip
DB_PRO_PORT=3306
DB_PRO_USER=root
DB_PRO_PASSWORD=your_password
DB_PRO_NAME=akshare
```

2. 数据库环境切换：修改 `quant/utils/db_connection.py` 中的 `use_pro` 参数

```python
# 使用生产环境
db_manager = DatabaseManager(use_pro=True)

# 使用开发环境
db_manager = DatabaseManager(use_pro=False)
```

## 快速开始

### 1. 基本使用

```bash
# 批量回测（默认策略，数据优先从数据库获取）
python main.py --symbols 000001 000002 000003

# 指定策略
python main.py --symbols 000001 --strategies SMACross BollingerBands

# 单只股票回测
python main.py --mode single --symbols 000001 --strategies SMACross

# 指定复权方式和资金
python main.py --symbols 000001 --adjust hfq --capital 200000
```

### 2. 系统信息

```bash
# 查看系统信息（含数据库连接状态）
python main.py --info

# 列出所有策略
python main.py --list-strategies

# 分析回测结果
python main.py --symbols 000001 --analyze
```

### 3. 性能优化

```bash
# 使用更多并发数
python main.py --symbols 000001 000002 000003 --max-workers 8

# 禁用缓存（强制获取最新数据）
python main.py --symbols 000001 --no-cache

# 不保存结果（只测试）
python main.py --symbols 000001 --no-save
```

## 数据获取架构

### 数据源优先级

系统采用**智能数据获取**策略，按以下优先级获取数据：

```
1. MySQL 数据库（优先）  →  直接查询，无需网络请求
2. 本地 pickle 缓存      →  文件级缓存，7天有效期
3. 东方财富 API          →  AKShare 主要数据源 (stock_zh_a_hist)
4. 腾讯证券 API          →  备用数据源 (stock_zh_a_hist_tx)
```

### 工作流程

```
fetch_data(symbol, adjust, source="auto")
    │
    ├─ source="auto"（默认，智能模式）
    │   ├─ 1. 尝试数据库 → 有数据则直接返回
    │   ├─ 2. 尝试缓存   → 有缓存则直接返回
    │   ├─ 3. API 降级获取 → 东方财富 → 腾讯证券（每个源3次重试）
    │   └─ 4. 保存到缓存 + 保存到数据库（供下次使用）
    │
    ├─ source="mysql"（仅数据库）
    │   └─ 直接查询数据库，失败则返回空
    │
    ├─ source="akshare"（仅API，跳过数据库）
    │   └─ API 降级获取 + 保存缓存 + 保存数据库
    │
    └─ source="tushare"/"local"（预留接口）
```

### 数据库集成原理

参考 `quant` 模块的数据库逻辑：

- **查询**：使用 `db_orm.get_mysql_data_to_df()` 通过 ORM 实体类查询数据库
- **保存**：使用 `ak.stock_zh_a_hist_orm()` 获取 ORM 格式数据，再通过 `db_orm.save_to_mysql_orm_incremental()` 增量保存
- **去重**：数据库数据自动 `drop_duplicates(subset=['date'])` 处理重复记录
- **降级**：数据库不可用时自动降级到缓存/API 模式

### 腾讯证券代码转换

使用腾讯证券接口时，股票代码需添加市场前缀：

| 原始代码 | 市场前缀 | 转换后 |
|---------|---------|--------|
| 600519  | sh（沪市） | sh600519 |
| 000001  | sz（深市） | sz000001 |
| 430001  | bj（京市） | bj430001 |

## 配置说明

### backtest.ini

```ini
[backtest]
initial_capital = 100000    # 初始资金
commission_rate = 0.0005    # 手续费率
default_adjust = qfq        # 默认复权方式（qfq=前复权, hfq=后复权）
default_strategy = SMACross # 默认策略

[data]
cache_enabled = true        # 启用缓存
cache_expiry_days = 7       # 缓存过期天数
data_source = auto          # 数据源（auto=智能选择, akshare=仅API）
max_workers = 4             # 最大并发数

# 数据库配置
db_enabled = true           # 启用数据库（需要 quant 模块）
db_save_enabled = true      # 自动保存 API 数据到数据库

[result]
save_format = json          # 保存格式（json, parquet, csv）
auto_save = true            # 自动保存
summary_report = true       # 生成汇总报告
```

### strategies.ini

```ini
[SMACross]
fast_ma = 7               # 快速均线周期
slow_ma = 30              # 慢速均线周期
stop_loss = 0.05          # 止损比例
take_profit = 0.15        # 止盈比例
max_position = 0.8        # 最大仓位

[SMACrossEnhanced]
fast_ma = 7
slow_ma = 30
stop_loss = 0.05
take_profit = 0.15
max_position = 0.8
volume_filter = true      # 启用成交量过滤
trend_filter = true       # 启用趋势过滤
```

## 策略开发

### 创建自定义策略

1. 继承 `BaseStrategy` 类：
```python
from strategies.base import BaseStrategy

class MyCustomStrategy(BaseStrategy):
    def __init__(self, param1, param2):
        super().__init__("我的自定义策略")
        self.params = {'param1': param1, 'param2': param2}
    
    def generate_signals(self, data):
        # 实现信号生成逻辑
        signals = pd.DataFrame(index=data.index, columns=['signal'], data=0)
        # ... 你的策略逻辑
        return signals
    
    def calculate_metrics(self, signals, prices):
        # 实现指标计算逻辑
        metrics = {}
        # ... 你的指标计算
        return metrics
```

2. 注册并使用：
```python
# 在 main.py 中注册
my_strategy = MyCustomStrategy(param1=10, param2=20)
system.strategy_executor.register_strategy(my_strategy)

# 命令行使用
python main.py --symbols 000001 --strategies MyCustomStrategy
```

### 策略参数配置

在 `strategies.ini` 中添加策略配置：
```ini
[MyCustomStrategy]
param1 = 10
param2 = 20
```

## 结果分析

系统提供多种结果分析功能：

### 自动报告
- 汇总统计
- 策略对比
- 股票表现
- 风险指标

### 可视化图表
- 收益率分布
- 风险收益散点图
- 回撤分析
- 交易统计

### 导出功能
```bash
# 导出为Excel
python main.py --symbols 000001 --export excel

# 导出为CSV
python main.py --symbols 000001 --export csv

# 导出为JSON
python main.py --symbols 000001 --export json
```

## 性能优化

### 并发执行
- 多线程并行处理
- 可配置并发数
- 批量任务调度

### 数据库加速
- 数据库优先避免重复网络请求
- 连接池管理（pool_size=10, max_overflow=20）
- 增量保存避免全量覆盖
- 自动去重处理

### 缓存机制
- 数据缓存避免重复下载
- 结果缓存提高查询效率
- 自动清理过期缓存（7天）

### 内存管理
- 大数据集分批处理
- 内存使用监控
- 垃圾回收优化

## 故障排除

### 常见问题

1. **数据库连接失败**
   ```bash
   # 检查数据库状态
   python main.py --info
   
   # 检查 .env 配置
   cat ../.env
   
   # 检查数据库环境选择（开发/生产）
   # 修改 quant/utils/db_connection.py 中的 use_pro 参数
   ```

2. **数据获取失败**
   ```bash
   # 禁用缓存强制重新获取
   python main.py --symbols 000001 --no-cache
   
   # 查看日志
   tail -f data/logs/backtest.log
   ```

3. **quant 模块导入失败**
   - 确认 `quant` 目录位于项目根目录下
   - 确认 `quant/__init__.py` 存在
   - 系统会自动禁用数据库功能，退化为 API + 缓存模式

4. **策略执行错误**
   ```bash
   # 列出可用策略
   python main.py --list-strategies
   
   # 检查策略配置
   cat config/strategies.ini
   ```

5. **内存不足**
   ```bash
   # 减少并发数
   python main.py --symbols 000001 --max-workers 2
   
   # 分批执行
   python main.py --symbols 000001 000002 000003 --mode sequential
   ```

### 日志配置
```ini
[logging]
log_level = DEBUG     # 调试级别
log_file = data/logs/backtest.log
log_format = %(asctime)s - %(name)s - %(levelname)s - %(message)s
```

### 数据库降级说明

当数据库不可用时，系统自动降级处理：

| 场景 | 行为 |
|------|------|
| quant 模块缺失 | DB_AVAILABLE=False，禁用所有数据库功能 |
| 数据库连接失败 | 跳过数据库，尝试缓存 → API |
| 数据库中无数据 | 跳过数据库，尝试缓存 → API |
| API 数据获取成功 | 自动保存到数据库（如 db_save_enabled=True） |
| 所有数据源失败 | 返回空 DataFrame，回测终止 |

## 最佳实践

1. **数据准备**
   - 启用数据库功能（db_enabled=true）
   - 启用自动入库（db_save_enabled=true），API 数据自动保存
   - 启用缓存避免重复下载
   - 选择合适的复权方式（qfq=前复权推荐）

2. **策略设计**
   - 从简单策略开始
   - 充分测试参数敏感性
   - 考虑风险管理

3. **性能优化**
   - 合理设置并发数（建议4-8）
   - 使用数据缓存
   - 定期清理旧结果

4. **结果分析**
   - 关注多个指标（收益、风险、夏普比率等）
   - 比较不同策略表现
   - 保存历史结果以便回溯

## 支持

如有问题或建议，请：
1. 查看日志文件 (`data/logs/backtest.log`)
2. 检查配置文件 (`config/backtest.ini`)
3. 运行 `python main.py --info` 查看系统状态
4. 提交 Issue 反馈问题

## 许可证

本项目采用 MIT 许可证，详见 LICENSE 文件。