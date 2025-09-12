from datetime import date
from typing import Optional

from sqlalchemy import Double, Date, Integer, String, Float
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from quant.entity.BaseEntity import BaseEntity


class StockHistoryDailyInfoEntity(BaseEntity):

    # 表名
    __tablename__ = "stock__history_daily_info_entity"

    # 表注释
    __table_args__ = {'comment': '个股历史行情数据表'}

    # 自增主键  字段顺序表示mysql数据表的字段顺序，保存和df的数据顺序一致，避免插入数据错误
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    Ticker: Mapped[Optional[str]] = mapped_column(String(10), comment="股票代码")
    date: Mapped[Optional[date]] = mapped_column(Date, comment="数据日期")
    # Optional[float]  Optional[]函数标记字段可以为空
    open: Mapped[Optional[float]] = mapped_column(Float, comment="当日开盘价")
    close: Mapped[Optional[float]] = mapped_column(Float, comment="收盘价")
    high: Mapped[Optional[float]] = mapped_column(Float, comment="最高价")
    # python中的float映射为mysql Float
    low: Mapped[Optional[float]] = mapped_column(Float, comment="最低价")
    volume: Mapped[Optional[float]] = mapped_column(Float, comment="成交量")
    Trading_Value: Mapped[Optional[float]] = mapped_column(Float, comment="成交额")
    Average_True_Range: Mapped[Optional[float]] = mapped_column(Float, comment="振幅")
    Price_Limit_Change: Mapped[Optional[float]] = mapped_column(Float, comment="涨跌幅")
    Price_Change_Amount: Mapped[Optional[float]] = mapped_column(Float, comment="涨跌额")
    Turnover_Rate: Mapped[Optional[float]] = mapped_column(Float, comment="换手率")
    create_date: Mapped[Optional[date]] = mapped_column(Date, comment="创建时间")
    adjust: Mapped[Optional[str]] = mapped_column(String(10), comment="复权 前[qfq']后[hfq]不['']")


    def __repr__(self) -> str:
        """
        返回对象的字符串表示，包含所有字段信息
        """
        return (f"StockDailyInfoEntity("
                f"date={self.date!r}, "
                f"open={self.open!r}, "
                f"close={self.close!r}, "
                f"high={self.high!r}, "
                f"low={self.low!r}, "
                f"volume={self.volume!r}, "
                f"Trading_Value={self.Trading_Value!r}, "
                f"Average_True_Range={self.Average_True_Range!r}, "
                f"Price_Limit_Change={self.Price_Limit_Change!r}, "
                f"Price_Change_Amount={self.Price_Change_Amount!r}, "
                f"Turnover_Rate={self.Turnover_Rate!r}, "
                f"Ticker={self.Ticker!r}"
                f")")
