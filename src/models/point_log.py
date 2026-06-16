from sqlmodel import Field
from typing import Optional
from datetime import datetime
from pydantic import field_serializer
from src.models.base import BaseModel

class PointLog(BaseModel, table=True):
    """积分记录表
    
    用于跟踪用户每日积分获得情况，实现每日积分限制
    """
    __tablename__ = "point_logs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(description="用户ID")
    points: int = Field(description="获得的积分数")
    source: str = Field(max_length=50, description="积分来源：article_create, regkey_exchange等")
    log_date: datetime = Field(description="积分记录日期（只记录日期，不记录时间）")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="记录创建时间")

    @field_serializer("log_date")
    def serialize_log_date(self, value: datetime) -> str:
        return value.date().isoformat()
