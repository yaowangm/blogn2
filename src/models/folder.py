from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from pydantic import ConfigDict

class Folder(SQLModel, table=True):
    __tablename__ = "folders"
    
    model_config = ConfigDict(validate_by_name=True)
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    parent: Optional[int] = Field(default=None, foreign_key="folders.id")
    projectid: Optional[int] = Field(default=None, foreign_key="project.id")
    recordcount: Optional[int] = Field(default=None)
    postcount: Optional[int] = Field(default=None)
