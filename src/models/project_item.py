from sqlmodel import Field
from sqlalchemy import Index
from typing import Optional
from datetime import datetime
from src.models.base import BaseModel, TimestampMixin, StatusMixin, UserMixin, FolderMixin, ProjectMixin, CountMixin

class ProjectItem(BaseModel, TimestampMixin, StatusMixin, UserMixin, FolderMixin, ProjectMixin, CountMixin, table=True):
    __tablename__ = "projectitem"
    __table_args__ = (
        # 博客列表分页：WHERE projectid=? AND status=1 ORDER BY createtime DESC OFFSET n LIMIT m
        Index("ix_projectitem_project_status_createtime", "projectid", "status", "createtime"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, description="条目名称")
    comment: Optional[str] = Field(default=None, description="条目内容")
    itemtype: Optional[int] = Field(default=None, description="条目类型")
    itemsize: Optional[int] = Field(default=None, description="条目大小（字节）")
    attachment: Optional[str] = Field(max_length=200, default=None, description="附件路径")
    linkstr: Optional[str] = Field(max_length=200, default=None, description="链接字符串")
    lastmodifytime: Optional[datetime] = Field(default=None, description="最后修改时间")
    allowpost: Optional[int] = Field(default=None, description="是否允许评论：1=允许，2=仅登录用户，3=不允许") 