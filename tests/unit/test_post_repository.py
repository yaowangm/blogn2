import pytest
from unittest.mock import AsyncMock, MagicMock
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
        """测试获取最新评论成功"""
        # 模拟用户查询结果
        mock_user_result = MagicMock()
        mock_user_result.first.return_value = "测试用户"
        
        # 模拟评论查询结果
        mock_result = MagicMock()
        mock_result.all.return_value = [sample_post]
        
        # 设置exec的返回值，第一次调用返回评论，第二次调用返回用户名
        mock_session.exec.side_effect = [mock_result, mock_user_result]
        
        result = await post_repository.get_recent_comments(5)
        
        assert len(result) == 1
        assert result[0]["id"] == 1
        assert result[0]["content"] == "测试评论内容"
        assert result[0]["author_name"] == "测试用户"
        assert result[0]["projectitemid"] == 456
        assert result[0]["userid"] == 123
        assert mock_session.exec.call_count == 2  # 一次查询评论，一次查询用户名
    
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
        mock_result.all.return_value = [post1, post2]
        mock_session.exec.return_value = mock_result
        
        result = await post_repository.get_recent_comments(5)
        
        assert len(result) == 2
        assert result[0]["id"] == 1
        assert result[1]["id"] == 2
    
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
        """测试获取最新留言成功"""
        mock_result = MagicMock()
        mock_result.all.return_value = [sample_message_post]
        mock_session.exec.return_value = mock_result
        
        result = await post_repository.get_recent_messages(5)
        
        assert len(result) == 1
        assert result[0]["id"] == 1
        assert result[0]["subject"] == "测试留言标题"
        assert result[0]["userid"] == 123
        assert result[0]["replycount"] == 3
    
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
        mock_result.all.return_value = [post]
        mock_session.exec.return_value = mock_result
        
        result = await post_repository.get_recent_messages(5)
        
        assert len(result) == 1
        assert result[0]["replycount"] == 0
    
    @pytest.mark.unit
    async def test_get_recent_messages_last_reply_exception(self, post_repository, mock_session, sample_message_post):
        """测试获取最新留言时最后回复查询异常"""
        # 模拟用户查询结果（作者）
        mock_user_result = MagicMock()
        mock_user_result.first.return_value = "测试用户"
        
        # 模拟最后回复用户查询结果（异常情况）
        mock_last_reply_result = MagicMock()
        mock_last_reply_result.first.side_effect = Exception("数据库查询异常")
        
        # 模拟评论查询结果
        mock_result = MagicMock()
        mock_result.all.return_value = [sample_message_post]
        
        # 设置exec的返回值，第一次调用返回留言，第二次调用返回作者用户名，第三次调用返回最后回复用户名（异常）
        mock_session.exec.side_effect = [mock_result, mock_user_result, mock_last_reply_result]
        
        result = await post_repository.get_recent_messages(5)
        
        assert len(result) == 1
        assert result[0]["last_reply_author"] == "未知用户"  # 异常时返回"未知用户"
    
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
        mock_result.all.return_value = [post]
        mock_session.exec.return_value = mock_result
        
        result = await post_repository.get_recent_messages(5)
        
        assert result[0]["reply_count"] == 0  # None值转换为0 