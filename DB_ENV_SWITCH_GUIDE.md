# 数据库环境切换指南

## 📋 概述

本项目支持**开发环境**和**生产环境**两种数据库配置，可以方便地在两者之间切换。

### 当前默认配置

✅ **已切换到生产环境数据库**

- **主机**: 8.137.104.120
- **端口**: 3306
- **用户**: root
- **数据库**: akshare

---

## 🔄 切换方法

### 方法1: 使用切换脚本（推荐）⭐

```bash
# 检查当前环境
python switch_db_env.py --to check

# 切换到生产环境
python switch_db_env.py --to pro

# 切换到开发环境
python switch_db_env.py --to dev
```

### 方法2: 手动修改配置文件

编辑 `quant/utils/db_connection.py` 文件：

```python
# 第113行：修改 use_pro 参数

# 生产环境
db_manager = DatabaseManager(use_pro=True, echo_sql=False)

# 开发环境
db_manager = DatabaseManager(use_pro=False, echo_sql=False)
```

**注意**: 修改后需要重启Python进程才能生效。

### 方法3: 使用环境变量（最灵活）

复制 `.env.example` 为 `.env` 并配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# 生产环境配置
DB_PRO_HOST=8.137.104.120
DB_PRO_PORT=3306
DB_PRO_USER=root
DB_PRO_PASSWORD=your_password
DB_PRO_NAME=akshare
```

---

## 📊 环境对比

| 特性 | 开发环境 | 生产环境 |
|------|---------|---------|
| **主机** | localhost | 8.137.104.120 |
| **用途** | 本地测试、开发 | 正式运行、生产数据 |
| **数据安全性** | 低 | 高 |
| **性能** | 取决于本地机器 | 云服务器，稳定 |
| **适用场景** | 功能开发、调试 | 日常数据更新、回测 |

---

## ⚙️ 配置优先级

配置加载的优先级顺序（从高到低）：

1. **环境变量** (`.env` 文件或系统环境变量)
2. **代码配置** (`db_config.py` 中的默认值)

示例：

```python
# db_config.py 中的逻辑
DB_CONFIG_PRO = {
    'host': get_env_var('DB_PRO_HOST', '8.137.104.120'),  # 环境变量优先
    'port': int(get_env_var('DB_PRO_PORT', '3306')),
    'user': get_env_var('DB_PRO_USER', 'root'),
    'password': get_env_var('DB_PRO_PASSWORD', 'root1314pwd'),
    'database': get_env_var('DB_PRO_NAME', 'akshare')
}
```

---

## 🔍 验证配置

### 方法1: 使用切换脚本

```bash
python switch_db_env.py --to check
```

输出示例：
```
======================================================================
📊 当前数据库环境
======================================================================
✅ 当前环境: 生产环境
   - 主机: 8.137.104.120
   - 端口: 3306
   - 数据库: akshare
```

### 方法2: Python代码验证

```python
from quant.utils.db_connection import db_manager
from quant.utils.db_config import DB_CONFIG, DB_CONFIG_PRO

# 查看当前使用的配置
print(f"Host: {db_manager.engine.url.host}")
print(f"Database: {db_manager.engine.url.database}")
```

### 方法3: 运行测试

```bash
# 测试数据库连接
python -c "from quant.utils.db_connection import get_engine; engine = get_engine(); print(f'✅ 连接成功: {engine.url}')"
```

---

## 💡 使用建议

### 开发阶段

```bash
# 1. 切换到开发环境
python switch_db_env.py --to dev

# 2. 在本地进行测试
python quant/entity/script/daily_stock_updater.py --test
```

### 生产部署

```bash
# 1. 切换到生产环境
python switch_db_env.py --to pro

# 2. 配置环境变量（推荐）
cp .env.example .env
# 编辑 .env 填写真实密码

# 3. 启动定时任务
python quant/entity/script/scheduler.py
```

### 安全建议

1. **不要将 `.env` 文件提交到Git**
   ```bash
   # .gitignore 中已包含
   .env
   ```

2. **生产环境密码通过环境变量设置**
   ```bash
   # Linux/Mac
   export DB_PRO_PASSWORD=your_secure_password
   
   # Windows PowerShell
   $env:DB_PRO_PASSWORD="your_secure_password"
   ```

3. **定期更换密码**
   - 开发环境：可选
   - 生产环境：**必须**

---

## 🔧 常见问题

### Q1: 切换后配置不生效？

**A**: 需要重启Python进程。如果是定时任务，需要重启调度器。

```bash
# 重启定时任务
pkill -f scheduler.py
python quant/entity/script/scheduler.py
```

### Q2: 如何确认当前使用的是哪个数据库？

**A**: 运行检查命令

```bash
python switch_db_env.py --to check
```

或者在代码中打印：

```python
from quant.utils.db_connection import db_manager
print(db_manager.engine.url)
# 输出: mysql+pymysql://root:***@8.137.104.120:3306/akshare
```

### Q3: 生产库连接失败怎么办？

**可能原因**:
1. 网络问题
2. 防火墙限制
3. 数据库服务未启动
4. 密码错误

**解决方案**:

```bash
# 1. 检查网络连接
ping 8.137.104.120

# 2. 检查端口是否开放
telnet 8.137.104.120 3306

# 3. 临时切换回开发环境测试
python switch_db_env.py --to dev
python quant/entity/script/daily_stock_updater.py --test
```

### Q4: 如何在代码中动态切换？

**A**: 创建新的DatabaseManager实例

```python
from quant.utils.db_connection import DatabaseManager

# 创建生产环境管理器
pro_manager = DatabaseManager(use_pro=True)

# 创建开发环境管理器
dev_manager = DatabaseManager(use_pro=False)

# 使用指定的管理器
with pro_manager.get_session() as session:
    # 操作生产数据库
    pass
```

---

## 📝 配置文件说明

### 1. `quant/utils/db_config.py`

数据库配置定义文件：

```python
# 开发环境配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'root1314pwd',
    'database': 'akshare'
}

# 生产环境配置
DB_CONFIG_PRO = {
    'host': '8.137.104.120',
    'port': 3306,
    'user': 'root',
    'password': 'root1314pwd',
    'database': 'akshare'
}
```

### 2. `quant/utils/db_connection.py`

数据库连接管理器：

```python
# 第113行：控制默认环境
db_manager = DatabaseManager(use_pro=True, echo_sql=False)
```

### 3. `.env` (需自行创建)

环境变量配置文件：

```env
# 生产环境
DB_PRO_HOST=8.137.104.120
DB_PRO_PORT=3306
DB_PRO_USER=root
DB_PRO_PASSWORD=your_password
DB_PRO_NAME=akshare
```

---

## ✨ 总结

### 快速切换

```bash
# 一行命令切换环境
python switch_db_env.py --to pro  # 生产环境
python switch_db_env.py --to dev  # 开发环境
python switch_db_env.py --to check # 检查当前环境
```

### 当前状态

✅ **已配置为生产环境**

所有量化模块的数据库操作都将使用生产库：
- 股票数据保存
- 每日增量更新
- 策略回测
- 数据分析

---

## 📚 相关文档

- [db_config.py](quant/utils/db_config.py) - 数据库配置文件
- [db_connection.py](quant/utils/db_connection.py) - 数据库连接管理器
- [.env.example](.env.example) - 环境变量模板
- [QUICK_START_DAILY_UPDATE.md](QUICK_START_DAILY_UPDATE.md) - 每日更新快速开始
