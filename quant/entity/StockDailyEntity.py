from datetime import date
from typing import Optional

from sqlalchemy import BigInteger, Float, Integer, String, Date
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from quant.entity.BaseEntity import BaseEntity


class StockDailyEntity(BaseEntity):
    # 表名
    __tablename__ = "stock_value_entity"

    # 表注释
    __table_args__ = {'comment': '个股估值数据表'}

    # 主键  mysql注解 comment
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    create_date: Mapped[Optional[date]] = mapped_column(Date, comment="创建时间")
    symbol: Mapped[Optional[str]] = mapped_column(String(10), comment="股票代码")
    SECURITY_NAME_ABBR: Mapped[Optional[str]] = mapped_column(String(10), comment="股票名称")
    BOARD_CODE: Mapped[Optional[str]] = mapped_column(String(10), comment="板块代码")
    BOARD_NAME: Mapped[Optional[str]] = mapped_column(String(10), comment="板块名称")
    TRADE_DATE: Mapped[Optional[date]] = mapped_column(comment="数据日期")
    # Optional[float]  Optional[]函数标记字段可以为空
    CLOSE_PRICE: Mapped[Optional[float]] = mapped_column(Float, comment="当日收盘价")
    CHANGE_RATE: Mapped[Optional[float]] = mapped_column(Float, comment="当日涨跌幅")
    TOTAL_MARKET_CAP: Mapped[Optional[float]] = mapped_column(Float, comment="总市值")
    # python中的float映射为mysql Float
    NOTLIMITED_MARKETCAP_A: Mapped[Optional[float]] = mapped_column(Float, comment="流通市值")
    # python中的int映射为mysql bigint
    TOTAL_SHARES: Mapped[Optional[int]] = mapped_column(BigInteger, comment="总股本")
    FREE_SHARES_A: Mapped[Optional[int]] = mapped_column(BigInteger, comment="流通股本")
    PE_TTM: Mapped[Optional[float]] = mapped_column(Float, comment="PE(TTM市盈率)")
    PE_LAR: Mapped[Optional[float]] = mapped_column(Float, comment="PE(静市盈率)")
    PB_MRQ: Mapped[Optional[float]] = mapped_column(Float, comment="市净率")
    PEG_CAR: Mapped[Optional[float]] = mapped_column(Float,
                                                     comment="PEG值[市盈率相对盈利增长比率{PEG=市盈率(PE)/盈利增长率(G)}被低估PEG<1 反之被高估]")
    PCF_OCF_TTM: Mapped[Optional[float]] = mapped_column(Float, comment="市现率")
    PS_TTM: Mapped[Optional[float]] = mapped_column(Float, comment="市销率")

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
