from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class Relation(SQLModel, table=True):
    """关系表模型 - 用于存储博客订阅关系"""
    __tablename__ = "relation"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    projectid: Optional[int] = Field(default=None, description="发起订阅的博客项目ID")
    objectid: Optional[int] = Field(default=None, description="被订阅的博客项目ID")
    created: Optional[datetime] = Field(default=None, description="创建时间")
    acttype: Optional[int] = Field(default=1, description="关系类型，默认为1（订阅）")
    
    def __repr__(self):
        return f"<Relation(id={self.id}, projectid={self.projectid}, objectid={self.objectid}, acttype={self.acttype})>"
