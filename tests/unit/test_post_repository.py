import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlmodel import select, func
from src.repositories.post_repository import PostRepository
from src.models.post import Post
from src.models.user import User


class TestPostRepository:
    """PostRepository单元测试类"""

    @pytest.fixture
    def mock_session(self):
        """模拟数据库会话"""
        return AsyncMock()

    @pytest.fixture
    def post_repository(self, mock_session):
        """创建PostRepository实例"""
        return PostRepository(mock_session)

    @pytest.fixture
    def sample_post(self):
        """示例Post数据"""
        post = Post(
            id=1,
            content="测试评论内容",
            userid=123,
            projectitemid=456,
            posttime="2023-01-01 10:00:00",
            status=1
        )
        return post

    @pytest.fixture
    def sample_message_post(self):
        """示例留言Post数据"""
        post = Post(
            id=1,
            subject="测试留言标题",
            userid=123,
            projectitemid=0,  # 留言本
            rootid=0,  # 主贴
            posttime="2023-01-01 10:00:00",
            status=1,
            lastreplyid=456,
            replycount=3
        )
        return post

    @pytest.mark.unit
    def test_init(self, mock_session):
        """测试PostRepository初始化"""
        repo = PostRepository(mock_session)
        assert repo.session == mock_session

    @pytest.mark.unit
    async def test_get_recent_comments_success(self, post_repository, mock_session, sample_post):
        """测试获取最新评论成功（单条 JOIN 查询，含用户名）"""
        mock_result = MagicMock()
        mock_result.all.return_value = [(sample_post, "测试用户", 42)]
        mock_session.exec.return_value = mock_result

        result = await post_repository.get_recent_comments(5)

        assert len(result) == 1
        assert result[0]["id"] == 1
        assert result[0]["content"] == "测试评论内容"
        assert result[0]["author_name"] == "测试用户"
        assert result[0]["projectitemid"] == 456
        assert result[0]["userid"] == 123
        assert result[0]["author_blog_id"] == 42
        mock_session.exec.assert_called_once()

    @pytest.mark.unit
    async def test_get_recent_comments_empty(self, post_repository, mock_session):
        """测试获取最新评论为空"""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.exec.return_value = mock_result

        result = await post_repository.get_recent_comments(5)

        assert len(result) == 0

    @pytest.mark.unit
    async def test_get_recent_comments_multiple(self, post_repository, mock_session):
        """测试获取多个最新评论"""
        post1 = Post(id=1, content="评论1", userid=1, projectitemid=1, posttime="2023-01-01 10:00:00", status=1)
        post2 = Post(id=2, content="评论2", userid=2, projectitemid=1, posttime="2023-01-01 09:00:00", status=1)

        mock_result = MagicMock()
        mock_result.all.return_value = [(post1, "用户1", 10), (post2, "用户2", 20)]
        mock_session.exec.return_value = mock_result

        result = await post_repository.get_recent_comments(5)

        assert len(result) == 2
        assert result[0]["id"] == 1
        assert result[1]["id"] == 2

    @pytest.mark.unit
    async def test_get_recent_comments_by_project_includes_anonymous(
        self, post_repository, mock_session
    ):
        """博客最近评论应包含匿名评论（outer join users）。"""
        from sqlalchemy.dialects import postgresql

        anonymous_post = Post(
            id=2,
            content="匿名评论",
            userid=0,
            projectitemid=456,
            posttime="2026-04-16 13:12:33",
            status=1,
        )
        mock_result = MagicMock()
        mock_result.all.return_value = [(anonymous_post, None, "测试文章", None)]
        mock_session.exec.return_value = mock_result

        result = await post_repository.get_recent_comments_by_project(23, 5)

        assert len(result) == 1
        assert result[0]["user_name"] == "匿名用户"
        statement = mock_session.exec.call_args[0][0]
        sql = str(statement.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))
        assert "LEFT OUTER JOIN" in sql.upper()

    @pytest.mark.unit
    async def test_get_by_project_item_id_paginated_includes_author(
        self, post_repository, mock_session, sample_post
    ):
        """分页评论含 author_name 与 author_avatar"""
        mock_count = MagicMock()
        mock_count.first.return_value = 1
        mock_rows = MagicMock()
        mock_rows.all.return_value = [(sample_post, "测试用户", 99)]
        mock_session.exec.side_effect = [mock_count, mock_rows]

        with patch(
            "src.repositories.post_repository.check_avatar_exists",
            return_value="/avatar/1/s_123.jpg",
        ):
            result = await post_repository.get_by_project_item_id_paginated(
                456, page=1, per_page=10
            )

        assert len(result["comments"]) == 1
        assert result["comments"][0]["author_name"] == "测试用户"
        assert result["comments"][0]["author_avatar"] == "/avatar/1/s_123.jpg"
        assert result["comments"][0]["author_blog_id"] == 99
        assert result["pagination"]["total"] == 1
        assert result["pagination"]["has_next"] is False

    @pytest.mark.unit
    async def test_count_comments_success(self, post_repository, mock_session):
        """测试获取评论总数成功"""
        mock_result = MagicMock()
        mock_result.first.return_value = 150
        mock_session.exec.return_value = mock_result

        result = await post_repository.count_comments()

        assert result == 150
        mock_session.exec.assert_called_once()

    @pytest.mark.unit
    async def test_count_comments_zero(self, post_repository, mock_session):
        """测试获取评论总数为0"""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result

        result = await post_repository.count_comments()

        assert result == 0

    @pytest.mark.unit
    async def test_count_messages_success(self, post_repository, mock_session):
        """测试获取留言本总数成功"""
        mock_result = MagicMock()
        mock_result.first.return_value = 50
        mock_session.exec.return_value = mock_result

        result = await post_repository.count_messages()

        assert result == 50
        mock_session.exec.assert_called_once()

    @pytest.mark.unit
    async def test_count_messages_zero(self, post_repository, mock_session):
        """测试获取留言本总数为0"""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result

        result = await post_repository.count_messages()

        assert result == 0

    @pytest.mark.unit
    async def test_get_recent_messages_success(self, post_repository, mock_session, sample_message_post):
        """测试获取最新留言成功（单条 JOIN 查询，含作者与最后回复用户名）"""
        mock_result = MagicMock()
        mock_result.all.return_value = [(sample_message_post, "测试用户", "回复用户")]
        mock_session.exec.return_value = mock_result

        result = await post_repository.get_recent_messages(5)

        assert len(result) == 1
        assert result[0]["id"] == 1
        assert result[0]["subject"] == "测试留言标题"
        assert result[0]["userid"] == 123
        assert result[0]["replycount"] == 3
        assert result[0]["author_name"] == "测试用户"
        assert result[0]["last_reply_author"] == "回复用户"

    @pytest.mark.unit
    async def test_get_recent_messages_no_last_reply(self, post_repository, mock_session):
        """测试获取最新留言时无最后回复"""
        post = Post(
            id=1,
            subject="测试留言标题",
            userid=123,
            projectitemid=0,
            rootid=0,
            posttime="2023-01-01 10:00:00",
            status=1,
            lastreplyid=0,  # 无最后回复
            replycount=0
        )

        mock_result = MagicMock()
        mock_result.all.return_value = [(post, "测试用户", None)]
        mock_session.exec.return_value = mock_result

        result = await post_repository.get_recent_messages(5)

        assert len(result) == 1
        assert result[0]["replycount"] == 0
        assert result[0]["last_reply_author"] == "匿名用户"

    @pytest.mark.unit
    async def test_get_recent_messages_last_reply_exception(self, post_repository, mock_session, sample_message_post):
        """测试获取最新留言时最后回复用户未关联（JOIN 无匹配）"""
        mock_result = MagicMock()
        mock_result.all.return_value = [(sample_message_post, "测试用户", None)]
        mock_session.exec.return_value = mock_result

        result = await post_repository.get_recent_messages(5)

        assert len(result) == 1
        assert result[0]["last_reply_author"] == "未知用户"

    @pytest.mark.unit
    async def test_get_recent_messages_empty(self, post_repository, mock_session):
        """测试获取最新留言为空"""
        mock_result = MagicMock()
        mock_result.__iter__.return_value = []
        mock_session.exec.return_value = mock_result

        result = await post_repository.get_recent_messages(5)

        assert len(result) == 0

    @pytest.mark.unit
    async def test_get_recent_messages_with_null_replycount(self, post_repository, mock_session):
        """测试获取最新留言时回复数为空"""
        post = Post(
            id=1,
            subject="测试留言标题",
            userid=123,
            projectitemid=0,
            rootid=0,
            posttime="2023-01-01 10:00:00",
            status=1,
            lastreplyid=0,
            replycount=None
        )

        mock_result = MagicMock()
        mock_result.all.return_value = [(post, "测试用户", None)]
        mock_session.exec.return_value = mock_result

        result = await post_repository.get_recent_messages(5)

        assert result[0]["reply_count"] == 0  # None值转换为0