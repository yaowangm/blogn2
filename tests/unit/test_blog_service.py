import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import os
from src.services.blog_service import BlogService
from src.utils.time_utils import TimeUtils


class TestBlogService:
    """BlogService单元测试类"""
    
    @pytest.fixture
    def mock_user_repo(self):
        """模拟用户仓库"""
        return AsyncMock()
    
    @pytest.fixture
    def mock_project_item_repo(self):
        """模拟项目项仓库"""
        return AsyncMock()
    
    @pytest.fixture
    def mock_project_repo(self):
        """模拟项目仓库"""
        return AsyncMock()
    
    @pytest.fixture
    def mock_post_repo(self):
        """模拟博文仓库"""
        return AsyncMock()
    
    @pytest.fixture
    def blog_service(self, mock_user_repo, mock_project_item_repo, mock_project_repo, mock_post_repo):
        """创建BlogService实例"""
        return BlogService(mock_user_repo, mock_project_item_repo, mock_project_repo, mock_post_repo)
    
    @pytest.fixture
    def sample_project_data(self):
        """示例项目数据"""
        return {
            "id": 1,
            "name": "测试博客",
            "createtime": TimeUtils.now_utc() - timedelta(days=1),
            "userid": 123,
            "accesscount": 1500,
            "author_name": "测试作者"
        }
    
    @pytest.fixture
    def sample_comment_data(self):
        """示例评论数据"""
        return {
            "id": 1,
            "author_name": "评论者",
            "content": "这是一条测试评论",
            "post_time": TimeUtils.now_utc() - timedelta(hours=2),
            "projectitemid": 456,
            "userid": 789
        }
    
    @pytest.fixture
    def sample_message_data(self):
        """示例留言数据"""
        return {
            "id": 1,
            "author_name": "留言者",
            "subject": "测试留言标题",
            "post_time": TimeUtils.now_utc() - timedelta(hours=1),
            "userid": 101,
            "last_reply_author": "回复者",
            "reply_count": 3
        }
    
    @pytest.fixture
    def sample_post_data(self):
        """示例博文数据"""
        return {
            "id": 1,
            "name": "测试博文标题",
            "comment": "这是博文内容摘要",
            "createtime": TimeUtils.now_utc() - timedelta(hours=3),
            "userid": 202,
            "author_name": "博文作者",
            "blog_name": "测试博客",
            "blog_id": 456,
            "attachment": "test.jpg"
        }
    
    @pytest.mark.unit
    async def test_init(self, mock_user_repo, mock_project_item_repo, mock_project_repo, mock_post_repo):
        """测试BlogService初始化"""
        service = BlogService(mock_user_repo, mock_project_item_repo, mock_project_repo, mock_post_repo)
        
        assert service.user_repo == mock_user_repo
        assert service.project_item_repo == mock_project_item_repo
        assert service.project_repo == mock_project_repo
        assert service.post_repo == mock_post_repo
    
    @pytest.mark.unit
    @patch('os.path.exists')
    def test_check_avatar_exists_success(self, mock_exists, blog_service, monkeypatch):
        """测试检查头像存在成功"""
        # 设置测试环境变量，确保使用测试期望的路径
        monkeypatch.setenv("AVATAR_DIR", "../pic/blogn_img/userlogo")
        
        mock_exists.return_value = True
        
        result = blog_service._check_avatar_exists(12345)
        
        expected_path = "/avatar/2/s_12345.jpg"
        assert result == expected_path
        # 检查是否被调用，但不限制调用次数，因为配置加载也会调用
        assert mock_exists.called
        # 检查最后一次调用是否是正确的路径
        assert mock_exists.call_args[0][0] == "../pic/blogn_img/userlogo/2/s_12345.jpg"
    
    @pytest.mark.unit
    @patch('os.path.exists')
    def test_check_avatar_exists_not_found(self, mock_exists, blog_service, monkeypatch):
        """测试检查头像不存在"""
        # 设置测试环境变量，确保使用测试期望的路径
        monkeypatch.setenv("AVATAR_DIR", "../pic/blogn_img/userlogo")
        
        mock_exists.return_value = False
        
        result = blog_service._check_avatar_exists(12345)
        
        assert result is None
        # 检查是否被调用，但不限制调用次数，因为配置加载也会调用
        assert mock_exists.called
        # 检查最后一次调用是否是正确的路径
        assert mock_exists.call_args[0][0] == "../pic/blogn_img/userlogo/2/s_12345.jpg"
    
    @pytest.mark.unit
    def test_check_avatar_exists_no_userid(self, blog_service):
        """测试检查头像时用户ID为空"""
        result = blog_service._check_avatar_exists(None)
        assert result is None
    
    @pytest.mark.unit
    def test_check_avatar_exists_zero_userid(self, blog_service):
        """测试检查头像时用户ID为0"""
        result = blog_service._check_avatar_exists(0)
        assert result is None
    
    @pytest.mark.unit
    async def test_get_recent_blogs_success(self, blog_service, mock_project_repo, sample_project_data):
        """测试获取最新博客成功"""
        mock_project_repo.get_recent_projects.return_value = [sample_project_data]
        
        result = await blog_service.get_recent_blogs(5)
        
        assert len(result) == 1
        assert result[0]["id"] == 1
        assert result[0]["name"] == "测试博客"
        assert result[0]["userid"] == 123
        assert "昨天" in result[0]["join_date"]  # 相对时间格式
        mock_project_repo.get_recent_projects.assert_called_once_with(5)
    
    @pytest.mark.unit
    async def test_get_recent_blogs_with_null_createtime(self, blog_service, mock_project_repo):
        """测试获取最新博客时创建时间为空"""
        project_data = {
            "id": 1,
            "name": "测试博客",
            "createtime": None,
            "userid": 123
        }
        mock_project_repo.get_recent_projects.return_value = [project_data]
        
        result = await blog_service.get_recent_blogs(5)
        
        assert len(result) == 1
        assert result[0]["join_date"] == "未知日期"
    
    @pytest.mark.unit
    async def test_get_popular_blogs_success(self, blog_service, mock_project_repo, sample_project_data):
        """测试获取热门博客成功"""
        mock_project_repo.get_popular_projects.return_value = [sample_project_data]
        
        result = await blog_service.get_popular_blogs(3)
        
        assert len(result) == 1
        assert result[0]["id"] == 1
        assert result[0]["name"] == "测试博客"
        assert result[0]["followers"] == "1.5k"  # 1500转换为1.5k
        assert result[0]["rank"] == 1
        assert result[0]["author"] == "测试作者"
        mock_project_repo.get_popular_projects.assert_called_once_with(3)
    
    @pytest.mark.unit
    async def test_get_popular_blogs_small_access_count(self, blog_service, mock_project_repo):
        """测试获取热门博客时访问量小于1000"""
        project_data = {
            "id": 1,
            "name": "测试博客",
            "accesscount": 500,
            "userid": 123,
            "author_name": "测试作者"
        }
        mock_project_repo.get_popular_projects.return_value = [project_data]
        
        result = await blog_service.get_popular_blogs(3)
        
        assert result[0]["followers"] == "500"
    
    @pytest.mark.unit
    async def test_get_recent_comments_success(self, blog_service, mock_post_repo, sample_comment_data):
        """测试获取最新评论成功"""
        mock_post_repo.get_recent_comments.return_value = [sample_comment_data]
        
        result = await blog_service.get_recent_comments(5)
        
        assert len(result) == 1
        assert result[0]["id"] == 1
        assert result[0]["author"] == "评论者"
        assert result[0]["content"] == "这是一条测试评论"
        assert result[0]["projectitemid"] == 456
        assert result[0]["userid"] == 789
        assert "小时前" in result[0]["time"]
        mock_post_repo.get_recent_comments.assert_called_once_with(5)
    
    @pytest.mark.unit
    async def test_get_recent_comments_with_null_post_time(self, blog_service, mock_post_repo):
        """测试获取最新评论时发布时间为空"""
        comment_data = {
            "id": 1,
            "author_name": "评论者",
            "content": "测试评论",
            "post_time": None,
            "projectitemid": 456,
            "userid": 789
        }
        mock_post_repo.get_recent_comments.return_value = [comment_data]
        
        result = await blog_service.get_recent_comments(5)
        
        assert result[0]["time"] == "未知时间"
    
    @pytest.mark.unit
    async def test_get_recent_comments_exception(self, blog_service, mock_post_repo):
        """测试获取最新评论时发生异常"""
        mock_post_repo.get_recent_comments.side_effect = Exception("数据库错误")
        
        result = await blog_service.get_recent_comments(5)
        
        assert result == []
    
    @pytest.mark.unit
    async def test_get_about_content_success(self, blog_service, mock_project_item_repo):
        """测试获取关于页面内容成功"""
        mock_item = MagicMock()
        mock_item.id = 486
        mock_item.comment = "这是关于页面的内容\n包含换行符"
        mock_project_item_repo.get_by_id.return_value = mock_item
        
        # 为 glovar 提供返回值，模拟 intropiid 配置
        blog_service.glovar_repo = AsyncMock()
        blog_service.glovar_repo.get_value.return_value = 486

        result = await blog_service.get_about_content()
        
        assert result["title"] == "Why Blogn"
        assert result["content"] == "这是关于页面的内容<br>包含换行符"
        assert result["link"] == "/article/486"
        mock_project_item_repo.get_by_id.assert_called_once_with(486)
    
    @pytest.mark.unit
    async def test_get_about_content_not_found(self, blog_service, mock_project_item_repo):
        """测试获取关于页面内容时记录不存在"""
        mock_project_item_repo.get_by_id.return_value = None
        
        result = await blog_service.get_about_content()
        
        assert result["title"] == "Why Blogn"
        assert result["content"] == "内容暂不可用"
        assert result["link"] is None
    
    @pytest.mark.unit
    async def test_get_about_content_long_content(self, blog_service, mock_project_item_repo):
        """测试获取关于页面内容时内容过长"""
        long_content = "a" * 400
        mock_item = MagicMock()
        mock_item.id = 486
        mock_item.comment = long_content
        mock_project_item_repo.get_by_id.return_value = mock_item
        
        # 为 glovar 提供返回值，模拟 intropiid 配置
        blog_service.glovar_repo = AsyncMock()
        blog_service.glovar_repo.get_value.return_value = 486

        result = await blog_service.get_about_content()
        
        assert len(result["content"]) <= 303  # 300 + "..."
        assert result["content"].endswith("...")
    
    @pytest.mark.unit
    async def test_get_about_content_exception(self, blog_service, mock_project_item_repo):
        """测试获取关于页面内容时发生异常"""
        mock_project_item_repo.get_by_id.side_effect = Exception("数据库错误")
        
        result = await blog_service.get_about_content()
        
        assert result["title"] == "Why Blogn"
        assert result["content"] == "内容暂不可用"
        assert result["link"] is None
    
    @pytest.mark.unit
    async def test_get_recent_messages_success(self, blog_service, mock_post_repo, sample_message_data):
        """测试获取最新留言成功"""
        mock_post_repo.get_recent_messages.return_value = [sample_message_data]
        
        result = await blog_service.get_recent_messages(5)
        
        assert len(result) == 1
        assert result[0]["id"] == 1
        assert result[0]["author"] == "留言者"
        assert result[0]["subject"] == "测试留言标题"
        assert result[0]["userid"] == 101
        assert result[0]["reply_info"] == "最后回复: 回复者"
        assert result[0]["reply_count"] == 3
        assert "小时前" in result[0]["time"]
        mock_post_repo.get_recent_messages.assert_called_once_with(5)
    
    @pytest.mark.unit
    async def test_get_recent_messages_long_subject(self, blog_service, mock_post_repo):
        """测试获取最新留言时标题过长"""
        message_data = {
            "id": 1,
            "author_name": "留言者",
            "subject": "这是一个非常非常长的留言标题，超过了50个字符的限制，应该被截断并添加省略号，确保测试能够正确验证截断逻辑",
            "post_time": TimeUtils.now_utc() - timedelta(hours=1),
            "userid": 101,
            "last_reply_author": None,
            "reply_count": 2
        }
        mock_post_repo.get_recent_messages.return_value = [message_data]
        
        result = await blog_service.get_recent_messages(5)
        
        assert len(result[0]["subject"]) <= 53  # 50 + "..."
        assert len(result[0]["subject"]) <= 53  # 50 + "..."
        assert result[0]["subject"].endswith("...")
        assert result[0]["reply_info"] == "回复数: 2"
    
    @pytest.mark.unit
    async def test_get_recent_messages_no_reply_info(self, blog_service, mock_post_repo):
        """测试获取最新留言时无回复信息"""
        message_data = {
            "id": 1,
            "author_name": "留言者",
            "subject": "测试标题",
            "post_time": TimeUtils.now_utc() - timedelta(hours=1),
            "userid": 101,
            "last_reply_author": None,
            "reply_count": 0
        }
        mock_post_repo.get_recent_messages.return_value = [message_data]
        
        result = await blog_service.get_recent_messages(5)
        
        assert result[0]["reply_info"] == ""
    
    @pytest.mark.unit
    async def test_get_recent_messages_exception(self, blog_service, mock_post_repo):
        """测试获取最新留言时发生异常"""
        mock_post_repo.get_recent_messages.side_effect = Exception("数据库错误")
        
        result = await blog_service.get_recent_messages(5)
        
        assert result == []
    
    @pytest.mark.unit
    async def test_get_latest_posts_success(self, blog_service, mock_project_item_repo, sample_post_data):
        """测试获取最新博文成功"""
        mock_project_item_repo.get_latest_posts.return_value = [sample_post_data]
        mock_project_item_repo.get_posts_count.return_value = 1
        
        result = await blog_service.get_latest_posts(1, 5)
        
        assert result["total"] == 1
        assert result["page"] == 1
        assert result["page_size"] == 5
        assert result["total_pages"] == 1
        assert len(result["posts"]) == 1
        assert result["posts"][0]["id"] == 1
        assert result["posts"][0]["title"] == "测试博文标题"
        assert result["posts"][0]["excerpt"] == "这是博文内容摘要"
        assert result["posts"][0]["author"] == "博文作者"
        assert result["posts"][0]["userid"] == 202
        assert result["posts"][0]["image"] == "/upload/test.jpg"
        assert "小时前" in result["posts"][0]["time"]
        mock_project_item_repo.get_latest_posts.assert_called_once_with(5, None, None, 0)
        mock_project_item_repo.get_posts_count.assert_called_once_with(None, None)
    
    @pytest.mark.unit
    async def test_get_latest_posts_long_title_and_excerpt(self, blog_service, mock_project_item_repo):
        """测试获取最新博文时标题和摘要过长"""
        post_data = {
            "id": 1,
            "name": "这是一个非常非常长的博文标题，超过了50个字符的限制，应该被截断并添加省略号，确保测试能够正确验证截断逻辑",
            "comment": "这是一个非常非常长的博文摘要内容，超过了100个字符的限制，应该被截断并添加省略号，确保测试能够正确验证截断逻辑，这是一个非常长的内容，需要更多的文字来达到100个字符的限制，这是额外的内容来确保测试能够正确工作",
            "createtime": TimeUtils.now_utc() - timedelta(hours=3),
            "userid": 202,
            "author_name": "博文作者",
            "blog_name": "测试博客",
            "blog_id": 456,
            "attachment": None
        }
        mock_project_item_repo.get_latest_posts.return_value = [post_data]
        
        mock_project_item_repo.get_posts_count.return_value = 1
        result = await blog_service.get_latest_posts(1, 5)
        
        assert len(result["posts"][0]["title"]) <= 53  # 50 + "..."
        assert result["posts"][0]["title"].endswith("...")
        assert len(result["posts"][0]["excerpt"]) <= 103  # 100 + "..."
        assert result["posts"][0]["excerpt"].endswith("...")
        assert result["posts"][0]["image"] is None
    
    @pytest.mark.unit
    async def test_get_latest_posts_exception(self, blog_service, mock_project_item_repo):
        """测试获取最新博文时发生异常"""
        mock_project_item_repo.get_latest_posts.side_effect = Exception("数据库错误")
        
        result = await blog_service.get_latest_posts(1, 5)
        
        assert result["posts"] == []
        assert result["total"] == 0
        assert result["page"] == 1
        assert result["page_size"] == 5
        assert result["total_pages"] == 0
    
    @pytest.mark.unit
    def test_format_relative_time_just_now(self, blog_service):
        """测试格式化时间：刚刚"""
        from src.utils.time_utils import TimeUtils
        now = TimeUtils.now_utc()
        result = TimeUtils.format_relative_time(now)
        assert result == "刚刚"
    
    @pytest.mark.unit
    def test_format_relative_time_minutes_ago(self, blog_service):
        """测试格式化时间：分钟前"""
        from src.utils.time_utils import TimeUtils
        now = TimeUtils.now_utc()
        past_time = now - timedelta(minutes=30)
        result = TimeUtils.format_relative_time(past_time)
        assert result == "30分钟前"
    
    @pytest.mark.unit
    def test_format_relative_time_hours_ago(self, blog_service):
        """测试格式化时间：小时前"""
        from src.utils.time_utils import TimeUtils
        now = TimeUtils.now_utc()
        past_time = now - timedelta(hours=2)
        result = TimeUtils.format_relative_time(past_time)
        assert result == "2小时前"
    
    @pytest.mark.unit
    def test_format_relative_time_yesterday(self, blog_service):
        """测试格式化时间：昨天"""
        from src.utils.time_utils import TimeUtils
        now = TimeUtils.now_utc()
        yesterday = now - timedelta(days=1)
        result = TimeUtils.format_relative_time(yesterday)
        assert result == "昨天"
    
    @pytest.mark.unit
    def test_format_relative_time_day_before_yesterday(self, blog_service):
        """测试格式化时间：前天"""
        from src.utils.time_utils import TimeUtils
        now = TimeUtils.now_utc()
        day_before_yesterday = now - timedelta(days=2)
        result = TimeUtils.format_relative_time(day_before_yesterday)
        assert result == "前天"
    
    @pytest.mark.unit
    def test_format_relative_time_other_days(self, blog_service):
        """测试格式化时间：其他日期"""
        from src.utils.time_utils import TimeUtils
        past_time = datetime(2023, 1, 15)
        result = TimeUtils.format_relative_time(past_time)
        assert result == "2023-01-15"
    
    @pytest.mark.unit
    async def test_get_recent_messages_with_null_post_time(self, blog_service, mock_post_repo):
        """测试获取最新留言时发布时间为空"""
        message_data = {
            "id": 1,
            "author_name": "留言者",
            "subject": "测试标题",
            "post_time": None,
            "userid": 101,
            "last_reply_author": None,
            "reply_count": 0
        }
        mock_post_repo.get_recent_messages.return_value = [message_data]
        
        result = await blog_service.get_recent_messages(5)
        
        assert result[0]["time"] == "未知时间"
    
    @pytest.mark.unit
    async def test_get_latest_posts_with_null_createtime(self, blog_service, mock_project_item_repo):
        """测试获取最新博文时创建时间为空"""
        post_data = {
            "id": 1,
            "name": "测试博文标题",
            "comment": "测试内容",
            "createtime": None,
            "userid": 202,
            "author_name": "博文作者",
            "blog_name": "测试博客",
            "blog_id": 456,
            "attachment": None
        }
        mock_project_item_repo.get_latest_posts.return_value = [post_data]
        
        mock_project_item_repo.get_posts_count.return_value = 1
        result = await blog_service.get_latest_posts(1, 5)
        
        assert result["posts"][0]["time"] == "未知时间" 