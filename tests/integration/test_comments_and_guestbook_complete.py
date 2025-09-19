"""
评论和留言本功能完整测试 - 真实数据库版本
使用真实PostgreSQL数据库，测试评论和留言本的完整功能
包括创建、获取、权限验证、数据验证等
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select
from src.models.user import User
from src.models.project import Project
from src.models.project_item import ProjectItem
from src.models.post import Post
from datetime import datetime


class TestCommentsAndGuestbookComplete:
    """评论和留言本功能完整测试类 - 真实数据库版本"""

    @pytest.mark.integration
    def test_article_comment_workflow_create(self, test_client, real_sync_session_with_commit):
        """测试文章评论创建工作流程"""
        # 1. 创建测试用户
        user = User(
            name="testuser_workflow",
            email="user_workflow@example.com",
            password="hashed_password",
            regtime=datetime(2024, 1, 1, 10, 0, 0)
        )
        real_sync_session_with_commit.add(user)
        real_sync_session_with_commit.flush()  # 刷新以获取ID
        # 临时提交数据，让API调用能找到
        real_sync_session_with_commit.commit()
        
        # 2. 创建测试项目
        project = Project(
            name="Test Project Workflow",
            userid=user.id,
            createtime=datetime(2024, 1, 1, 10, 0, 0),
            state=0,
            accesscount=0
        )
        real_sync_session_with_commit.add(project)
        real_sync_session_with_commit.flush()  # 刷新以获取ID
        # 临时提交数据，让API调用能找到
        real_sync_session_with_commit.commit()
        
        # 3. 创建测试文章（允许匿名评论）
        article = ProjectItem(
            projectid=project.id,
            name="Test Article Workflow",
            comment="This is a test article for workflow testing",
            itemtype=1,
            userid=user.id,
            createtime=datetime(2024, 1, 1, 10, 0, 0),
            status=1,
            allowpost=1  # 允许匿名评论
        )
        real_sync_session_with_commit.add(article)
        real_sync_session_with_commit.flush()  # 刷新以获取ID
        
        # 临时提交数据，让API调用能找到
        real_sync_session_with_commit.commit()
        
        # 4. 测试创建匿名评论
        comment_data = {
            "content": "这是一条工作流程测试评论",
            "user_id": 0  # 匿名用户
        }
        
        response = test_client.post(
            f"/api/articles/{article.id}/comments",
            json=comment_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "comment_id" in data
        comment_id = data["comment_id"]
        
        # 5. 验证评论已保存到数据库
        comment_result = real_sync_session_with_commit.exec(
            select(Post).where(Post.id == comment_id)
        )
        comment = comment_result.first()
        assert comment is not None
        assert comment.content == "这是一条工作流程测试评论"
        assert comment.userid == 0
        assert comment.projectitemid == article.id
        assert comment.status == 1

    @pytest.mark.integration
    def test_article_comment_workflow_get(self, test_client, real_sync_session_with_commit):
        """测试文章评论获取工作流程"""
        # 1. 创建测试用户
        user = User(
            name="testuser_workflow_2",
            email="user_workflow2@example.com",
            password="hashed_password",
            regtime=datetime(2024, 1, 1, 10, 0, 0)
        )
        real_sync_session_with_commit.add(user)
        real_sync_session_with_commit.flush()  # 刷新以获取ID
        # 临时提交数据，让API调用能找到
        real_sync_session_with_commit.commit()
        
        # 2. 创建测试项目
        project = Project(
            name="Test Project Workflow 2",
            userid=user.id,
            createtime=datetime(2024, 1, 1, 10, 0, 0),
            state=0,
            accesscount=0
        )
        real_sync_session_with_commit.add(project)
        real_sync_session_with_commit.flush()  # 刷新以获取ID
        # 临时提交数据，让API调用能找到
        real_sync_session_with_commit.commit()
        
        # 3. 创建测试文章（允许匿名评论）
        article = ProjectItem(
            projectid=project.id,
            name="Test Article Workflow 2",
            comment="This is a test article for workflow testing 2",
            itemtype=1,
            userid=user.id,
            createtime=datetime(2024, 1, 1, 10, 0, 0),
            status=1,
            allowpost=1  # 允许匿名评论
        )
        real_sync_session_with_commit.add(article)
        real_sync_session_with_commit.flush()  # 刷新以获取ID
        
        # 临时提交数据，让API调用能找到
        real_sync_session_with_commit.commit()
        
        # 4. 创建测试评论
        comment = Post(
            folderid=0,
            projectitemid=article.id,
            userid=0,  # 匿名用户
            subject="",
            content="这是一条工作流程测试评论",
            size=len("这是一条工作流程测试评论".encode('utf-8')),
            hits=0,
            userip="127.0.0.1",
            posttime=datetime(2024, 1, 1, 11, 0, 0),
            status=1,
            rootid=0,
            replycount=0
        )
        real_sync_session_with_commit.add(comment)
        real_sync_session_with_commit.flush()  # 刷新以获取ID
        # 临时提交数据，让API调用能找到
        real_sync_session_with_commit.commit()
        
        # 5. 测试获取评论列表
        response = test_client.get(f"/api/articles/{article.id}/comments")
        assert response.status_code == 200
        comments_data = response.json()
        assert isinstance(comments_data, list)
        assert len(comments_data) == 1
        
        comment_data = comments_data[0]
        assert comment_data["content"] == "这是一条工作流程测试评论"
        assert comment_data["user_id"] == 0

    @pytest.mark.integration
    def test_guestbook_workflow_create(self, test_client, real_sync_session_with_commit):
        """测试留言本创建工作流程"""
        # 1. 创建测试用户
        user = User(
            name="testuser_guestbook",
            email="user_guestbook@example.com",
            password="hashed_password",
            regtime=datetime(2024, 1, 1, 10, 0, 0)
        )
        real_sync_session_with_commit.add(user)
        real_sync_session_with_commit.flush()  # 刷新以获取ID
        # 临时提交数据，让API调用能找到
        real_sync_session_with_commit.commit()
        
        # 2. 测试创建匿名留言
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
        message_id = data["message_id"]
        
        # 3. 验证留言已保存到数据库
        message_result = real_sync_session_with_commit.exec(
            select(Post).where(Post.id == message_id)
        )
        message = message_result.first()
        assert message is not None
        assert message.subject == "测试留言标题"
        assert message.content == "这是一条测试留言内容"
        assert message.userid == 0
        assert message.projectitemid == 0  # 留言本的projectitemid为0
        assert message.rootid == 0  # 主贴的rootid为0

    @pytest.mark.integration
    def test_guestbook_workflow_reply(self, test_client, real_sync_session_with_commit):
        """测试留言本回复工作流程"""
        # 1. 创建测试用户
        user = User(
            name="testuser_guestbook_2",
            email="user_guestbook2@example.com",
            password="hashed_password",
            regtime=datetime(2024, 1, 1, 10, 0, 0)
        )
        real_sync_session_with_commit.add(user)
        real_sync_session_with_commit.flush()  # 刷新以获取ID
        # 临时提交数据，让API调用能找到
        real_sync_session_with_commit.commit()
        
        # 2. 创建测试留言
        message = Post(
            folderid=0,
            projectitemid=0,  # 留言本的projectitemid为0
            userid=0,  # 匿名用户
            subject="测试留言标题",
            content="这是一条测试留言内容",
            size=len("这是一条测试留言内容".encode('utf-8')),
            hits=0,
            userip="127.0.0.1",
            posttime=datetime(2024, 1, 1, 11, 0, 0),
            status=1,
            rootid=0,  # 主贴的rootid为0
            replycount=0
        )
        real_sync_session_with_commit.add(message)
        real_sync_session_with_commit.flush()  # 刷新以获取ID
        # 临时提交数据，让API调用能找到
        real_sync_session_with_commit.commit()
        
        # 3. 测试创建跟贴
        reply_data = {
            "subject": "",  # 跟贴可以没有标题
            "content": "这是跟贴内容",
            "thread_id": message.id,
            "user_id": 0
        }
        
        response = test_client.post(
            "/api/messages",
            json=reply_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        reply_id = data["message_id"]
        
        # 4. 验证跟贴已保存到数据库
        reply_result = real_sync_session_with_commit.exec(
            select(Post).where(Post.id == reply_id)
        )
        reply = reply_result.first()
        assert reply is not None
        assert reply.content == "这是跟贴内容"
        assert reply.rootid == message.id  # 跟贴的rootid为主贴ID
        assert reply.projectitemid == 0  # 留言本

    @pytest.mark.integration
    def test_guestbook_workflow_get(self, test_client, real_sync_session_with_commit):
        """测试留言本获取工作流程"""
        # 1. 创建测试用户
        user = User(
            name="testuser_guestbook_3",
            email="user_guestbook3@example.com",
            password="hashed_password",
            regtime=datetime(2024, 1, 1, 10, 0, 0)
        )
        real_sync_session_with_commit.add(user)
        real_sync_session_with_commit.flush()  # 刷新以获取ID
        # 临时提交数据，让API调用能找到
        real_sync_session_with_commit.commit()
        
        # 2. 创建测试留言
        message = Post(
            folderid=0,
            projectitemid=0,  # 留言本的projectitemid为0
            userid=0,  # 匿名用户
            subject="测试留言标题",
            content="这是一条测试留言内容",
            size=len("这是一条测试留言内容".encode('utf-8')),
            hits=0,
            userip="127.0.0.1",
            posttime=datetime(2024, 1, 1, 11, 0, 0),
            status=1,
            rootid=0,  # 主贴的rootid为0
            replycount=0
        )
        real_sync_session_with_commit.add(message)
        real_sync_session_with_commit.flush()  # 刷新以获取ID
        # 临时提交数据，让API调用能找到
        real_sync_session_with_commit.commit()
        
        # 3. 测试获取主题留言
        response = test_client.get(f"/api/thread/{message.id}")
        assert response.status_code == 200
        thread_data = response.json()
        assert isinstance(thread_data, dict)
        assert "messages" in thread_data
        
        messages = thread_data["messages"]
        assert isinstance(messages, list)
        assert len(messages) == 1  # 只有主贴
        
        # 验证主贴
        main_post = next((msg for msg in messages if msg["is_main_post"]), None)
        assert main_post is not None
        assert main_post["subject"] == "测试留言标题"
        assert main_post["content"] == "这是一条测试留言内容"

    @pytest.mark.integration
    def test_comment_permissions_anonymous_allowed(self, test_client, real_sync_session_with_commit):
        """测试评论权限验证 - 允许匿名评论"""
        # 创建测试用户
        user = User(
            name="testuser_permissions",
            email="user_permissions@example.com",
            password="hashed_password",
            regtime=datetime(2024, 1, 1, 10, 0, 0)
        )
        real_sync_session_with_commit.add(user)
        real_sync_session_with_commit.flush()  # 刷新以获取ID
        # 临时提交数据，让API调用能找到
        real_sync_session_with_commit.commit()
        
        # 创建测试项目
        project = Project(
            name="Test Project Permissions",
            userid=user.id,
            createtime=datetime(2024, 1, 1, 10, 0, 0),
            state=0,
            accesscount=0
        )
        real_sync_session_with_commit.add(project)
        real_sync_session_with_commit.flush()  # 刷新以获取ID
        # 临时提交数据，让API调用能找到
        real_sync_session_with_commit.commit()
        
        # 测试1: 允许匿名评论的文章
        article1 = ProjectItem(
            projectid=project.id,
            name="Article Allow Anonymous",
            comment="This article allows anonymous comments",
            itemtype=1,
            userid=user.id,
            createtime=datetime(2024, 1, 1, 10, 0, 0),
            status=1,
            allowpost=1  # 允许匿名评论
        )
        real_sync_session_with_commit.add(article1)
        real_sync_session_with_commit.flush()  # 刷新以获取ID
        # 临时提交数据，让API调用能找到
        real_sync_session_with_commit.commit()
        
        comment_data = {
            "content": "匿名评论测试",
            "user_id": 0
        }
        
        response = test_client.post(
            f"/api/articles/{article1.id}/comments",
            json=comment_data
        )
        assert response.status_code == 200

    @pytest.mark.integration
    def test_comment_permissions_login_required(self, test_client, real_sync_session_with_commit):
        """测试评论权限验证 - 需要登录"""
        # 创建测试用户
        user = User(
            name="testuser_permissions_2",
            email="user_permissions2@example.com",
            password="hashed_password",
            regtime=datetime(2024, 1, 1, 10, 0, 0)
        )
        real_sync_session_with_commit.add(user)
        real_sync_session_with_commit.flush()  # 刷新以获取ID
        # 临时提交数据，让API调用能找到
        real_sync_session_with_commit.commit()
        
        # 创建测试项目
        project = Project(
            name="Test Project Permissions 2",
            userid=user.id,
            createtime=datetime(2024, 1, 1, 10, 0, 0),
            state=0,
            accesscount=0
        )
        real_sync_session_with_commit.add(project)
        real_sync_session_with_commit.flush()  # 刷新以获取ID
        # 临时提交数据，让API调用能找到
        real_sync_session_with_commit.commit()
        
        # 测试2: 只允许登录用户评论的文章
        article2 = ProjectItem(
            projectid=project.id,
            name="Article Require Login",
            comment="This article requires login to comment",
            itemtype=1,
            userid=user.id,
            createtime=datetime(2024, 1, 1, 10, 0, 0),
            status=1,
            allowpost=2  # 只允许登录用户评论
        )
        real_sync_session_with_commit.add(article2)
        real_sync_session_with_commit.flush()  # 刷新以获取ID
        # 临时提交数据，让API调用能找到
        real_sync_session_with_commit.commit()
        
        comment_data = {
            "content": "匿名评论测试",
            "user_id": 0
        }
        
        response = test_client.post(
            f"/api/articles/{article2.id}/comments",
            json=comment_data
        )
        assert response.status_code == 401  # 需要登录

    @pytest.mark.integration
    def test_comment_permissions_disabled(self, test_client, real_sync_session_with_commit):
        """测试评论权限验证 - 评论被禁用"""
        # 创建测试用户
        user = User(
            name="testuser_permissions_3",
            email="user_permissions3@example.com",
            password="hashed_password",
            regtime=datetime(2024, 1, 1, 10, 0, 0)
        )
        real_sync_session_with_commit.add(user)
        real_sync_session_with_commit.flush()  # 刷新以获取ID
        # 临时提交数据，让API调用能找到
        real_sync_session_with_commit.commit()
        
        # 创建测试项目
        project = Project(
            name="Test Project Permissions 3",
            userid=user.id,
            createtime=datetime(2024, 1, 1, 10, 0, 0),
            state=0,
            accesscount=0
        )
        real_sync_session_with_commit.add(project)
        real_sync_session_with_commit.flush()  # 刷新以获取ID
        # 临时提交数据，让API调用能找到
        real_sync_session_with_commit.commit()
        
        # 测试3: 禁用评论的文章
        article3 = ProjectItem(
            projectid=project.id,
            name="Article Disabled Comments",
            comment="This article has disabled comments",
            itemtype=1,
            userid=user.id,
            createtime=datetime(2024, 1, 1, 10, 0, 0),
            status=1,
            allowpost=3  # 禁用评论
        )
        real_sync_session_with_commit.add(article3)
        real_sync_session_with_commit.flush()  # 刷新以获取ID
        # 临时提交数据，让API调用能找到
        real_sync_session_with_commit.commit()
        
        comment_data = {
            "content": "匿名评论测试",
            "user_id": 0
        }
        
        response = test_client.post(
            f"/api/articles/{article3.id}/comments",
            json=comment_data
        )
        assert response.status_code == 403  # 评论被禁用

    @pytest.mark.integration
    def test_data_validation(self, test_client, real_sync_session_with_commit):
        """测试数据验证"""
        # 创建测试用户
        user = User(
            name="testuser_validation",
            email="user_validation@example.com",
            password="hashed_password",
            regtime=datetime(2024, 1, 1, 10, 0, 0)
        )
        real_sync_session_with_commit.add(user)
        real_sync_session_with_commit.flush()  # 刷新以获取ID
        # 临时提交数据，让API调用能找到
        real_sync_session_with_commit.commit()
        
        # 创建测试项目
        project = Project(
            name="Test Project Validation",
            userid=user.id,
            createtime=datetime(2024, 1, 1, 10, 0, 0),
            state=0,
            accesscount=0
        )
        real_sync_session_with_commit.add(project)
        real_sync_session_with_commit.flush()  # 刷新以获取ID
        # 临时提交数据，让API调用能找到
        real_sync_session_with_commit.commit()
        
        # 创建测试文章
        article = ProjectItem(
            projectid=project.id,
            name="Test Article Validation",
            comment="This is a test article for validation testing",
            itemtype=1,
            userid=user.id,
            createtime=datetime(2024, 1, 1, 10, 0, 0),
            status=1,
            allowpost=1
        )
        real_sync_session_with_commit.add(article)
        real_sync_session_with_commit.flush()  # 刷新以获取ID
        
        # 临时提交数据，让API调用能找到
        real_sync_session_with_commit.commit()
        
        # 测试1: 空内容评论
        comment_data = {
            "content": "",
            "user_id": 0
        }
        
        response = test_client.post(
            f"/api/articles/{article.id}/comments",
            json=comment_data
        )
        assert response.status_code == 400
        data = response.json()
        assert "评论内容不能为空" in data["detail"]
        
        # 测试2: 空内容留言
        message_data = {
            "subject": "测试标题",
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
        
        # 测试3: 空标题留言
        message_data = {
            "subject": "",
            "content": "测试内容",
            "user_id": 0
        }
        
        response = test_client.post(
            "/api/messages",
            json=message_data
        )
        assert response.status_code == 400
        data = response.json()
        assert "留言标题不能为空" in data["detail"]
        
        # 测试4: 超长标题留言
        long_subject = "a" * 201  # 超过200字符限制
        message_data = {
            "subject": long_subject,
            "content": "测试内容",
            "user_id": 0
        }
        
        response = test_client.post(
            "/api/messages",
            json=message_data
        )
        assert response.status_code == 400
        data = response.json()
        assert "标题不能超过200个字符" in data["detail"]
        
        # 清理测试数据

    @pytest.mark.integration
    def test_nonexistent_article_comment_create(self, test_client):
        """测试不存在的文章评论创建"""
        comment_data = {
            "content": "对不存在文章的评论",
            "user_id": 0
        }
        
        response = test_client.post(
            "/api/articles/99999/comments",
            json=comment_data
        )
        assert response.status_code == 404
        data = response.json()
        assert "文章不存在" in data["detail"]

    @pytest.mark.integration
    def test_nonexistent_article_comment_get(self, test_client):
        """测试获取不存在文章的评论"""
        response = test_client.get("/api/articles/99999/comments")
        assert response.status_code == 404
        data = response.json()
        assert "文章不存在" in data["detail"]

    @pytest.mark.integration
    def test_nonexistent_thread_get(self, test_client):
        """测试获取不存在主题的留言"""
        response = test_client.get("/api/thread/99999")
        assert response.status_code == 404
        data = response.json()
        assert "主题" in data["detail"] and "不存在" in data["detail"]
