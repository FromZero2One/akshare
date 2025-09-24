from datetime import date
from typing import Optional
from sqlalchemy import BigInteger, Float, Integer, String, Date
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from quant.entity.BaseEntity import BaseEntity


class StockCommentEntity(BaseEntity):
    # 表名
    __tablename__ = "stock_comment_entity"

    # 表注释
    __table_args__ = {'comment': '千股千评数据表'}

    # 主键  mysql注解 comment
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    index: Mapped[int] = mapped_column(Integer, comment="序号")
    SECURITY_INNER_CODE: Mapped[Optional[int]] = mapped_column(BigInteger, comment="-")
    symbol: Mapped[Optional[str]] = mapped_column(String(10), comment="股票代码")
    SECUCODE: Mapped[Optional[str]] = mapped_column(String(20), comment="-")
    TRADE_DATE: Mapped[Optional[date]] = mapped_column(Date, comment="交易日")
    SECURITY_NAME_ABBR: Mapped[Optional[str]] = mapped_column(String(50), comment="名称")
    SUPERDEAL_INFLOW: Mapped[Optional[int]] = mapped_column(BigInteger, comment="-")
    SUPERDEAL_OUTFLOW: Mapped[Optional[int]] = mapped_column(BigInteger, comment="-")
    PRIME_INFLOW: Mapped[Optional[float]] = mapped_column(Float, comment="-")
    CLOSE_PRICE: Mapped[Optional[float]] = mapped_column(Float, comment="最新价")
    CHANGE_RATE: Mapped[Optional[float]] = mapped_column(Float, comment="涨跌幅")
    TRADE_MARKET_CODE: Mapped[Optional[int]] = mapped_column(BigInteger, comment="-")
    TURNOVERRATE: Mapped[Optional[float]] = mapped_column(Float, comment="换手率")
    PRIME_COST: Mapped[Optional[float]] = mapped_column(Float, comment="主力成本")
    PE_DYNAMIC: Mapped[Optional[float]] = mapped_column(Float, comment="市盈率")
    PRIME_COST_20DAYS: Mapped[Optional[float]] = mapped_column(Float, comment="-")
    PRIME_COST_60DAYS: Mapped[Optional[float]] = mapped_column(Float, comment="-")
    ORG_PARTICIPATE: Mapped[Optional[float]] = mapped_column(Float, comment="机构参与度")
    PARTICIPATE_TYPE: Mapped[Optional[int]] = mapped_column(BigInteger, comment="-")
    BIGDEAL_INFLOW: Mapped[Optional[int]] = mapped_column(BigInteger, comment="-")
    BIGDEAL_OUTFLOW: Mapped[Optional[int]] = mapped_column(BigInteger, comment="-")
    BUY_SUPERDEAL_RATIO: Mapped[Optional[float]] = mapped_column(Float, comment="-")
    BUY_BIGDEAL_RATIO: Mapped[Optional[float]] = mapped_column(Float, comment="-")
    RATIO: Mapped[Optional[float]] = mapped_column(Float, comment="-")
    RATIO_3DAYS: Mapped[Optional[float]] = mapped_column(Float, comment="-")
    RATIO_50DAYS: Mapped[Optional[float]] = mapped_column(Float, comment="-")
    TOTALSCORE: Mapped[Optional[float]] = mapped_column(Float, comment="综合得分")
    RANK_UP: Mapped[Optional[int]] = mapped_column(Integer, comment="上升")
    RANK: Mapped[Optional[int]] = mapped_column(Integer, comment="目前排名")
    FOCUS: Mapped[Optional[float]] = mapped_column(Float, comment="关注指数")
    SECURITY_TYPE_CODE: Mapped[Optional[int]] = mapped_column(BigInteger, comment="-")
    LISTING_STATE: Mapped[Optional[int]] = mapped_column(BigInteger, comment="-")
    create_date: Mapped[Optional[date]] = mapped_column(Date, comment="创建时间")


    def __repr__(self) -> str:
        """
        返回对象的字符串表示，包含关键字段信息
        """
        return (f"StockCommentEntity("
                f"SECURITY_CODE={self.SECURITY_CODE!r}, "
                f"SECURITY_NAME_ABBR={self.SECURITY_NAME_ABBR!r}, "
                f"TRADE_DATE={self.TRADE_DATE!r}, "
                f"CLOSE_PRICE={self.CLOSE_PRICE!r}, "
                f"CHANGE_RATE={self.CHANGE_RATE!r}"
                f")")
