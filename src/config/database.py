from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession
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

# 创建异步会话工厂
async_session = sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# 依赖注入函数
async def get_async_session() -> AsyncSession:
    async with async_session() as session:
        yield session 