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
    TRADE_DATE: Mapped[Optional[date]] = mapped_column(Date, comment="交易日")
    symbol: Mapped[Optional[str]] = mapped_column(String(10), comment="股票代码")
    SECURITY_NAME_ABBR: Mapped[Optional[str]] = mapped_column(String(50), comment="名称")
    PRIME_COST: Mapped[Optional[float]] = mapped_column(Float, comment="主力成本")
    TOTALSCORE: Mapped[Optional[float]] = mapped_column(Float, comment="综合得分")
    FOCUS: Mapped[Optional[float]] = mapped_column(Float, comment="关注指数")
    ORG_PARTICIPATE: Mapped[Optional[float]] = mapped_column(Float, comment="机构参与度")
    CLOSE_PRICE: Mapped[Optional[float]] = mapped_column(Float, comment="最新价")
    CHANGE_RATE: Mapped[Optional[float]] = mapped_column(Float, comment="涨跌幅")
    TURNOVERRATE: Mapped[Optional[float]] = mapped_column(Float, comment="换手率")
    PE_DYNAMIC: Mapped[Optional[float]] = mapped_column(Float, comment="市盈率")
    RANK_UP: Mapped[Optional[int]] = mapped_column(Integer, comment="上升")
    RANK: Mapped[Optional[int]] = mapped_column(Integer, comment="目前排名")
    SUPERDEAL_INFLOW: Mapped[Optional[int]] = mapped_column(BigInteger, comment="SUPERDEAL_INFLOW")
    SUPERDEAL_OUTFLOW: Mapped[Optional[int]] = mapped_column(BigInteger, comment="SUPERDEAL_OUTFLOW")
    PRIME_INFLOW: Mapped[Optional[float]] = mapped_column(Float, comment="PRIME_INFLOW")
    PRIME_COST_20DAYS: Mapped[Optional[float]] = mapped_column(Float, comment="PRIME_COST_20DAYS")
    PRIME_COST_60DAYS: Mapped[Optional[float]] = mapped_column(Float, comment="PRIME_COST_60DAYS")
    PARTICIPATE_TYPE: Mapped[Optional[int]] = mapped_column(BigInteger, comment="PARTICIPATE_TYPE")
    BIGDEAL_INFLOW: Mapped[Optional[int]] = mapped_column(BigInteger, comment="BIGDEAL_INFLOW")
    BIGDEAL_OUTFLOW: Mapped[Optional[int]] = mapped_column(BigInteger, comment="BIGDEAL_OUTFLOW")
    BUY_SUPERDEAL_RATIO: Mapped[Optional[float]] = mapped_column(Float, comment="BUY_SUPERDEAL_RATIO")
    BUY_BIGDEAL_RATIO: Mapped[Optional[float]] = mapped_column(Float, comment="BUY_BIGDEAL_RATIO")
    RATIO: Mapped[Optional[float]] = mapped_column(Float, comment="RATIO")
    RATIO_3DAYS: Mapped[Optional[float]] = mapped_column(Float, comment="RATIO_3DAYS")
    RATIO_50DAYS: Mapped[Optional[float]] = mapped_column(Float, comment="RATIO_50DAYS")
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
