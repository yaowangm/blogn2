"""
基础模型类

提供所有数据模型的通用配置和字段定义。
"""

from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from pydantic import ConfigDict


class BaseModel(SQLModel):
    """基础模型类"""
    
    model_config = ConfigDict(validate_by_name=True)


class TimestampMixin:
    """时间戳混入类"""
    
    createtime: Optional[datetime] = Field(default=None, description="创建时间")
    updatetime: Optional[datetime] = Field(default=None, description="更新时间")


class StatusMixin:
    """状态混入类"""
    
    status: Optional[int] = Field(default=1, description="状态：1=正常，0=禁用")


class CountMixin:
    """计数混入类"""
    
    accesscount: Optional[int] = Field(default=0, description="访问次数")
    commentcount: Optional[int] = Field(default=0, description="评论数量")


class UserMixin:
    """用户相关混入类"""
    
    userid: Optional[int] = Field(default=None, description="用户ID")


class ProjectMixin:
    """项目相关混入类"""
    
    projectid: Optional[int] = Field(default=None, description="项目ID")


class FolderMixin:
    """文件夹相关混入类"""
    
    folderid: Optional[int] = Field(default=None, description="文件夹ID")

