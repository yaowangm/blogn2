from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from pydantic import ConfigDict

class RegKey(SQLModel, table=True):
    __tablename__ = "regkey"
    
    model_config = ConfigDict(validate_by_name=True)
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=25, description="注册码")
    ownerid: int = Field(description="申请者用户ID")
    userid: Optional[int] = Field(default=None, description="使用者用户ID")
    status: int = Field(default=1, description="状态：1为未使用，2为已使用")
    createtime: datetime = Field(default_factory=datetime.now, description="创建时间")
    
    @property
    def regkey(self) -> str:
        """兼容性属性，返回name字段"""
        return self.name

class RegKeyWithUserInfo(SQLModel):
    """注册码信息，包含申请者和使用者的详细信息"""
    id: int
    regkey: str
    ownerid: int
    owner_name: str
    userid: Optional[int] = None
    user_name: Optional[str] = None
    status: int
    createtime: datetime
    
    @property
    def status_text(self) -> str:
        """获取状态文本描述"""
        return "已使用" if self.status == 2 else "未使用"
