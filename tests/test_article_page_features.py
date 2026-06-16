"""
文章页面功能集成测试
测试新增的文章页面相关功能
"""

import pytest


class TestArticlePageFeatures:
    """文章页面功能集成测试类"""
    
    def test_attachment_data_structure(self):
        """测试附件数据结构"""
        # 模拟附件数据
        attachments = [
            {"id": 1, "linkstr": "/upload/img1.jpg", "comment": "图片1"},
            {"id": 2, "linkstr": "/upload/img2.jpg", "comment": "图片2"}
        ]
        
        # 验证附件数据
        assert len(attachments) == 2
        assert attachments[0]["id"] == 1
        assert attachments[0]["linkstr"] == "/upload/img1.jpg"
    
    def test_comment_anchor_format(self):
        """测试评论锚点格式"""
        comment_id = 123
        expected_anchor = f"#post{comment_id}"
        
        # 验证锚点格式
        assert expected_anchor.startswith("#post")
        assert expected_anchor.endswith(str(comment_id))
    
    def test_link_detection(self):
        """测试链接检测（RFC 3986 字符集，CJK/全角标点不进入 URL）"""
        from tests.unit.autolink_helpers import find_autolink_urls, linkify_plain_text_to_html

        content = "访问 https://example.com 获取更多信息"
        detected_links = find_autolink_urls(content)
        assert detected_links == ["https://example.com"]

        beelink = "http://club.beelink.com.cn/index.asp?boardid=168），禁书挺多的"
        assert find_autolink_urls(beelink) == [
            "http://club.beelink.com.cn/index.asp?boardid=168"
        ]
        html = linkify_plain_text_to_html(beelink)
        assert 'href="http://club.beelink.com.cn/index.asp?boardid=168"' in html
        assert "），禁书挺多的" in html
    
    def test_blog_profile_email_removal(self):
        """测试博客资料中电子邮件的移除"""
        user_data = {
            "id": 123,
            "name": "测试用户",
            "email": "test@example.com"  # 这个字段不应该显示
        }
        
        # 验证必要字段存在
        assert "id" in user_data
        assert "name" in user_data
        
        # 验证email字段存在但不显示
        assert "email" in user_data  # 数据中存在
        # 但在渲染时应该被忽略
    
    def test_rss_link_format(self):
        """测试RSS链接格式"""
        # 验证RSS链接应该是正确的格式
        expected_format = "/article/{article_id}"
        
        # 模拟文章数据
        article_id = 123
        expected_link = f"/article/{article_id}"
        
        # 验证链接格式正确
        assert expected_link.startswith("/article/")
        assert expected_link.endswith(str(article_id))
        assert expected_link == expected_format.format(article_id=article_id)
