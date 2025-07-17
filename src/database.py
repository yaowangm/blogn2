from sqlmodel import SQLModel, Field, create_engine, Session
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker
from typing import Optional
from datetime import datetime
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 数据库URL - 必须通过环境变量设置，不允许硬编码
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL 环境变量未设置。请在 .env 文件中设置数据库连接信息，例如：\n"
        "DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/database_name"
    )

# 创建异步引擎
async_engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # 在开发环境中显示SQL语句
    future=True
)

# 创建同步引擎（用于创建表）
sync_engine = create_engine(
    DATABASE_URL.replace("+asyncpg", "+psycopg2"),
    echo=True
)

# 创建异步会话工厂
async_session = sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# User模型 - 匹配现有数据库表结构
class User(SQLModel, table=True):
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=50)
    password: str = Field(max_length=50)
    state: int = Field(default=1)
    email: str = Field(max_length=50)
    regtime: datetime = Field()
    iplog: Optional[str] = Field(max_length=15, default=None)
    projectid: Optional[int] = Field(default=None)
    point: Optional[int] = Field(default=0)
    lastupdate: Optional[datetime] = Field(default=None)
    intropiid: Optional[int] = Field(default=None)
    
    class Config:
        allow_population_by_field_name = True

# ProjectItem模型 - 匹配现有数据库表结构
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

# 依赖注入函数
async def get_async_session() -> AsyncSession:
    async with async_session() as session:
        yield session

# 创建所有表
def create_db_and_tables():
    SQLModel.metadata.create_all(sync_engine)

# 初始化数据库
if __name__ == "__main__":
    create_db_and_tables()
    print("数据库表创建完成！") 