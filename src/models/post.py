from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from pydantic import ConfigDict

class Post(SQLModel, table=True):
    __tablename__ = "post"
    
    model_config = ConfigDict(validate_by_name=True)
    
    id: Optional[int] = Field(default=None, primary_key=True)
    folderid: Optional[int] = Field(default=None)
    rootid: Optional[int] = Field(default=None)
    userid: Optional[int] = Field(default=None)
    subject: Optional[str] = Field(max_length=200, default=None)
    content: Optional[str] = Field(default=None)
    size: Optional[int] = Field(default=None)
    status: Optional[int] = Field(default=None)
    hits: Optional[int] = Field(default=None)
    posttime: Optional[datetime] = Field(default=None)
    lastreplytime: Optional[datetime] = Field(default=None)
    lastreplyid: Optional[int] = Field(default=None)
    projectitemid: Optional[int] = Field(default=None)  # 0表示留言本，>0表示博文评论
    replycount: Optional[int] = Field(default=None)
    userip: Optional[str] = Field(max_length=15, default=None) 