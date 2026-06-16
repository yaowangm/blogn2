from sqlmodel import Field
from typing import Optional
from datetime import datetime
from src.constants import ProjectStatus
from src.models.base import BaseModel, TimestampMixin, UserMixin, FolderMixin, CountMixin

class Project(BaseModel, TimestampMixin, UserMixin, FolderMixin, CountMixin, table=True):
    __tablename__ = "project"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, description="项目名称")
    comment: Optional[str] = Field(default=None, description="项目描述")
    recordcount: Optional[int] = Field(default=None, description="记录数量")
    lastitem: Optional[int] = Field(default=None, description="最后条目ID")
    state: Optional[int] = Field(
        default=ProjectStatus.ACTIVE,
        description="项目状态：0=正常，1=禁用",
    ) 