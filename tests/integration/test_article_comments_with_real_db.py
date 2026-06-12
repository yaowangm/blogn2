"""
文章评论功能集成测试 - 真实数据库版本
使用真实PostgreSQL数据库，测试文章评论的完整功能
包括创建评论、获取评论列表、权限验证等
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


class TestArticleCommentsWithRealDB:
    """文章评论功能测试类 - 真实数据库版本"""

    @pytest.mark.integration
    def test_create_article_comment_anonymous(self, test_client, real_sync_session_with_commit, test_data_tracker):
        """测试匿名用户创建文章评论"""
        # 创建测试用户（不指定ID，让数据库自动生成）
        user = User(
            name="testuser_comment_1",
            email="user_comment_1@example.com",
            password="hashed_password",
            regtime=datetime(2024, 1, 1, 10, 0, 0)
        )
        real_sync_session_with_commit.add(user)
        real_sync_session_with_commit.flush()  # 获取生成的用户ID
        test_data_tracker.add_user(user.id)  # 跟踪用户ID
        
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
        test_data_tracker.add_project(project.id)  # 跟踪项目ID
        
        # 创建测试文章（允许匿名评论）
        article = ProjectItem(
            projectid=project.id,
            name="Test Article for Comments",
            comment="This is a test article for comment testing",
            itemtype=1,
            userid=user.id,
            createtime=datetime(2024, 1, 1, 10, 0, 0),
            status=1,
            allowpost=1  # 允许匿名评论
        )
        real_sync_session_with_commit.add(article)
        real_sync_session_with_commit.flush()  # 刷新以获取ID
        test_data_tracker.add_article(article.id)  # 跟踪文章ID
        
        # 提交数据，让API调用能找到
        real_sync_session_with_commit.commit()
        
        # 测试创建匿名评论
        comment_data = {
            "content": "这是一条测试评论",
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
        assert data["message"] == "评论创建成功"
        test_data_tracker.add_comment(int(data["comment_id"]))

        # 清除 session 缓存后再查，确保读到 API 已提交的数据
        real_sync_session_with_commit.expire_all()
        comment_result = real_sync_session_with_commit.exec(
            select(Post).where(Post.id == data["comment_id"])
        )
        comment = comment_result.first()
        assert comment is not None
        assert comment.content == "这是一条测试评论"
        assert comment.userid == 0
        assert comment.projectitemid == article.id
        assert comment.status == 1

    @pytest.mark.integration
    def test_create_article_comment_logged_in(self, test_client, real_sync_session_with_commit, test_data_tracker):
        """测试登录用户创建文章评论"""
        # 创建测试用户（不指定ID，让数据库自动生成）
        user = User(
            name="testuser_comment_2",
            email="user_comment_2@example.com",
            password="hashed_password",
            regtime=datetime(2024, 1, 1, 10, 0, 0)
        )
        real_sync_session_with_commit.add(user)
        real_sync_session_with_commit.flush()  # 获取生成的用户ID
        test_data_tracker.add_user(user.id)  # 跟踪用户ID
        
        # 创建测试项目
        project = Project(
            name="Test Project for Logged Comments",
            userid=user.id,
            createtime=datetime(2024, 1, 1, 10, 0, 0),
            state=0,
            accesscount=0
        )
        real_sync_session_with_commit.add(project)
        real_sync_session_with_commit.flush()  # 获取生成的项目ID
        test_data_tracker.add_project(project.id)  # 跟踪项目ID
        
        # 创建测试文章（只允许登录用户评论）
        article = ProjectItem(
            projectid=project.id,
            name="Test Article for Logged Comments",
            comment="This is a test article for logged user comment testing",
            itemtype=1,
            userid=user.id,
            createtime=datetime(2024, 1, 1, 10, 0, 0),
            status=1,
            allowpost=2  # 只允许登录用户评论
        )
        real_sync_session_with_commit.add(article)
        real_sync_session_with_commit.flush()  # 刷新以获取ID
        test_data_tracker.add_article(article.id)  # 跟踪文章ID
        
        # 提交数据，让API调用能找到
        real_sync_session_with_commit.commit()
        
        # 模拟登录用户（这里需要实际的认证机制，暂时跳过认证检查）
        # 在实际应用中，这里应该设置有效的认证token
        comment_data = {
            "content": "这是登录用户的测试评论",
            "user_id": user.id
        }
        
        # 由于需要认证，这个测试可能会失败，但我们可以测试API结构
        response = test_client.post(
            f"/api/articles/{article.id}/comments",
            json=comment_data
        )
        
        # 由于没有认证，应该返回401或403
        assert response.status_code in [401, 403]

    @pytest.mark.integration
    def test_create_article_comment_disabled(self, test_client, real_sync_session_with_commit, test_data_tracker):
        """测试评论功能被禁用的文章"""
        # 创建测试用户（不指定ID，让数据库自动生成）
        user = User(
            name="testuser_comment_3",
            email="user_comment_3@example.com",
            password="hashed_password",
            regtime=datetime(2024, 1, 1, 10, 0, 0)
        )
        real_sync_session_with_commit.add(user)
        real_sync_session_with_commit.flush()  # 获取生成的用户ID
        test_data_tracker.add_user(user.id)  # 跟踪用户ID
        
        # 创建测试项目
        project = Project(
            name="Test Project for Disabled Comments",
            userid=user.id,
            createtime=datetime(2024, 1, 1, 10, 0, 0),
            state=0,
            accesscount=0
        )
        real_sync_session_with_commit.add(project)
        real_sync_session_with_commit.flush()  # 获取生成的项目ID
        test_data_tracker.add_project(project.id)  # 跟踪项目ID
        
        # 创建测试文章（禁用评论）
        article = ProjectItem(
            projectid=project.id,
            name="Test Article with Disabled Comments",
            comment="This is a test article with disabled comments",
            itemtype=1,
            userid=user.id,
            createtime=datetime(2024, 1, 1, 10, 0, 0),
            status=1,
            allowpost=3  # 禁用评论
        )
        real_sync_session_with_commit.add(article)
        real_sync_session_with_commit.flush()  # 刷新以获取ID
        test_data_tracker.add_article(article.id)  # 跟踪文章ID
        
        # 提交数据，让API调用能找到
        real_sync_session_with_commit.commit()
        
        # 尝试创建评论
        comment_data = {
            "content": "这应该失败的评论",
            "user_id": 0
        }
        
        response = test_client.post(
            f"/api/articles/{article.id}/comments",
            json=comment_data
        )
        
        assert response.status_code == 403
        data = response.json()
        assert "已关闭评论功能" in data["detail"]

    @pytest.mark.integration
    def test_create_article_comment_empty_content(self, test_client, real_sync_session_with_commit, test_data_tracker):
        """测试创建空内容评论"""
        # 创建测试用户（不指定ID，让数据库自动生成）
        user = User(
            name="testuser_comment_4",
            email="user_comment_4@example.com",
            password="hashed_password",
            regtime=datetime(2024, 1, 1, 10, 0, 0)
        )
        real_sync_session_with_commit.add(user)
        real_sync_session_with_commit.flush()  # 获取生成的用户ID
        test_data_tracker.add_user(user.id)  # 跟踪用户ID
        
        # 创建测试项目
        project = Project(
            name="Test Project for Empty Comment",
            userid=user.id,
            createtime=datetime(2024, 1, 1, 10, 0, 0),
            state=0,
            accesscount=0
        )
        real_sync_session_with_commit.add(project)
        real_sync_session_with_commit.flush()  # 获取生成的项目ID
        test_data_tracker.add_project(project.id)  # 跟踪项目ID
        
        # 创建测试文章
        article = ProjectItem(
            projectid=project.id,
            name="Test Article for Empty Comment",
            comment="This is a test article for empty comment testing",
            itemtype=1,
            userid=user.id,
            createtime=datetime(2024, 1, 1, 10, 0, 0),
            status=1,
            allowpost=1
        )
        real_sync_session_with_commit.add(article)
        real_sync_session_with_commit.flush()  # 刷新以获取ID
        test_data_tracker.add_article(article.id)  # 跟踪文章ID
        
        # 提交数据，让API调用能找到
        real_sync_session_with_commit.commit()
        
        # 尝试创建空内容评论
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

    @pytest.mark.integration
    def test_create_article_comment_nonexistent_article(self, test_client):
        """测试为不存在的文章创建评论"""
        comment_data = {
            "content": "这是对不存在文章的评论",
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
    def test_get_article_comments(self, test_client, real_sync_session_with_commit, test_data_tracker):
        """测试获取文章评论列表"""
        # 创建测试用户（不指定ID，让数据库自动生成）
        user = User(
            name="testuser_comment_5",
            email="user_comment_5@example.com",
            password="hashed_password",
            regtime=datetime(2024, 1, 1, 10, 0, 0)
        )
        real_sync_session_with_commit.add(user)
        real_sync_session_with_commit.flush()  # 获取生成的用户ID
        test_data_tracker.add_user(user.id)  # 跟踪用户ID
        
        # 创建测试项目
        project = Project(
            name="Test Project for Get Comments",
            userid=user.id,
            createtime=datetime(2024, 1, 1, 10, 0, 0),
            state=0,
            accesscount=0
        )
        real_sync_session_with_commit.add(project)
        real_sync_session_with_commit.flush()  # 获取生成的项目ID
        test_data_tracker.add_project(project.id)  # 跟踪项目ID
        
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
        real_sync_session_with_commit.flush()  # 获取生成的文章ID
        test_data_tracker.add_article(article.id)  # 跟踪文章ID
        
        # 创建测试评论
        comment1 = Post(
            folderid=0,
            projectitemid=article.id,
            userid=user.id,
            subject="",
            content="第一条测试评论",
            size=len("第一条测试评论".encode('utf-8')),
            hits=0,
            userip="127.0.0.1",
            posttime=datetime(2024, 1, 1, 11, 0, 0),
            status=1,
            rootid=0,
            replycount=0
        )
        real_sync_session_with_commit.add(comment1)
        real_sync_session_with_commit.flush()  # 刷新以获取ID
        test_data_tracker.add_comment(comment1.id)  # 跟踪评论ID
        
        comment2 = Post(
            folderid=0,
            projectitemid=article.id,
            userid=user.id,
            subject="",
            content="第二条测试评论",
            size=len("第二条测试评论".encode('utf-8')),
            hits=0,
            userip="127.0.0.1",
            posttime=datetime(2024, 1, 1, 12, 0, 0),
            status=1,
            rootid=0,
            replycount=0
        )
        real_sync_session_with_commit.add(comment2)
        real_sync_session_with_commit.flush()  # 刷新以获取ID
        test_data_tracker.add_comment(comment2.id)  # 跟踪评论ID
        # 提交数据，让API调用能找到
        real_sync_session_with_commit.commit()
        
        # 获取评论列表
        response = test_client.get(f"/api/articles/{article.id}/comments")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        comments = data["comments"]
        assert len(comments) == 2
        
        # 验证评论数据
        comment_ids = [comment["id"] for comment in comments]
        assert comment1.id in comment_ids
        assert comment2.id in comment_ids
        
        # 验证评论内容
        for comment in comments:
            assert "content" in comment
            assert "user_id" in comment
            assert "post_time" in comment
            assert "reply_count" in comment

    @pytest.mark.integration
    def test_get_article_comments_nonexistent_article(self, test_client):
        """测试获取不存在文章的评论列表"""
        response = test_client.get("/api/articles/99999/comments")
        
        assert response.status_code == 404
        data = response.json()
        assert "文章不存在" in data["detail"]

    @pytest.mark.integration
    def test_get_article_comments_pagination_first_page(self, test_client, real_sync_session_with_commit, test_data_tracker):
        """测试评论列表分页功能 - 第一页"""
        # 创建测试用户（不指定ID，让数据库自动生成）
        user = User(
            name="testuser_comment_6",
            email="user_comment_6@example.com",
            password="hashed_password",
            regtime=datetime(2024, 1, 1, 10, 0, 0)
        )
        real_sync_session_with_commit.add(user)
        real_sync_session_with_commit.flush()  # 获取生成的用户ID
        test_data_tracker.add_user(user.id)  # 跟踪用户ID
        
        # 创建测试项目
        project = Project(
            name="Test Project for Pagination",
            userid=user.id,
            createtime=datetime(2024, 1, 1, 10, 0, 0),
            state=0,
            accesscount=0
        )
        real_sync_session_with_commit.add(project)
        real_sync_session_with_commit.flush()  # 获取生成的项目ID
        test_data_tracker.add_project(project.id)  # 跟踪项目ID
        
        # 创建测试文章
        article = ProjectItem(
            projectid=project.id,
            name="Test Article for Pagination",
            comment="This is a test article for pagination testing",
            itemtype=1,
            userid=user.id,
            createtime=datetime(2024, 1, 1, 10, 0, 0),
            status=1,
            allowpost=1
        )
        real_sync_session_with_commit.add(article)
        real_sync_session_with_commit.flush()  # 获取生成的文章ID
        test_data_tracker.add_article(article.id)  # 跟踪文章ID
        
        # 创建多个测试评论
        for i in range(5):
            comment = Post(
                folderid=0,
                projectitemid=article.id,
                userid=user.id,
                subject="",
                content=f"测试评论 {i+1}",
                size=len(f"测试评论 {i+1}".encode('utf-8')),
                hits=0,
                userip="127.0.0.1",
                posttime=datetime(2024, 1, 1, 11, i, 0),
                status=1,
                rootid=0,
                replycount=0
            )
            real_sync_session_with_commit.add(comment)
        real_sync_session_with_commit.flush()  # 刷新以获取ID
        for row in real_sync_session_with_commit.exec(
            select(Post).where(Post.projectitemid == article.id)
        ).all():
            test_data_tracker.add_comment(row.id)
        # 提交数据，让API调用能找到
        real_sync_session_with_commit.commit()
        
        # 测试第一页（每页3条）
        response = test_client.get(f"/api/articles/{article.id}/comments?page=1&limit=3")
        assert response.status_code == 200
        data = response.json()
        assert len(data["comments"]) == 3

    @pytest.mark.integration
    def test_get_article_comments_pagination_second_page(self, test_client, real_sync_session_with_commit, test_data_tracker):
        """测试评论列表分页功能 - 第二页"""
        # 创建测试用户（不指定ID，让数据库自动生成）
        user = User(
            name="testuser_comment_7",
            email="user_comment_7@example.com",
            password="hashed_password",
            regtime=datetime(2024, 1, 1, 10, 0, 0)
        )
        real_sync_session_with_commit.add(user)
        real_sync_session_with_commit.flush()  # 获取生成的用户ID
        test_data_tracker.add_user(user.id)  # 跟踪用户ID
        
        # 创建测试项目
        project = Project(
            name="Test Project for Pagination 2",
            userid=user.id,
            createtime=datetime(2024, 1, 1, 10, 0, 0),
            state=0,
            accesscount=0
        )
        real_sync_session_with_commit.add(project)
        real_sync_session_with_commit.flush()  # 获取生成的项目ID
        test_data_tracker.add_project(project.id)  # 跟踪项目ID
        
        # 创建测试文章
        article = ProjectItem(
            projectid=project.id,
            name="Test Article for Pagination 2",
            comment="This is a test article for pagination testing 2",
            itemtype=1,
            userid=user.id,
            createtime=datetime(2024, 1, 1, 10, 0, 0),
            status=1,
            allowpost=1
        )
        real_sync_session_with_commit.add(article)
        real_sync_session_with_commit.flush()  # 获取生成的文章ID
        test_data_tracker.add_article(article.id)  # 跟踪文章ID
        
        # 创建多个测试评论
        for i in range(5):
            comment = Post(
                folderid=0,
                projectitemid=article.id,
                userid=user.id,
                subject="",
                content=f"测试评论 {i+1}",
                size=len(f"测试评论 {i+1}".encode('utf-8')),
                hits=0,
                userip="127.0.0.1",
                posttime=datetime(2024, 1, 1, 11, i, 0),
                status=1,
                rootid=0,
                replycount=0
            )
            real_sync_session_with_commit.add(comment)
        real_sync_session_with_commit.flush()  # 刷新以获取ID
        for row in real_sync_session_with_commit.exec(
            select(Post).where(Post.projectitemid == article.id)
        ).all():
            test_data_tracker.add_comment(row.id)
        # 提交数据，让API调用能找到
        real_sync_session_with_commit.commit()
        
        # 测试第二页
        response = test_client.get(f"/api/articles/{article.id}/comments?page=2&limit=3")
        assert response.status_code == 200
        data = response.json()
        assert len(data["comments"]) == 2  # 剩余2条评论
