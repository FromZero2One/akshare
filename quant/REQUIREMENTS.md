# 量化模块依赖安装

量化模块需要额外的 Python 包支持。

## 必需依赖

```bash
pip install sqlalchemy pandas pymysql backtrader
```

## 可选依赖

```bash
# 环境变量支持
pip install python-dotenv

# 技术指标计算
pip install ta-lib

# 数据可视化
pip install matplotlib mplfinance
```

## 完整安装命令

```bash
pip install sqlalchemy>=2.0.0 pandas>=2.0.0 pymysql>=1.0.0 backtrader>=1.9.76 python-dotenv>=1.0.0
```

## 验证安装

运行测试脚本验证安装是否成功：

```bash
python quant/test_optimization.py
```

## 常见问题

### 1. ModuleNotFoundError: No module named 'sqlalchemy'
**解决**: `pip install sqlalchemy`

### 2. ModuleNotFoundError: No module named 'pymysql'
**解决**: `pip install pymysql`

### 3. ModuleNotFoundError: No module named 'backtrader'
**解决**: `pip install backtrader`

### 4. ImportError: DLL load failed (Windows)
**解决**: 确保安装了 Microsoft Visual C++ Redistributable

## 数据库配置

复制 `.env.example` 为 `.env` 并填写您的数据库配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：
```
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=akshare
```
