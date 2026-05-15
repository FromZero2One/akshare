from datetime import date
from typing import Optional

from sqlalchemy import Double, Date, Integer, String, Float
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from quant.entity.BaseEntity import BaseEntity


class StockHistoryDailyInfoEntity(BaseEntity):

    # 表名
    __tablename__ = "stock_history_daily_info_entity"

    # 表注释
    __table_args__ = {
        'comment': '个股历史行情数据表',
        'mysql_unique_key': 'uk_symbol_date_adjust (symbol, date, adjust)'  # 复合唯一索引
    }

    # 自增主键  字段顺序表示mysql数据表的字段顺序，保存和df的数据顺序一致，避免插入数据错误
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[Optional[str]] = mapped_column(String(10), comment="股票代码")
    date: Mapped[Optional[date]] = mapped_column(Date, comment="数据日期")
    # Optional[float]  Optional[]函数标记字段可以为空
    open: Mapped[Optional[float]] = mapped_column(Float, comment="当日开盘价")
    close: Mapped[Optional[float]] = mapped_column(Float, comment="收盘价")
    high: Mapped[Optional[float]] = mapped_column(Float, comment="最高价")
    # python中的float映射为mysql Float
    low: Mapped[Optional[float]] = mapped_column(Float, comment="最低价")
    volume: Mapped[Optional[float]] = mapped_column(Float, comment="成交量")
    trading_value: Mapped[Optional[float]] = mapped_column(Float, comment="成交额")
    average_true_range: Mapped[Optional[float]] = mapped_column(Float, comment="振幅")
    price_limit_change: Mapped[Optional[float]] = mapped_column(Float, comment="涨跌幅")
    price_change_amount: Mapped[Optional[float]] = mapped_column(Float, comment="涨跌额")
    turnover_rate: Mapped[Optional[float]] = mapped_column(Float, comment="换手率")
    create_date: Mapped[Optional[date]] = mapped_column(Date, comment="创建时间")
    adjust: Mapped[Optional[str]] = mapped_column(String(10), comment="复权 前[qfq']后[hfq]不['']")


    def __repr__(self) -> str:
        """
        返回对象的字符串表示，包含所有字段信息
        """
        return (f"StockHistoryDailyInfoEntity("
                f"symbol={self.symbol!r}, "
                f"date={self.date!r}, "
                f"open={self.open!r}, "
                f"close={self.close!r}, "
                f"high={self.high!r}, "
                f"low={self.low!r}, "
                f"volume={self.volume!r}, "
                f"trading_value={self.trading_value!r}, "
                f"average_true_range={self.average_true_range!r}, "
                f"price_limit_change={self.price_limit_change!r}, "
                f"price_change_amount={self.price_change_amount!r}, "
                f"turnover_rate={self.turnover_rate!r}, "
                f"adjust={self.adjust!r}"
                f")")
