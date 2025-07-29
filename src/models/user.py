from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from pydantic import ConfigDict

class User(SQLModel, table=True):
    __tablename__ = "users"
    
    model_config = ConfigDict(validate_by_name=True)
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=50)
    password: str = Field(max_length=50)
    state: int = Field(default=1)
    email: str = Field(max_length=50)
    regtime: datetime
    iplog: Optional[str] = Field(max_length=15, default=None)
    projectid: Optional[int] = Field(default=None)
    point: Optional[int] = Field(default=0)
    lastupdate: Optional[datetime] = Field(default=None)
    intropiid: Optional[int] = Field(default=None) 