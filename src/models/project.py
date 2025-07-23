from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from pydantic import ConfigDict

class Project(SQLModel, table=True):
    __tablename__ = "project"
    
    model_config = ConfigDict(validate_by_name=True)
    
    id: Optional[int] = Field(default=None, primary_key=True, alias="ID")
    name: str = Field(max_length=100, alias="Name")
    comment: Optional[str] = Field(default=None, alias="Comment")
    recordcount: Optional[int] = Field(default=None, alias="Recordcount")
    accesscount: Optional[int] = Field(default=None, alias="Accesscount")  # 访问量
    userid: Optional[int] = Field(default=None, alias="Userid")
    folderid: Optional[int] = Field(default=None, alias="Folderid")
    createtime: Optional[datetime] = Field(default=None, alias="Createtime")
    state: Optional[int] = Field(default=None, alias="State")  # 数据库中是state字段
    lastitem: Optional[int] = Field(default=None, alias="Lastitem")
    updatetime: Optional[datetime] = Field(default=None, alias="Updatetime")
    commentcount: Optional[int] = Field(default=None, alias="Commentcount")  # 评论数 