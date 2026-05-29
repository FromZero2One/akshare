#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2026/5/29
Desc: Redis 股票日线数据缓存

将股票日线数据以 Parquet 压缩字节形式存储在 Redis 中，
读取性能比本地 Parquet 文件又提升一个数量级。

缓存层级链：
  Redis (L1, 内存) → Parquet (L2, 磁盘) → MySQL (L3, 远程)

设计要点：
  - 序列化：利用已有的 pyarrow，DataFrame ↔ Parquet 字节
  - 压缩：zstd（高压缩比 + 快速度）
  - 键前缀：stock_cache:{symbol}:{adjust}:data / :meta
  - 自动降级：Redis 不可用时返回 None，调用方降级到 Parquet
  - 线程安全：Redis 单线程原子操作，无需额外锁
"""

import io
import json
import time
from typing import Optional, Callable

import pandas as pd

from .logger_config import get_quant_logger

logger = get_quant_logger()

# redis 包懒加载（避免未安装时模块加载失败）
_Redis = None
_RedisError = None
_AuthenticationError = None
_TimeoutError = None


def _load_redis():
    """延迟导入 redis，仅在使用时加载"""
    global _Redis, _RedisError, _AuthenticationError, _TimeoutError
    if _Redis is not None:
        return True
    try:
        from redis import Redis as R
        from redis.exceptions import RedisError as RE, AuthenticationError as AE, TimeoutError as TE
        _Redis, _RedisError, _AuthenticationError, _TimeoutError = R, RE, AE, TE
        return True
    except ImportError:
        logger.warning("redis 包未安装，请执行: pip install redis")
        return False


class RedisStockDataCache:
    """
    Redis 股票日线缓存。
    将 DataFrame 序列化为 Parquet 字节后存入 Redis。

    同一个接口签名兼容 `StockDataCache`，可做 drop-in replacement。

    Example:
        rcache = RedisStockDataCache(password='1314')
        df = rcache.get('601398', 'qfq')
        if df is None:
            df = fetch_from_db()
            rcache.put('601398', 'qfq', df)
    """

    # Redis 键模板
    _KEY_DATA = "stock_cache:{symbol}:{adjust}:data"   # Parquet 字节
    _KEY_META = "stock_cache:{symbol}:{adjust}:meta"    # JSON 元数据

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        socket_timeout: int = 2,
        socket_connect_timeout: int = 2,
        compression: str = "zstd",
        **kwargs,
    ):
        """
        Args:
            host: Redis 主机
            port: Redis 端口
            db: Redis 数据库编号
            password: Redis 密码
            socket_timeout: 读写超时（秒）
            socket_connect_timeout: 连接超时（秒）
            compression: Parquet 压缩算法 ('zstd', 'snappy', 'lz4', None)
        """
        if not _load_redis():
            raise ImportError("redis 包未安装，无法使用 RedisStockDataCache")
        self._config = dict(
            host=host, port=port, db=db, password=password,
            socket_timeout=socket_timeout,
            socket_connect_timeout=socket_connect_timeout,
            **kwargs,
        )
        self._compression = compression
        self._client: Optional[_Redis] = None

    # ------------------------------------------------------------------
    # 连接管理
    # ------------------------------------------------------------------

    @property
    def client(self) -> "_Redis":
        """延迟初始化 Redis 连接"""
        if self._client is None:
            self._client = _Redis(**self._config)
        return self._client

    def ping(self) -> bool:
        """检查 Redis 是否连通"""
        try:
            return self.client.ping()
        except (_RedisError, _AuthenticationError, _TimeoutError) as e:
            logger.warning(f"Redis ping 失败: {e}")
            return False

    def close(self):
        """关闭 Redis 连接"""
        if self._client is not None:
            try:
                self._client.close()
            except Exception:
                pass
            self._client = None

    def _ensure_connected(self) -> bool:
        """确保连接可用，不可用时自动重连（最多尝试 2 次）"""
        for attempt in range(2):
            try:
                self.client.ping()
                return True
            except (_RedisError, _AuthenticationError, _TimeoutError) as e:
                if attempt == 0:
                    logger.debug(f"Redis 连接断开，尝试重连: {e}")
                    self.close()
                else:
                    logger.warning(f"Redis 连接失败 (已重试): {e}")
        return False

    # ------------------------------------------------------------------
    # 序列化
    # ------------------------------------------------------------------

    @staticmethod
    def _df_to_bytes(df: pd.DataFrame, compression: str = "zstd") -> bytes:
        """DataFrame → Parquet 字节"""
        buf = io.BytesIO()
        df.to_parquet(buf, index=False, compression=compression)
        return buf.getvalue()

    @staticmethod
    def _bytes_to_df(data: bytes) -> Optional[pd.DataFrame]:
        """Parquet 字节 → DataFrame"""
        try:
            buf = io.BytesIO(data)
            return pd.read_parquet(buf)
        except Exception as e:
            logger.warning(f"Parquet 反序列化失败: {e}")
            return None

    @staticmethod
    def _build_meta(symbol: str, adjust: str, df: pd.DataFrame) -> dict:
        """构建元数据字典"""
        latest_date = ""
        if "date" in df.columns:
            try:
                latest_date = str(df["date"].max())
            except Exception:
                pass
        return {
            "symbol": symbol,
            "adjust": adjust,
            "rows": len(df),
            "latest_date": latest_date,
            "cached_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

    # ------------------------------------------------------------------
    # 键生成
    # ------------------------------------------------------------------

    def _data_key(self, symbol: str, adjust: str) -> str:
        return self._KEY_DATA.format(symbol=symbol, adjust=adjust or "none")

    def _meta_key(self, symbol: str, adjust: str) -> str:
        return self._KEY_META.format(symbol=symbol, adjust=adjust or "none")

    def _pattern_key(self, symbol: Optional[str] = None, adjust: Optional[str] = None) -> str:
        """用于 SCAN 的模式匹配键"""
        s = symbol or "*"
        a = adjust or "*"
        return self._KEY_DATA.format(symbol=s, adjust=a)

    # ------------------------------------------------------------------
    # 核心 API
    # ------------------------------------------------------------------

    def get(self, symbol: str, adjust: str = "qfq") -> Optional[pd.DataFrame]:
        """从 Redis 读取股票日线数据"""
        if not self._ensure_connected():
            return None
        try:
            data = self.client.get(self._data_key(symbol, adjust))
            if data is None:
                logger.debug(f"Redis 缓存未命中: {symbol}({adjust})")
                return None
            df = self._bytes_to_df(data)
            if df is not None:
                logger.debug(
                    f"Redis 缓存命中: {symbol}({adjust}) {len(df)} 行, "
                    f"{len(data) / 1024:.1f} KB"
                )
            return df
        except (_RedisError, _TimeoutError) as e:
            logger.warning(f"Redis 读取失败({symbol}/{adjust}): {e}")
            self.close()
            return None

    def put(self, symbol: str, adjust: str, df: pd.DataFrame):
        """将 DataFrame 写入 Redis"""
        if df is None or df.empty:
            logger.warning(f"跳过空数据: {symbol}({adjust})")
            return
        if not self._ensure_connected():
            return
        try:
            data = self._df_to_bytes(df, self._compression)
            meta = self._build_meta(symbol, adjust, df)
            meta_json = json.dumps(meta, ensure_ascii=False)

            pipe = self.client.pipeline()
            pipe.set(self._data_key(symbol, adjust), data)
            pipe.set(self._meta_key(symbol, adjust), meta_json)
            pipe.execute()

            logger.info(
                f"Redis 缓存写入: {symbol}({adjust}) {len(df)} 行, "
                f"{len(data) / 1024:.1f} KB"
            )
        except (_RedisError, _TimeoutError) as e:
            logger.warning(f"Redis 写入失败({symbol}/{adjust}): {e}")
            self.close()

    def get_or_fetch(
        self,
        symbol: str,
        adjust: str = "qfq",
        fetch_func: Optional[Callable[[], pd.DataFrame]] = None,
        force_refresh: bool = False,
    ) -> Optional[pd.DataFrame]:
        """
        Redis 优先的数据获取。

        流程：Redis 命中 → 返回
              Redis 未命中 → fetch_func → 回填 → 返回
        """
        if not force_refresh and self._ensure_connected():
            cached = self.get(symbol, adjust)
            if cached is not None and not cached.empty:
                return cached
        if fetch_func is None:
            return None
        t0 = time.time()
        df = fetch_func()
        elapsed = time.time() - t0
        if df is not None and not df.empty:
            tag = "强制刷新" if force_refresh else "Redis 未命中"
            logger.info(f"{tag}: {symbol}({adjust}) {elapsed:.2f}s, {len(df)} 行")
            self.put(symbol, adjust, df)
        else:
            logger.warning(f"数据获取返回空: {symbol}({adjust})")
        return df

    def get_latest_date_in_cache(self, symbol: str, adjust: str = "qfq") -> Optional[str]:
        """读取缓存中的最新日期"""
        if not self._ensure_connected():
            return None
        try:
            meta_json = self.client.get(self._meta_key(symbol, adjust))
            if meta_json is None:
                return None
            meta = json.loads(meta_json)
            return meta.get("latest_date")
        except (_RedisError, json.JSONDecodeError) as e:
            logger.warning(f"Redis 元数据读取失败: {e}")
            return None

    def clear(self, symbol: Optional[str] = None, adjust: Optional[str] = None):
        """
        清除 Redis 缓存。

        Args:
            symbol: 指定股票，None 则清除全部
            adjust: 指定复权类型，None 则清除该股票全部
        """
        if not self._ensure_connected():
            return
        try:
            if symbol:
                if adjust:
                    dk = self._data_key(symbol, adjust)
                    mk = self._meta_key(symbol, adjust)
                    self.client.delete(dk, mk)
                    logger.info(f"Redis 清除: {symbol}({adjust})")
                else:
                    pattern = self._pattern_key(symbol, "*")
                    cursor, keys = self._scan(pattern)
                    if keys:
                        self.client.delete(*keys)
                    logger.info(f"Redis 清除: {symbol}(*) {len(keys)} 条")
            else:
                self.client.flushdb()
                logger.info("Redis 清除全部缓存")
        except (_RedisError, _TimeoutError) as e:
            logger.warning(f"Redis 清除失败: {e}")

    def stats(self) -> dict:
        """Redis 缓存统计（含服务器状态）"""
        try:
            if not self._ensure_connected():
                return {"available": False, "error": "连接失败"}
            info = self.client.info()

            # SCAN 估算 data key 的字节数
            total_bytes = 0
            cursor = 0
            while True:
                cursor, keys = self.client.scan(
                    cursor=cursor,
                    match=self._pattern_key(),
                    count=100,
                )
                if keys:
                    pipe = self.client.pipeline()
                    for k in keys:
                        pipe.strlen(k)
                    sizes = pipe.execute()
                    total_bytes += sum(s for s in sizes if s)
                if cursor == 0:
                    break

            return {
                "available": True,
                "server_version": info.get("redis_version", ""),
                "used_memory_mb": round(info.get("used_memory", 0) / (1024 * 1024), 2),
                "cache_size_mb": round(total_bytes / (1024 * 1024), 2),
                "uptime_days": info.get("uptime_in_days", 0),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
            }
        except (_RedisError, _TimeoutError) as e:
            return {"available": False, "error": str(e)}

    # ------------------------------------------------------------------
    # 内部辅助
    # ------------------------------------------------------------------

    def _scan(self, pattern: str) -> tuple:
        """SCAN 匹配模式的所有键"""
        keys = []
        cursor = 0
        while True:
            cursor, batch = self.client.scan(
                cursor=cursor,
                match=pattern,
                count=500,
            )
            keys.extend(batch)
            if cursor == 0:
                break
        return cursor, keys

    def __repr__(self):
        return (
            f"<RedisStockDataCache "
            f"{self._config['host']}:{self._config['port']}/{self._config['db']}>"
        )


# 全局实例（redis 未安装时不会崩溃）
try:
    redis_stock_cache = RedisStockDataCache(password="1314")
except ImportError:
    redis_stock_cache = None
    logger.warning("redis_stock_cache 不可用（redis 包未安装）")
