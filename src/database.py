import logging
from sqlmodel import SQLModel, create_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# 导入模型
from src.models.user import User
from src.models.project_item import ProjectItem
from src.models.post import Post
from src.models.subscription import Subscription
from src.models.urllink import UrlLink
from src.models.relation import Relation

# 加载环境变量
load_dotenv()

# 数据库URL - 必须从环境变量获取
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL 环境变量未设置，请在 .env 文件中配置数据库连接信息")

# 创建异步引擎
async_engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # 关闭SQL语句输出
    future=True
)

# 创建同步引擎（用于创建表）
sync_engine = create_engine(
    DATABASE_URL.replace("+asyncpg", "+psycopg2"),
    echo=False  # 关闭SQL语句输出
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

# 创建所有表
def create_db_and_tables():
    SQLModel.metadata.create_all(sync_engine)

# 初始化数据库
if __name__ == "__main__":
    create_db_and_tables()
    logger.info("数据库表创建完成！") 