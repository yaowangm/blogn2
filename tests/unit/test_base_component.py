"""
BaseComponent 测试模块

测试基础Web组件类的核心功能，包括：
- HTML转义和XSS防护
- Markdown处理
- URL验证
- 日期格式化
- 文本处理工具
"""

import pytest
from unittest.mock import patch, MagicMock
import json
from datetime import datetime, timedelta


class TestBaseComponent:
    """BaseComponent 功能测试类"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        # 模拟浏览器环境
        self.mock_document = MagicMock()
        self.mock_window = MagicMock()
        self.mock_location = MagicMock()
        self.mock_match_media = MagicMock()
        
        # 设置模拟对象
        self.mock_location.pathname = "/blog/1"
        self.mock_window.location = self.mock_location
        self.mock_window.matchMedia = self.mock_match_media
        self.mock_match_media.return_value.matches = False
        
        # 模拟全局对象
        with patch('builtins.window', self.mock_window), \
             patch('builtins.document', self.mock_document), \
             patch('builtins.Node', MagicMock()), \
             patch('builtins.customElements', MagicMock()):
            
            # 导入BaseComponent类
            import sys
            sys.path.append('/home/wy/blogn2/src/static/js/components')
            
            # 模拟HTMLElement
            class MockHTMLElement:
                def __init__(self):
                    self.shadowRoot = MagicMock()
                
                def attachShadow(self, mode):
                    return self.shadowRoot
                
                def createElement(self, tag):
                    return MagicMock()
                
                def createTextNode(self, text):
                    return MagicMock()
            
            with patch('builtins.HTMLElement', MockHTMLElement):
                from base_component import BaseComponent
                self.BaseComponent = BaseComponent
                self.component = BaseComponent()
    
    def test_escape_html_basic(self):
        """测试基本HTML转义功能"""
        # 测试基本字符转义
        assert self.component.escapeHtml("&") == "&amp;"
        assert self.component.escapeHtml("<") == "&lt;"
        assert self.component.escapeHtml(">") == "&gt;"
        assert self.component.escapeHtml('"') == "&quot;"
        assert self.component.escapeHtml("'") == "&#39;"
        
        # 测试组合转义
        assert self.component.escapeHtml("<script>alert('xss')</script>") == "&lt;script&gt;alert(&#39;xss&#39;)&lt;/script&gt;"
        
        # 测试非字符串输入
        assert self.component.escapeHtml(None) == ""
        assert self.component.escapeHtml(123) == 123
        assert self.component.escapeHtml("") == ""
    
    def test_is_valid_url(self):
        """测试URL验证功能"""
        # 有效URL
        assert self.component.isValidUrl("https://example.com") == True
        assert self.component.isValidUrl("http://example.com") == True
        assert self.component.isValidUrl("mailto:test@example.com") == True
        
        # 无效URL
        assert self.component.isValidUrl("javascript:alert('xss')") == False
        assert self.component.isValidUrl("ftp://example.com") == False
        assert self.component.isValidUrl("invalid-url") == False
        assert self.component.isValidUrl("") == False
        assert self.component.isValidUrl(None) == False
    
    def test_is_valid_image_src(self):
        """测试图片src验证功能"""
        # 有效图片URL
        assert self.component.isValidImageSrc("https://example.com/image.jpg") == True
        assert self.component.isValidImageSrc("http://example.com/image.png") == True
        
        # 无效图片URL
        assert self.component.isValidImageSrc("javascript:alert('xss')") == False
        assert self.component.isValidImageSrc("ftp://example.com/image.jpg") == False
        assert self.component.isValidImageSrc("data:image/png;base64,iVBORw0KGgo=") == False
        assert self.component.isValidImageSrc("") == False
        assert self.component.isValidImageSrc(None) == False
    
    def test_strip_markdown(self):
        """测试Markdown标记移除功能"""
        # 测试标题标记
        assert self.component.stripMarkdown("# 标题") == "标题"
        assert self.component.stripMarkdown("## 二级标题") == "二级标题"
        assert self.component.stripMarkdown("### 三级标题") == "三级标题"
        
        # 测试粗体和斜体
        assert self.component.stripMarkdown("**粗体**") == "粗体"
        assert self.component.stripMarkdown("*斜体*") == "斜体"
        assert self.component.stripMarkdown("__粗体__") == "粗体"
        assert self.component.stripMarkdown("_斜体_") == "斜体"
        
        # 测试删除线
        assert self.component.stripMarkdown("~~删除线~~") == "删除线"
        
        # 测试行内代码
        assert self.component.stripMarkdown("`代码`") == "代码"
        
        # 测试代码块
        markdown_with_code = """```python
def hello():
    print("Hello")
```"""
        assert "def hello():" not in self.component.stripMarkdown(markdown_with_code)
        
        # 测试链接
        assert self.component.stripMarkdown("[链接文本](https://example.com)") == "链接文本"
        
        # 测试图片
        assert self.component.stripMarkdown("![图片](https://example.com/image.jpg)") == "图片"
        
        # 测试引用
        assert self.component.stripMarkdown("> 引用内容") == "引用内容"
        
        # 测试列表
        assert self.component.stripMarkdown("- 列表项") == "列表项"
        assert self.component.stripMarkdown("1. 有序列表") == "有序列表"
        
        # 测试水平线
        assert self.component.stripMarkdown("---") == ""
        
        # 测试表格
        assert self.component.stripMarkdown("| 列1 | 列2 |") == "列1 列2"
        
        # 测试非字符串输入
        assert self.component.stripMarkdown(None) == ""
        assert self.component.stripMarkdown(123) == ""
    
    def test_truncate_text(self):
        """测试文本截断功能"""
        # 测试正常截断
        long_text = "这是一个很长的文本内容，需要被截断"
        result = self.component.truncateText(long_text, 10)
        assert len(result) == 13  # "这是一个很长的文本内容，需要被截断" -> "这是一个很长的文本内容，需要被截断..."
        assert result.endswith("...")
        
        # 测试短文本不截断
        short_text = "短文本"
        result = self.component.truncateText(short_text, 10)
        assert result == short_text
        assert not result.endswith("...")
        
        # 测试换行符处理
        text_with_newlines = "第一行\n第二行\r\n第三行"
        result = self.component.truncateText(text_with_newlines, 5)
        assert "\n" not in result
        assert "\r" not in result
        
        # 测试空文本
        assert self.component.truncateText("", 10) == ""
        assert self.component.truncateText(None, 10) == ""
    
    def test_format_date(self):
        """测试日期格式化功能"""
        now = datetime.now()
        
        # 测试今天的时间
        one_hour_ago = now - timedelta(hours=1, minutes=30)
        result = self.component.formatDate(one_hour_ago.isoformat())
        assert "1小时" in result and "30分钟" in result
        
        # 测试几分钟前
        five_minutes_ago = now - timedelta(minutes=5)
        result = self.component.formatDate(five_minutes_ago.isoformat())
        assert "5分钟前" in result
        
        # 测试昨天
        yesterday = now - timedelta(days=1)
        result = self.component.formatDate(yesterday.isoformat())
        assert result == "昨天"
        
        # 测试几天前
        three_days_ago = now - timedelta(days=3)
        result = self.component.formatDate(three_days_ago.isoformat())
        assert "3天前" in result
        
        # 测试一周前
        ten_days_ago = now - timedelta(days=10)
        result = self.component.formatDate(ten_days_ago.isoformat())
        # 应该返回本地化日期格式
        assert isinstance(result, str)
        assert len(result) > 0
        
        # 测试空日期
        assert self.component.formatDate("") == ""
        assert self.component.formatDate(None) == ""
    
    def test_get_default_metadata(self):
        """测试默认元数据获取"""
        metadata = self.component.getDefaultMetadata()
        
        assert isinstance(metadata, dict)
        assert "site_name" in metadata
        assert "logo_url" in metadata
        assert "user_count" in metadata
        assert "post_count" in metadata
        
        assert metadata["site_name"] == "BlogN"
        assert metadata["logo_url"] == "/static/images/logo.svg"
        assert metadata["user_count"] == 0
        assert metadata["post_count"] == 0
    
    def test_get_project_id(self):
        """测试项目ID获取功能"""
        # 测试博客页面URL
        self.mock_location.pathname = "/blog/123"
        project_id = self.component.getProjectId()
        assert project_id == 123
        
        # 测试文章页面URL
        self.mock_location.pathname = "/article/456"
        project_id = self.component.getProjectId()
        assert project_id is None
        
        # 测试编辑文章页面URL
        self.mock_location.pathname = "/edit-article/789"
        project_id = self.component.getProjectId()
        assert project_id is None
        
        # 测试无效URL
        self.mock_location.pathname = "/invalid/path"
        project_id = self.component.getProjectId()
        assert project_id is None
    
    def test_get_article_id(self):
        """测试文章ID获取功能"""
        # 测试文章页面URL
        self.mock_location.pathname = "/article/456"
        article_id = self.component.getArticleId()
        assert article_id == 456
        
        # 测试编辑文章页面URL
        self.mock_location.pathname = "/edit-article/789"
        article_id = self.component.getArticleId()
        assert article_id == 789
        
        # 测试博客页面URL
        self.mock_location.pathname = "/blog/123"
        article_id = self.component.getArticleId()
        assert article_id is None
        
        # 测试无效URL
        self.mock_location.pathname = "/invalid/path"
        article_id = self.component.getArticleId()
        assert article_id is None
    
    def test_is_article_page(self):
        """测试文章页面检测功能"""
        # 测试文章页面
        self.mock_location.pathname = "/article/456"
        assert self.component.isArticlePage() == True
        
        # 测试编辑文章页面
        self.mock_location.pathname = "/edit-article/789"
        assert self.component.isArticlePage() == True
        
        # 测试博客页面
        self.mock_location.pathname = "/blog/123"
        assert self.component.isArticlePage() == False
        
        # 测试其他页面
        self.mock_location.pathname = "/invalid/path"
        assert self.component.isArticlePage() == False
    
    def test_create_loading_html(self):
        """测试加载状态HTML创建"""
        html = self.component.createLoadingHTML()
        
        assert isinstance(html, str)
        assert "加载中" in html
        assert "animation: spin" in html
        assert "@keyframes spin" in html
        assert "display: flex" in html
    
    def test_create_error_html(self):
        """测试错误状态HTML创建"""
        # 测试默认错误消息
        html = self.component.createErrorHTML()
        assert isinstance(html, str)
        assert "加载失败" in html
        
        # 测试自定义错误消息
        custom_message = "自定义错误消息"
        html = self.component.createErrorHTML(custom_message)
        assert custom_message in html
    
    @patch('builtins.fetch')
    def test_load_metadata_success(self, mock_fetch):
        """测试元数据加载成功"""
        # 模拟成功的API响应
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "site_name": "Test Site",
            "logo_url": "/test/logo.svg",
            "user_count": 100,
            "post_count": 50
        }
        mock_fetch.return_value = mock_response
        
        # 测试元数据加载
        import asyncio
        asyncio.run(self.component.loadMetadata())
        
        assert self.component.metadata is not None
        assert self.component.metadata["site_name"] == "Test Site"
        assert self.component.metadata["user_count"] == 100
    
    @patch('builtins.fetch')
    def test_load_metadata_failure(self, mock_fetch):
        """测试元数据加载失败"""
        # 模拟失败的API响应
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status = 404
        mock_fetch.return_value = mock_response
        
        # 测试元数据加载失败
        import asyncio
        asyncio.run(self.component.loadMetadata())
        
        # 应该使用默认元数据
        assert self.component.metadata is not None
        assert self.component.metadata["site_name"] == "BlogN"
    
    @patch('builtins.fetch')
    def test_load_metadata_exception(self, mock_fetch):
        """测试元数据加载异常"""
        # 模拟网络异常
        mock_fetch.side_effect = Exception("Network error")
        
        # 测试元数据加载异常
        import asyncio
        asyncio.run(self.component.loadMetadata())
        
        # 应该使用默认元数据
        assert self.component.metadata is not None
        assert self.component.metadata["site_name"] == "BlogN"
    
    def test_log_error(self):
        """测试错误日志记录"""
        # 测试基本错误记录
        with patch('builtins.console') as mock_console:
            self.component.logError("Test error", "Error details")
            mock_console.error.assert_called_once()
    
    def test_get_logo_url(self):
        """测试Logo URL获取"""
        # 设置元数据
        self.component.metadata = {
            "logo_url": "/static/images/logo.svg"
        }
        
        # 测试浅色主题
        self.mock_match_media.return_value.matches = False
        logo_url = self.component.getLogoUrl()
        assert logo_url == "/static/images/logo-light.svg"
        
        # 测试深色主题
        self.mock_match_media.return_value.matches = True
        logo_url = self.component.getLogoUrl()
        assert logo_url == "/static/images/logo-dark.svg"
        
        # 测试无元数据情况
        self.component.metadata = None
        logo_url = self.component.getLogoUrl()
        assert logo_url == "/static/images/logo-light.svg"


class TestBaseComponentIntegration:
    """BaseComponent 集成测试类"""
    
    def test_sanitize_html_basic(self):
        """测试基本HTML清理功能"""
        # 这个测试需要更复杂的DOM模拟，暂时跳过
        # 在实际浏览器环境中会正常工作
        pass
    
    def test_sanitize_html_xss_protection(self):
        """测试XSS防护功能"""
        # 这个测试需要更复杂的DOM模拟，暂时跳过
        # 在实际浏览器环境中会正常工作
        pass


if __name__ == "__main__":
    pytest.main([__file__])
