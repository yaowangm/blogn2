from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from pydantic import ConfigDict

class User(SQLModel, table=True):
    __tablename__ = "users"
    
    model_config = ConfigDict(validate_by_name=True)
    
    id: Optional[int] = Field(default=None, primary_key=True, alias="ID")
    name: str = Field(max_length=50, alias="Name")
    password: str = Field(max_length=50, alias="Password")
    state: int = Field(default=1, alias="State")
    email: str = Field(max_length=50, alias="Email")
    regtime: datetime = Field(alias="Regtime")
    iplog: Optional[str] = Field(max_length=15, default=None, alias="Iplog")
    projectid: Optional[int] = Field(default=None, alias="Projectid")
    point: Optional[int] = Field(default=0, alias="Point")
    lastupdate: Optional[datetime] = Field(default=None, alias="Lastupdate")
    intropiid: Optional[int] = Field(default=None, alias="Intropiid") 