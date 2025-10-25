from datetime import date
from typing import Optional

from sqlalchemy import Integer, String, Date
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from quant.entity.BaseEntity import BaseEntity


class StockNameEntity(BaseEntity):
    # 表名
    __tablename__ = "stock_name_entity"

    # 表注释
    __table_args__ = {'comment': '股票名称表'}

    # 主键  mysql注解 comment
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[Optional[str]] = mapped_column(String(10), comment="股票代码")
    stock_name: Mapped[Optional[str]] = mapped_column(String(20), comment="股票名称")
    create_date: Mapped[Optional[date]] = mapped_column(Date, comment="创建时间")

    def __repr__(self) -> str:
        """
        返回对象的字符串表示，包含所有字段信息
        """
        return (f"StockNameEntity("
                f"id={self.id!r}, "
                f"code={self.code!r}, "
                f"stock_name={self.stock_name!r}"
                f")")
