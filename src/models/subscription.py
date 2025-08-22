from sqlmodel import SQLModel, Field
from typing import Optional
from pydantic import ConfigDict

class Subscription(SQLModel, table=True):
    __tablename__ = "subsc"
    
    model_config = ConfigDict(validate_by_name=True)
    
    id: Optional[int] = Field(default=None, primary_key=True)
    projectid: Optional[int] = Field(default=None, foreign_key="project.id")
    piid: Optional[int] = Field(default=None, foreign_key="projectitem.id")
