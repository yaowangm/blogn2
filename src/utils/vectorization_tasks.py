"""后台向量化任务：在独立会话中异步执行，不阻塞 HTTP 响应。"""

import asyncio
import logging

logger = logging.getLogger(__name__)


async def _run_with_session(coro_factory) -> None:
    """在独立 DB 会话中执行向量化操作。"""
    from src.database import async_session

    session = async_session()
    try:
        await coro_factory(session)
        await session.commit()
    except Exception:
        await session.rollback()
        logger.exception("后台向量化任务失败")
    finally:
        await session.close()


def schedule_article_vectorization(article_id: int, title: str, content: str) -> None:
    """文章创建/更新后异步更新向量索引。"""

    async def _factory(session):
        from src.services.vectorization_update_service import get_vectorization_update_service

        svc = get_vectorization_update_service(session)
        await svc.update_article_vectors(article_id, title, content)

    asyncio.create_task(_run_with_session(_factory))


def schedule_comment_vectorization(
    comment_id: int, subject: str, content: str, projectitem_id: int
) -> None:
    """评论/留言创建后异步更新向量索引。"""

    async def _factory(session):
        from src.services.vectorization_update_service import get_vectorization_update_service

        svc = get_vectorization_update_service(session)
        await svc.update_comment_vectors(comment_id, subject, content, projectitem_id)

    asyncio.create_task(_run_with_session(_factory))
