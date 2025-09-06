from typing import Optional, Dict, Any

from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from tests.BaseEntity import BaseEntity


class StockEntity(BaseEntity):
    __tablename__ = "stock_entity"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30))
    fullname: Mapped[Optional[str]] = mapped_column(String(255))  # 或适当的长度

    def __repr__(self) -> str:
        """
        toString()
        """
        return f"StockEntity(id={self.id!r}, name={self.name!r}, fullname={self.fullname!r})"
    
    @classmethod
    def create_from_dict(cls, data: Dict[str, Any]):
        """
        从字典创建StockEntity对象
        
        Parameters:
        -----------
        data : dict
            包含对象属性的字典
            
        Returns:
        --------
        StockEntity
            创建的StockEntity对象
        """
        # 获取类定义的字段
        valid_fields = {'id', 'name', 'fullname'}
        # 过滤掉无效字段
        filtered_data = {k: v for k, v in data.items() if k in valid_fields and v is not None}
        return cls(**filtered_data)