from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from pydantic import ConfigDict

class Post(SQLModel, table=True):
    __tablename__ = "post"
    
    model_config = ConfigDict(validate_by_name=True)
    
    id: Optional[int] = Field(default=None, primary_key=True, alias="ID")
    folderid: Optional[int] = Field(default=None, alias="Folderid")
    rootid: Optional[int] = Field(default=None, alias="Rootid")
    userid: Optional[int] = Field(default=None, alias="Userid")
    subject: Optional[str] = Field(max_length=200, default=None, alias="Subject")
    content: Optional[str] = Field(default=None, alias="Content")
    size: Optional[int] = Field(default=None, alias="Size")
    status: Optional[int] = Field(default=None, alias="Status")
    hits: Optional[int] = Field(default=None, alias="Hits")
    posttime: Optional[datetime] = Field(default=None, alias="Posttime")
    lastreplytime: Optional[datetime] = Field(default=None, alias="Lastreplytime")
    lastreplyid: Optional[int] = Field(default=None, alias="Lastreplyid")
    projectitemid: Optional[int] = Field(default=None, alias="Projectitemid")  # 0表示留言本，>0表示博文评论
    replycount: Optional[int] = Field(default=None, alias="Replycount")
    userip: Optional[str] = Field(max_length=15, default=None, alias="Userip") 