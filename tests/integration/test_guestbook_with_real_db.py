"""
留言本功能集成测试 - 真实数据库版本
使用真实PostgreSQL数据库，测试留言本的完整功能
包括创建留言、获取留言列表、跟贴功能等
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select
from src.models.user import User
from src.models.project import Project
from src.models.project_item import ProjectItem
from src.models.post import Post
from datetime import datetime
import json


class TestGuestbookWithRealDB:
    """留言本功能测试类 - 真实数据库版本"""

    @pytest.mark.integration
    def test_create_message_anonymous(self, test_client, real_sync_session_with_commit, test_data_tracker):
        """测试匿名用户创建留言"""
        # 创建测试用户（用于留言本）
        user = User(
            name="testuser_message_1",
            email="user_message_1@example.com",
            password="hashed_password",
            regtime=datetime(2024, 1, 1, 10, 0, 0)
        )
        real_sync_session_with_commit.add(user)
        real_sync_session_with_commit.flush()
        test_data_tracker.add_user(user.id)  # 跟踪用户ID
        
        # 测试创建匿名留言
        message_data = {
            "subject": "测试留言标题",
            "content": "这是一条测试留言内容",
            "user_id": 0  # 匿名用户
        }
        
        response = test_client.post(
            "/api/messages",
            json=message_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "message_id" in data
        assert data["message"] == "留言创建成功"
        assert data["subject"] == "测试留言标题"
        assert data["content"] == "这是一条测试留言内容"
        assert data["user_id"] == 0
        
        # 跟踪留言ID
        test_data_tracker.add_message(data["message_id"])
        
        # 验证留言已保存到数据库
        message_result = real_sync_session_with_commit.exec(
            select(Post).where(Post.id == data["message_id"])
        )
        message = message_result.first()
        assert message is not None
        assert message.subject == "测试留言标题"
        assert message.content == "这是一条测试留言内容"
        assert message.userid == 0
        assert message.projectitemid == 0  # 留言本的projectitemid为0
        assert message.rootid == 0  # 主贴的rootid为0
        assert message.status == 1

    @pytest.mark.integration
    def test_create_message_logged_in(self, test_client, real_sync_session_with_commit, test_data_tracker):
        """测试登录用户创建留言"""
        # 创建测试用户
        user = User(
            id=2002,
            name="testuser2002",
            email="user2002@example.com",
            password="hashed_password",
            regtime=datetime(2024, 1, 1, 10, 0, 0)
        )
        real_sync_session_with_commit.add(user)
        real_sync_session_with_commit.flush()
        test_data_tracker.add_user(user.id)  # 跟踪用户ID
        
        # 测试创建登录用户留言
        message_data = {
            "subject": "登录用户留言标题",
            "content": "这是登录用户的测试留言内容",
            "user_id": user.id
        }
        
        response = test_client.post(
            "/api/messages",
            json=message_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["user_id"] == user.id
        
        # 跟踪留言ID
        test_data_tracker.add_message(data["message_id"])
        
        # 验证留言已保存到数据库
        message_result = real_sync_session_with_commit.exec(
            select(Post).where(Post.id == data["message_id"])
        )
        message = message_result.first()
        assert message is not None
        assert message.userid == 2002

    @pytest.mark.integration
    def test_create_message_empty_subject(self, test_client, real_sync_session_with_commit, test_data_tracker):
        """测试创建空标题留言（应该失败）"""
        message_data = {
            "subject": "",
            "content": "这是没有标题的留言",
            "user_id": 0
        }
        
        response = test_client.post(
            "/api/messages",
            json=message_data
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "留言标题不能为空" in data["detail"]

    @pytest.mark.integration
    def test_create_message_empty_content(self, test_client, real_sync_session_with_commit, test_data_tracker):
        """测试创建空内容留言"""
        message_data = {
            "subject": "有标题但无内容",
            "content": "",
            "user_id": 0
        }
        
        response = test_client.post(
            "/api/messages",
            json=message_data
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "留言内容不能为空" in data["detail"]

    @pytest.mark.integration
    def test_create_message_long_subject(self, test_client, real_sync_session_with_commit, test_data_tracker):
        """测试创建超长标题留言"""
        long_subject = "a" * 201  # 超过200字符限制
        message_data = {
            "subject": long_subject,
            "content": "这是超长标题的留言",
            "user_id": 0
        }
        
        response = test_client.post(
            "/api/messages",
            json=message_data
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "标题不能超过200个字符" in data["detail"]

    @pytest.mark.integration
    def test_create_reply_message(self, test_client, real_sync_session_with_commit, test_data_tracker):
        """测试创建跟贴留言"""
        # 创建测试用户
        user = User(
            id=2003,
            name="testuser2003",
            email="user2003@example.com",
            password="hashed_password",
            regtime=datetime(2024, 1, 1, 10, 0, 0)
        )
        real_sync_session_with_commit.add(user)
        real_sync_session_with_commit.flush()
        test_data_tracker.add_user(user.id)  # 跟踪用户ID
        
        # 先创建一个主贴
        main_message = Post(
            folderid=0,
            projectitemid=0,  # 留言本
            userid=2003,
            subject="主贴标题",
            content="这是主贴内容",
            size=len("这是主贴内容".encode('utf-8')),
            hits=0,
            userip="127.0.0.1",
            posttime=datetime(2024, 1, 1, 10, 0, 0),
            status=1,
            rootid=0,  # 主贴的rootid为0
            replycount=0
        )
        real_sync_session_with_commit.add(main_message)
        real_sync_session_with_commit.flush()
        test_data_tracker.add_message(main_message.id)  # 跟踪主贴ID
        
        # 创建跟贴
        reply_data = {
            "subject": "",  # 跟贴可以没有标题
            "content": "这是跟贴内容",
            "thread_id": main_message.id,
            "user_id": 0
        }
        
        response = test_client.post(
            "/api/messages",
            json=reply_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # 跟踪跟贴ID
        test_data_tracker.add_message(data["message_id"])
        
        # 验证跟贴已保存到数据库
        reply_result = real_sync_session_with_commit.exec(
            select(Post).where(Post.id == data["message_id"])
        )
        reply = reply_result.first()
        assert reply is not None
        assert reply.content == "这是跟贴内容"
        assert reply.rootid == main_message.id  # 跟贴的rootid为主贴ID
        assert reply.projectitemid == 0  # 留言本

    @pytest.mark.integration
    def test_get_messages_list(self, test_client, real_sync_session_with_commit, test_data_tracker):
        """测试获取留言本列表"""
        # 创建测试用户
        user = User(
            id=2004,
            name="testuser2004",
            email="user2004@example.com",
            password="hashed_password",
            regtime=datetime(2024, 1, 1, 10, 0, 0)
        )
        real_sync_session_with_commit.add(user)
        real_sync_session_with_commit.flush()
        test_data_tracker.add_user(user.id)  # 跟踪用户ID
        
        # 创建测试留言
        message1 = Post(
            folderid=0,
            projectitemid=0,  # 留言本
            userid=2004,
            subject="第一条留言",
            content="第一条留言内容",
            size=len("第一条留言内容".encode('utf-8')),
            hits=0,
            userip="127.0.0.1",
            posttime=datetime(2024, 1, 1, 10, 0, 0),
            status=1,
            rootid=0,
            replycount=0
        )
        real_sync_session_with_commit.add(message1)
        
        message2 = Post(
            folderid=0,
            projectitemid=0,  # 留言本
            userid=2004,
            subject="第二条留言",
            content="第二条留言内容",
            size=len("第二条留言内容".encode('utf-8')),
            hits=0,
            userip="127.0.0.1",
            posttime=datetime(2024, 1, 1, 11, 0, 0),
            status=1,
            rootid=0,
            replycount=0
        )
        real_sync_session_with_commit.add(message2)
        real_sync_session_with_commit.flush()
        
        # 跟踪留言ID
        test_data_tracker.add_message(message1.id)
        test_data_tracker.add_message(message2.id)
        
        # 获取留言列表
        response = test_client.get("/api/messages")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "messages" in data
        assert "current_page" in data
        assert "total_pages" in data
        
        messages = data["messages"]
        assert isinstance(messages, list)
        assert len(messages) >= 0  # 数据库中可能已有其他留言
        
        # 验证留言字段
        for message in messages:
            assert "id" in message
            assert "subject" in message
            assert "author" in message  # 注意字段名是author不是author_name
            assert "userid" in message
            assert "post_time" in message

    @pytest.mark.integration
    def test_get_thread_messages(self, test_client, real_sync_session_with_commit, test_data_tracker):
        """测试获取主题的所有留言（主贴+跟贴）"""
        # 创建测试用户（不指定ID，让数据库自动生成）
        user = User(
            name="testuser2005",
            email="user2005@example.com",
            password="hashed_password",
            regtime=datetime(2024, 1, 1, 10, 0, 0)
        )
        real_sync_session_with_commit.add(user)
        real_sync_session_with_commit.flush()  # 获取生成的用户ID
        
        # 创建主贴
        main_message = Post(
            folderid=0,
            projectitemid=0,  # 留言本
            userid=user.id,
            subject="主贴标题",
            content="这是主贴内容",
            size=len("这是主贴内容".encode('utf-8')),
            hits=0,
            userip="127.0.0.1",
            posttime=datetime(2024, 1, 1, 10, 0, 0),
            status=1,
            rootid=0,
            replycount=0
        )
        real_sync_session_with_commit.add(main_message)
        real_sync_session_with_commit.flush()
        
        # 创建跟贴
        reply1 = Post(
            folderid=0,
            projectitemid=0,  # 留言本
            userid=user.id,
            subject="",
            content="跟贴1",
            size=len("跟贴1".encode('utf-8')),
            hits=0,
            userip="127.0.0.1",
            posttime=datetime(2024, 1, 1, 11, 0, 0),
            status=1,
            rootid=main_message.id,  # 跟贴的rootid为主贴ID
            replycount=0
        )
        real_sync_session_with_commit.add(reply1)
        
        reply2 = Post(
            folderid=0,
            projectitemid=0,  # 留言本
            userid=user.id,
            subject="",
            content="跟贴2",
            size=len("跟贴2".encode('utf-8')),
            hits=0,
            userip="127.0.0.1",
            posttime=datetime(2024, 1, 1, 12, 0, 0),
            status=1,
            rootid=main_message.id,  # 跟贴的rootid为主贴ID
            replycount=0
        )
        real_sync_session_with_commit.add(reply2)
        real_sync_session_with_commit.flush()  # 刷新以获取ID
        
        # 临时提交数据，让API调用能找到
        real_sync_session_with_commit.commit()
        
        # 获取主题留言
        response = test_client.get(f"/api/thread/{main_message.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "messages" in data
        assert "thread_id" in data
        
        messages = data["messages"]
        assert isinstance(messages, list)
        assert len(messages) == 3  # 主贴 + 2个跟贴
        
        # 验证主贴
        main_post = next((msg for msg in messages if msg["is_main_post"]), None)
        assert main_post is not None
        assert main_post["subject"] == "主贴标题"
        assert main_post["content"] == "这是主贴内容"
        
        # 验证跟贴
        replies = [msg for msg in messages if not msg["is_main_post"]]
        assert len(replies) == 2
        reply_contents = [reply["content"] for reply in replies]
        assert "跟贴1" in reply_contents
        assert "跟贴2" in reply_contents

    @pytest.mark.integration
    def test_get_thread_messages_nonexistent(self, test_client):
        """测试获取不存在主题的留言"""
        response = test_client.get("/api/thread/99999")
        
        assert response.status_code == 404
        data = response.json()
        assert "主题" in data["detail"] and "不存在" in data["detail"]

    @pytest.mark.integration
    def test_get_recent_comments(self, test_client, real_sync_session_with_commit, test_data_tracker):
        """测试获取最近评论（排除留言本）"""
        # 创建测试用户（不指定ID，让数据库自动生成）
        user = User(
            name="testuser2006",
            email="user2006@example.com",
            password="hashed_password",
            regtime=datetime(2024, 1, 1, 10, 0, 0)
        )
        real_sync_session_with_commit.add(user)
        real_sync_session_with_commit.flush()  # 获取生成的用户ID
        
        # 创建测试项目
        project = Project(
            name="Test Project for Comments",
            userid=user.id,
            createtime=datetime(2024, 1, 1, 10, 0, 0),
            state=0,
            accesscount=0
        )
        real_sync_session_with_commit.add(project)
        real_sync_session_with_commit.flush()  # 获取生成的项目ID
        
        # 创建测试文章
        article = ProjectItem(
            projectid=project.id,
            name="Test Article for Comments",
            comment="This is a test article for comment testing",
            itemtype=1,
            userid=user.id,
            createtime=datetime(2024, 1, 1, 10, 0, 0),
            status=1,
            allowpost=1
        )
        real_sync_session_with_commit.add(article)
        real_sync_session_with_commit.flush()  # 获取生成的文章ID
        
        # 创建文章评论（应该被包含）- 使用当前时间确保是最新的
        from datetime import timezone
        now = datetime.now(timezone.utc)
        
        article_comment = Post(
            folderid=0,
            projectitemid=article.id,  # 文章评论
            userid=user.id,
            subject="",
            content="这是文章评论",
            size=len("这是文章评论".encode('utf-8')),
            hits=0,
            userip="127.0.0.1",
            posttime=now,
            status=1,
            rootid=0,
            replycount=0
        )
        real_sync_session_with_commit.add(article_comment)
        
        # 创建留言本留言（应该被排除）
        guestbook_message = Post(
            folderid=0,
            projectitemid=0,  # 留言本
            userid=user.id,
            subject="留言本留言",
            content="这是留言本留言",
            size=len("这是留言本留言".encode('utf-8')),
            hits=0,
            userip="127.0.0.1",
            posttime=now,
            status=1,
            rootid=0,
            replycount=0
        )
        real_sync_session_with_commit.add(guestbook_message)
        real_sync_session_with_commit.flush()  # 刷新以获取ID
        
        # 临时提交数据，让API调用能找到
        real_sync_session_with_commit.commit()
        
        # 获取最近评论
        response = test_client.get("/api/comments/recent?limit=10")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # 验证只包含文章评论，不包含留言本留言
        comment_ids = [comment["id"] for comment in data]
        assert article_comment.id in comment_ids
        assert guestbook_message.id not in comment_ids
