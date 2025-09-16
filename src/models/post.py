from sqlmodel import Field
from typing import Optional
from datetime import datetime
from src.models.base import BaseModel, StatusMixin, UserMixin, FolderMixin, ProjectMixin

class Post(BaseModel, StatusMixin, UserMixin, FolderMixin, table=True):
    __tablename__ = "post"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    rootid: Optional[int] = Field(default=None, description="根评论ID")
    subject: Optional[str] = Field(max_length=200, default=None, description="主题")
    content: Optional[str] = Field(default=None, description="内容")
    size: Optional[int] = Field(default=None, description="内容大小（字节）")
    hits: Optional[int] = Field(default=None, description="点击数")
    posttime: Optional[datetime] = Field(default=None, description="发布时间")
    lastreplytime: Optional[datetime] = Field(default=None, description="最后回复时间")
    lastreplyid: Optional[int] = Field(default=None, description="最后回复ID")
    projectitemid: Optional[int] = Field(default=None, description="项目条目ID：0表示留言本，>0表示博文评论")
    replycount: Optional[int] = Field(default=None, description="回复数量")
    userip: Optional[str] = Field(max_length=15, default=None, description="用户IP地址") 