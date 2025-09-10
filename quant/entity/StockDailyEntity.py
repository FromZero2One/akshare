from datetime import date
from typing import Optional

from sqlalchemy import BigInteger, Double, Integer
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from quant.entity.BaseEntity import BaseEntity


class StockDailyEntity(BaseEntity):
    # 表名
    __tablename__ = "stock_daily_entity"

    # 主键  mysql注解 comment
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    TRADE_DATE: Mapped[Optional[date]] = mapped_column(comment="数据日期")
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
        返回对象的字符串表示，包含所有字段信息
        """
        return (f"StockDailyEntity("
                f"TRADE_DATE={self.TRADE_DATE!r}, "
                f"CLOSE_PRICE={self.CLOSE_PRICE!r}, "
                f"CHANGE_RATE={self.CHANGE_RATE!r}, "
                f"TOTAL_MARKET_CAP={self.TOTAL_MARKET_CAP!r}, "
                f"NOTLIMITED_MARKETCAP_A={self.NOTLIMITED_MARKETCAP_A!r}, "
                f"TOTAL_SHARES={self.TOTAL_SHARES!r}, "
                f"FREE_SHARES_A={self.FREE_SHARES_A!r}, "
                f"PE_TTM={self.PE_TTM!r}, "
                f"PE_LAR={self.PE_LAR!r}, "
                f"PB_MRQ={self.PB_MRQ!r}, "
                f"PEG_CAR={self.PEG_CAR!r}, "
                f"PCF_OCF_TTM={self.PCF_OCF_TTM!r}, "
                f"PS_TTM={self.PS_TTM!r}"
                f")")
