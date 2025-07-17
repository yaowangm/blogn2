from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class ProjectItem(SQLModel, table=True):
    __tablename__ = "projectitem"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    projectid: Optional[int] = Field(default=None)
    name: str = Field(max_length=100)
    comment: Optional[str] = Field(default=None)
    itemtype: Optional[int] = Field(default=None)
    itemsize: Optional[int] = Field(default=None)
    attachment: Optional[str] = Field(max_length=200, default=None)
    linkstr: Optional[str] = Field(max_length=200, default=None)
    userid: Optional[int] = Field(default=None)
    accesscount: Optional[int] = Field(default=None)
    updatetime: Optional[datetime] = Field(default=None)
    commentcount: Optional[int] = Field(default=None)
    createtime: Optional[datetime] = Field(default=None)
    FOLDERID: Optional[int] = Field(default=None)
    lastmodifytime: Optional[datetime] = Field(default=None)
    status: Optional[int] = Field(default=None)
    allowpost: Optional[int] = Field(default=None)
    
    class Config:
        allow_population_by_field_name = True 