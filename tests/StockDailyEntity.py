from datetime import date
from typing import Optional

from sqlalchemy import BigInteger, Double
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from tests.BaseEntity import BaseEntity


class StockDailyEntity(BaseEntity):
    # 表名
    __tablename__ = "stock_daily_entity"

    # 主键  mysql注解 comment
    TRADE_DATE: Mapped[date] = mapped_column(primary_key=True, comment="数据日期")
    # Optional[float]  Optional[]函数标记字段可以为空
    CLOSE_PRICE: Mapped[Optional[float]] = mapped_column(Double, comment="当日收盘价")
    CHANGE_RATE: Mapped[Optional[float]] = mapped_column(Double, comment="当日涨跌幅")
    TOTAL_MARKET_CAP: Mapped[Optional[float]] = mapped_column(Double, comment="总市值")
    # python中的float映射为mysql double
    NOTLIMITED_MARKETCAP_A: Mapped[Optional[float]] = mapped_column(Double, comment="流通市值")
    # python中的int映射为mysql bigint
    TOTAL_SHARES: Mapped[Optional[int]] = mapped_column(BigInteger, comment="总股本")
    FREE_SHARES_A: Mapped[Optional[int]] = mapped_column(BigInteger, comment="流通股本")
    PE_TTM: Mapped[Optional[float]] = mapped_column(Double, comment="PE(TTM)")
    PE_LAR: Mapped[Optional[float]] = mapped_column(Double, comment="PE(静)")
    PB_MRQ: Mapped[Optional[float]] = mapped_column(Double, comment="市净率")
    PEG_CAR: Mapped[Optional[float]] = mapped_column(Double, comment="PEG值")
    PCF_OCF_TTM: Mapped[Optional[float]] = mapped_column(Double, comment="市现率")
    PS_TTM: Mapped[Optional[float]] = mapped_column(Double, comment="市销率")

    def __repr__(self) -> str:
        """
        toString()
        """
        return f"StockDailyEntity(TRADE_DATE={self.TRADE_DATE!r})"
