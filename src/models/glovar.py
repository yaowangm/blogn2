"""
全局变量模型

用于存储系统全局统计数据，如用户数量、项目数量、项目项数量等。
"""

from sqlmodel import Field
from typing import Optional
from src.models.base import BaseModel


class Glovar(BaseModel, table=True):
    """全局变量表
    
    存储系统全局统计数据，包括：
    - usercount: 用户数量
    - projectcount: 项目数量  
    - projectitemcount: 项目项数量
    """
    
    __tablename__ = "glovar"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    varname: str = Field(max_length=50, description="变量名")
    varvalue: Optional[int] = Field(default=0, description="变量值")
