"""
文章评论功能简单测试 - 真实数据库版本
使用真实PostgreSQL数据库，测试文章评论的基本功能
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select
from src.models.user import User
from src.models.project import Project
from src.models.project_item import ProjectItem
from src.models.post import Post
from datetime import datetime


class TestArticleCommentsSimple:
    """文章评论功能简单测试类 - 真实数据库版本"""

    @pytest.mark.integration
    def test_create_article_comment_basic(self, test_client, real_sync_session_with_commit):
        """测试创建文章评论的基本功能"""
        # 创建测试用户
        user = User(
            name="testuser_simple_1",
            email="user_simple_1@example.com",
            password="hashed_password",
            regtime=datetime(2024, 1, 1, 10, 0, 0)
        )
        real_sync_session_with_commit.add(user)
        real_sync_session_with_commit.flush()  # 刷新以获取ID
        
        # 创建测试项目
        project = Project(
            name="Test Project Simple",
            userid=user.id,
            createtime=datetime(2024, 1, 1, 10, 0, 0),
            state=0,
            accesscount=0
        )
        real_sync_session_with_commit.add(project)
        real_sync_session_with_commit.flush()  # 刷新以获取ID
        
        # 创建测试文章
        article = ProjectItem(
            projectid=project.id,
            name="Test Article Simple",
            comment="This is a test article for simple comment testing",
            itemtype=1,
            userid=user.id,
            createtime=datetime(2024, 1, 1, 10, 0, 0),
            status=1,
            allowpost=1  # 允许匿名评论
        )
        real_sync_session_with_commit.add(article)
        real_sync_session_with_commit.flush()  # 刷新以获取ID
        
        print(f"Created article with ID: {article.id}")
        
        # 测试创建匿名评论
        comment_data = {
            "content": "这是一条简单测试评论",
            "user_id": 0  # 匿名用户
        }
        
        response = test_client.post(
            f"/api/articles/{article.id}/comments",
            json=comment_data
        )
        
        # 检查响应
        print(f"Response status: {response.status_code}")
        print(f"Response content: {response.text}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "comment_id" in data
        assert data["message"] == "评论创建成功"
        
        # 验证评论已保存到数据库
        comment_result = real_sync_session_with_commit.exec(
            select(Post).where(Post.id == data["comment_id"])
        )
        comment = comment_result.first()
        assert comment is not None
        assert comment.content == "这是一条简单测试评论"
        assert comment.userid == 0
        assert comment.projectitemid == article.id
        assert comment.status == 1
        
        # 数据将在测试结束时自动回滚，无需手动删除

    @pytest.mark.integration
    def test_get_article_comments_basic(self, test_client, real_sync_session_with_commit):
        """测试获取文章评论列表的基本功能"""
        # 创建测试用户
        user = User(
            name="testuser_simple_2",
            email="user_simple_2@example.com",
            password="hashed_password",
            regtime=datetime(2024, 1, 1, 10, 0, 0)
        )
        real_sync_session_with_commit.add(user)
        real_sync_session_with_commit.flush()  # 刷新以获取ID
        
        # 创建测试项目
        project = Project(
            name="Test Project for Get Comments",
            userid=user.id,
            createtime=datetime(2024, 1, 1, 10, 0, 0),
            state=0,
            accesscount=0
        )
        real_sync_session_with_commit.add(project)
        real_sync_session_with_commit.flush()  # 刷新以获取ID
        
        # 创建测试文章
        article = ProjectItem(
            projectid=project.id,
            name="Test Article for Get Comments",
            comment="This is a test article for getting comments",
            itemtype=1,
            userid=user.id,
            createtime=datetime(2024, 1, 1, 10, 0, 0),
            status=1,
            allowpost=1
        )
        real_sync_session_with_commit.add(article)
        real_sync_session_with_commit.flush()  # 刷新以获取ID
        
        # 创建测试评论
        comment = Post(
            folderid=0,
            projectitemid=article.id,
            userid=user.id,
            subject="",
            content="测试评论内容",
            size=len("测试评论内容".encode('utf-8')),
            hits=0,
            userip="127.0.0.1",
            posttime=datetime(2024, 1, 1, 11, 0, 0),
            status=1,
            rootid=0,
            replycount=0
        )
        real_sync_session_with_commit.add(comment)
        real_sync_session_with_commit.flush()  # 刷新以获取ID
        
        # 获取评论列表
        response = test_client.get(f"/api/articles/{article.id}/comments")
        
        print(f"Response status: {response.status_code}")
        print(f"Response content: {response.text}")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        
        # 验证评论数据
        comment_data = data[0]
        assert comment_data["content"] == "测试评论内容"
        assert comment_data["user_id"] == user.id
        assert "post_time" in comment_data
        assert "reply_count" in comment_data
        
        # 数据将在测试结束时自动回滚，无需手动删除

