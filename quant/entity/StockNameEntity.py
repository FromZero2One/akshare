from typing import Optional

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from quant.entity.BaseEntity import BaseEntity


class StockNameEntity(BaseEntity):
    # 表名
    __tablename__ = "stock_name_entity"

    # 主键  mysql注解 comment
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[Optional[str]] = mapped_column(String(10), comment="股票代码")
    stock_name: Mapped[Optional[str]] = mapped_column(String(255), comment="股票名称")

    def __repr__(self) -> str:
        """
        返回对象的字符串表示，包含所有字段信息
        """
        return (f"StockNameEntity("
                f"id={self.id!r}, "
                f"code={self.code!r}, "
                f"stock_name={self.stock_name!r}"
                f")")
