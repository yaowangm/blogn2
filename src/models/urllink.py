from sqlmodel import SQLModel, Field
from typing import Optional

class UrlLink(SQLModel, table=True):
    __tablename__ = "urllink"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    subject: str = Field(max_length=200)
    linkstr: str = Field(max_length=200)
    projectid: Optional[int] = Field(default=None)
    ordernum: Optional[int] = Field(default=0)
