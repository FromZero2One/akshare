from datetime import date, datetime
from typing import Optional

from sqlalchemy import Double, Date, Integer, String, DateTime, DECIMAL, Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from quant.entity.BaseEntity import BaseEntity


class BacktestResultEntity(BaseEntity):
    # 表名
    __tablename__ = "backtest_result_entity"

    # 表注释 + 复合唯一键（支持 INSERT ... ON DUPLICATE KEY UPDATE 原子 upsert）
    # 同 (symbol, strategy_name) 视为同一份回测结果，重新回测时直接覆盖。
    # ⚠️ 升级提示：若存量库已有重复 (symbol, strategy_name) 行，需先手动清理再加唯一键。
    __table_args__ = {
        'comment': '回测结果表',
        'mysql_unique_key': 'uk_symbol_strategy (symbol, strategy_name)',
    }

    # 自增主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[Optional[str]] = mapped_column(String(10), comment="股票代码")
    # 长度说明：SQLAlchemy String(N) → MySQL VARCHAR(N)，N 为字符数（非字节）。
    # A 股股票名最长 6 字符（如 "*ST康佳A"），String(10) 余量充足。
    stock_name: Mapped[Optional[str]] = mapped_column(String(10), comment="股票名称")
    strategy_name: Mapped[Optional[str]] = mapped_column(String(50), comment="策略名称")
    initial_cash: Mapped[Optional[float]] = mapped_column(Double, comment="初始资金")
    final_value: Mapped[Optional[float]] = mapped_column(Double, comment="总资金")
    net_profit: Mapped[Optional[float]] = mapped_column(Double, comment="净收益")
    # 数据库层面保留两位小数
    returns: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 2), comment="收益率")
    commission: Mapped[Optional[float]] = mapped_column(Double, comment="手续费率")
    start_date: Mapped[Optional[date]] = mapped_column(Date, comment="开始时间")
    end_date: Mapped[Optional[date]] = mapped_column(Date, comment="结束时间")
    create_time: Mapped[Optional[datetime]] = mapped_column(DateTime, comment="创建时间")
    # 策略参数 JSON 序列化（用于追溯某次回测跑的是哪组参数）
    # 老行为：未传时为 NULL，与存量行兼容
    params_json: Mapped[Optional[str]] = mapped_column(Text, comment="策略参数 JSON")

    def __repr__(self) -> str:
        """
        返回对象的字符串表示，包含所有字段信息
        """
        return (f"BacktestResultEntity("
                f"symbol={self.symbol!r}, "
                f"strategy_name={self.strategy_name!r}, "
                f"initial_cash={self.initial_cash!r}, "
                f"final_value={self.final_value!r}, "
                f"net_profit={self.net_profit!r}, "
                f"returns={self.returns!r}, "
                f"start_date={self.start_date!r}, "
                f"end_date={self.end_date!r}"
                f")")
