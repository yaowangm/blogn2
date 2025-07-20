from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from pydantic import ConfigDict

class Project(SQLModel, table=True):
    __tablename__ = "project"
    
    model_config = ConfigDict(validate_by_name=True)
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    comment: Optional[str] = Field(default=None)
    recordcount: Optional[int] = Field(default=None)
    accesscount: Optional[int] = Field(default=None)  # 访问量
    userid: Optional[int] = Field(default=None)
    folderid: Optional[int] = Field(default=None)
    createtime: Optional[datetime] = Field(default=None)
    state: Optional[int] = Field(default=None)  # 数据库中是state字段
    lastitem: Optional[int] = Field(default=None)
    updatetime: Optional[datetime] = Field(default=None)
    commentcount: Optional[int] = Field(default=None)  # 评论数 