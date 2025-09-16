from sqlmodel import Field
from typing import Optional
from datetime import datetime
from src.models.base import BaseModel, ProjectMixin

class User(BaseModel, ProjectMixin, table=True):
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=50, description="用户名")
    password: str = Field(max_length=60, description="密码")
    state: int = Field(default=1, description="用户状态：1=正常，0=冻结，10=管理员")
    email: str = Field(max_length=50, description="邮箱")
    regtime: datetime = Field(description="注册时间")
    iplog: Optional[str] = Field(max_length=15, default=None, description="IP日志")
    point: Optional[int] = Field(default=0, description="积分")
    lastupdate: Optional[datetime] = Field(default=None, description="最后更新时间")
    intropiid: Optional[int] = Field(default=None, description="介绍文章ID") 