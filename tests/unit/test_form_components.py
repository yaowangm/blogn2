"""
表单组件测试模块

测试表单组件的功能，包括：
- 表单样式应用
- 表单验证
- 预览功能
- 图片上传
- 响应式设计
"""

import pytest
from unittest.mock import patch, MagicMock
import json
import os


class TestFormComponentsCSS:
    """表单组件CSS测试类"""
    
    def test_form_components_css_exists(self):
        """测试form-components.css文件存在"""
        css_file = "/home/wy/blogn2/src/static/css/form-components.css"
        assert os.path.exists(css_file), "form-components.css文件不存在"
    
    def test_form_components_css_content(self):
        """测试form-components.css文件内容"""
        css_file = "/home/wy/blogn2/src/static/css/form-components.css"
        
        with open(css_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查关键CSS类是否存在
        assert ".form-group" in content, "缺少.form-group样式"
        assert ".form-label" in content, "缺少.form-label样式"
        assert ".form-input" in content, "缺少.form-input样式"
        assert ".form-textarea" in content, "缺少.form-textarea样式"
        assert ".form-select" in content, "缺少.form-select样式"
        assert ".form-actions" in content, "缺少.form-actions样式"
        assert ".btn" in content, "缺少.btn样式"
        assert ".btn-primary" in content, "缺少.btn-primary样式"
        assert ".btn-secondary" in content, "缺少.btn-secondary样式"
        assert ".error-message" in content, "缺少.error-message样式"
        assert ".success-message" in content, "缺少.success-message样式"
        assert ".loading" in content, "缺少.loading样式"
        assert ".loading-spinner" in content, "缺少.loading-spinner样式"
        assert ".preview-toggle" in content, "缺少.preview-toggle样式"
        assert ".btn-preview" in content, "缺少.btn-preview样式"
        assert ".content-container" in content, "缺少.content-container样式"
        assert ".content-preview" in content, "缺少.content-preview样式"
        assert ".preview-content" in content, "缺少.preview-content样式"
        assert ".image-upload-container" in content, "缺少.image-upload-container样式"
        assert ".uploaded-image-preview" in content, "缺少.uploaded-image-preview样式"
        assert ".main-image-preview" in content, "缺少.main-image-preview样式"
        assert ".multiple-images-preview" in content, "缺少.multiple-images-preview样式"
        assert ".images-list" in content, "缺少.images-list样式"
        assert ".image-item" in content, "缺少.image-item样式"
        assert ".thumb-image" in content, "缺少.thumb-image样式"
        assert ".image-info" in content, "缺少.image-info样式"
        assert ".image-name" in content, "缺少.image-name样式"
        assert ".image-size" in content, "缺少.image-size样式"
        assert ".btn-remove-image" in content, "缺少.btn-remove-image样式"
    
    def test_form_components_css_variables(self):
        """测试CSS变量使用"""
        css_file = "/home/wy/blogn2/src/static/css/form-components.css"
        
        with open(css_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查CSS变量使用
        assert "var(--spacing-" in content, "缺少spacing变量使用"
        assert "var(--gray-" in content, "缺少gray变量使用"
        assert "var(--primary-color)" in content, "缺少primary-color变量使用"
        assert "var(--radius-" in content, "缺少radius变量使用"
        assert "var(--font-size-" in content, "缺少font-size变量使用"
        assert "var(--transition-" in content, "缺少transition变量使用"
        assert "var(--white)" in content, "缺少white变量使用"
        assert "var(--error-color)" in content, "缺少error-color变量使用"
    
    def test_form_components_css_responsive(self):
        """测试响应式设计"""
        css_file = "/home/wy/blogn2/src/static/css/form-components.css"
        
        with open(css_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查响应式相关样式
        assert "grid-template-columns" in content, "缺少网格布局"
        assert "minmax(" in content, "缺少响应式网格"
        assert "auto-fill" in content, "缺少自动填充网格"
        assert "max-width: 100%" in content, "缺少最大宽度限制"
        assert "height: auto" in content, "缺少自动高度"
    
    def test_form_components_css_animations(self):
        """测试动画效果"""
        css_file = "/home/wy/blogn2/src/static/css/form-components.css"
        
        with open(css_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查动画相关样式
        assert "@keyframes spin" in content, "缺少旋转动画"
        assert "animation: spin" in content, "缺少旋转动画应用"
        assert "transition:" in content, "缺少过渡效果"
        assert "transform:" in content, "缺少变换效果"
    
    def test_form_components_css_accessibility(self):
        """测试无障碍设计"""
        css_file = "/home/wy/blogn2/src/static/css/form-components.css"
        
        with open(css_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查无障碍相关样式
        assert "cursor: pointer" in content, "缺少指针光标"
        assert "cursor: not-allowed" in content, "缺少禁用光标"
        assert "focus" in content, "缺少焦点样式"
        assert "hover" in content, "缺少悬停样式"
        assert "disabled" in content, "缺少禁用样式"


class TestFormComponentsIntegration:
    """表单组件集成测试类"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        # 模拟浏览器环境
        self.mock_document = MagicMock()
        self.mock_window = MagicMock()
        
        # 模拟全局对象
        with patch('builtins.window', self.mock_window), \
             patch('builtins.document', self.mock_document), \
             patch('builtins.Node', MagicMock()), \
             patch('builtins.customElements', MagicMock()):
            
            # 导入相关组件
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
    
    def test_form_components_css_loading(self):
        """测试表单组件CSS加载"""
        # 模拟CSS文件加载
        mock_link = MagicMock()
        mock_link.rel = "stylesheet"
        mock_link.href = "/static/css/form-components.css"
        
        self.mock_document.createElement.return_value = mock_link
        self.mock_document.head.appendChild = MagicMock()
        
        # 测试CSS加载逻辑
        # 这里需要在实际的组件中测试CSS加载
        pass
    
    def test_form_validation_styles(self):
        """测试表单验证样式"""
        # 测试错误状态样式
        error_styles = [
            ".error-message",
            ".form-input:invalid",
            ".form-textarea:invalid",
            ".form-select:invalid"
        ]
        
        css_file = "/home/wy/blogn2/src/static/css/form-components.css"
        with open(css_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        for style in error_styles:
            assert style in content, f"缺少{style}样式"
    
    def test_form_success_styles(self):
        """测试表单成功样式"""
        # 测试成功状态样式
        success_styles = [
            ".success-message",
            ".form-input:valid",
            ".form-textarea:valid",
            ".form-select:valid"
        ]
        
        css_file = "/home/wy/blogn2/src/static/css/form-components.css"
        with open(css_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        for style in success_styles:
            assert style in content, f"缺少{style}样式"
    
    def test_form_loading_styles(self):
        """测试表单加载样式"""
        # 测试加载状态样式
        loading_styles = [
            ".loading",
            ".loading-spinner",
            "@keyframes spin"
        ]
        
        css_file = "/home/wy/blogn2/src/static/css/form-components.css"
        with open(css_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        for style in loading_styles:
            assert style in content, f"缺少{style}样式"
    
    def test_form_preview_styles(self):
        """测试表单预览样式"""
        # 测试预览功能样式
        preview_styles = [
            ".preview-toggle",
            ".btn-preview",
            ".content-container",
            ".content-preview",
            ".preview-content"
        ]
        
        css_file = "/home/wy/blogn2/src/static/css/form-components.css"
        with open(css_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        for style in preview_styles:
            assert style in content, f"缺少{style}样式"
    
    def test_form_image_upload_styles(self):
        """测试表单图片上传样式"""
        # 测试图片上传样式
        image_styles = [
            ".image-upload-container",
            ".uploaded-image-preview",
            ".main-image-preview",
            ".multiple-images-preview",
            ".images-list",
            ".image-item",
            ".thumb-image",
            ".image-info",
            ".image-name",
            ".image-size",
            ".btn-remove-image"
        ]
        
        css_file = "/home/wy/blogn2/src/static/css/form-components.css"
        with open(css_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        for style in image_styles:
            assert style in content, f"缺少{style}样式"
    
    def test_form_markdown_preview_styles(self):
        """测试Markdown预览样式"""
        # 测试Markdown预览样式
        markdown_styles = [
            ".preview-content.markdown-content",
            ".preview-content.markdown-content h1",
            ".preview-content.markdown-content h2",
            ".preview-content.markdown-content h3",
            ".preview-content.markdown-content h4",
            ".preview-content.markdown-content h5",
            ".preview-content.markdown-content h6",
            ".preview-content.markdown-content p",
            ".preview-content.markdown-content ul",
            ".preview-content.markdown-content ol",
            ".preview-content.markdown-content li",
            ".preview-content.markdown-content blockquote",
            ".preview-content.markdown-content code",
            ".preview-content.markdown-content pre",
            ".preview-content.markdown-content table",
            ".preview-content.markdown-content th",
            ".preview-content.markdown-content td",
            ".preview-content.markdown-content a",
            ".preview-content.markdown-content img",
            ".preview-content.markdown-content hr"
        ]
        
        css_file = "/home/wy/blogn2/src/static/css/form-components.css"
        with open(css_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        for style in markdown_styles:
            assert style in content, f"缺少{style}样式"
    
    def test_form_button_styles(self):
        """测试按钮样式"""
        # 测试按钮样式
        button_styles = [
            ".btn",
            ".btn-primary",
            ".btn-secondary",
            ".btn:disabled",
            ".btn-preview"
        ]
        
        css_file = "/home/wy/blogn2/src/static/css/form-components.css"
        with open(css_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        for style in button_styles:
            assert style in content, f"缺少{style}样式"
    
    def test_form_layout_styles(self):
        """测试表单布局样式"""
        # 测试布局样式
        layout_styles = [
            ".form-group",
            ".form-label-container",
            ".form-actions",
            ".content-container"
        ]
        
        css_file = "/home/wy/blogn2/src/static/css/form-components.css"
        with open(css_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        for style in layout_styles:
            assert style in content, f"缺少{style}样式"


class TestFormComponentsFunctionality:
    """表单组件功能测试类"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        # 模拟浏览器环境
        self.mock_document = MagicMock()
        self.mock_window = MagicMock()
        
        # 模拟全局对象
        with patch('builtins.window', self.mock_window), \
             patch('builtins.document', self.mock_document), \
             patch('builtins.Node', MagicMock()), \
             patch('builtins.customElements', MagicMock()):
            
            # 导入相关组件
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
    
    def test_form_validation_logic(self):
        """测试表单验证逻辑"""
        # 测试URL验证
        assert self.component.isValidUrl("https://example.com") == True
        assert self.component.isValidUrl("http://example.com") == True
        assert self.component.isValidUrl("javascript:alert('xss')") == False
        
        # 测试图片src验证
        assert self.component.isValidImageSrc("https://example.com/image.jpg") == True
        assert self.component.isValidImageSrc("http://example.com/image.png") == True
        assert self.component.isValidImageSrc("javascript:alert('xss')") == False
        
        # 测试HTML转义
        assert self.component.escapeHtml("<script>alert('xss')</script>") == "&lt;script&gt;alert(&#39;xss&#39;)&lt;/script&gt;"
    
    def test_form_preview_functionality(self):
        """测试表单预览功能"""
        # 测试Markdown预览
        markdown_text = "# 标题\n\n**粗体**文本"
        stripped_text = self.component.stripMarkdown(markdown_text)
        assert "标题" in stripped_text
        assert "粗体" in stripped_text
        assert "#" not in stripped_text
        assert "**" not in stripped_text
    
    def test_form_image_upload_functionality(self):
        """测试表单图片上传功能"""
        # 测试图片URL验证
        valid_urls = [
            "https://example.com/image.jpg",
            "http://example.com/image.png",
            "https://example.com/image.gif"
        ]
        
        for url in valid_urls:
            assert self.component.isValidImageSrc(url) == True
        
        # 测试无效图片URL
        invalid_urls = [
            "javascript:alert('xss')",
            "ftp://example.com/image.jpg",
            "data:image/png;base64,iVBORw0KGgo="
        ]
        
        for url in invalid_urls:
            assert self.component.isValidImageSrc(url) == False
    
    def test_form_error_handling(self):
        """测试表单错误处理"""
        # 测试错误状态HTML创建
        error_html = self.component.createErrorHTML("测试错误")
        assert "测试错误" in error_html
        assert "error" in error_html.lower() or "失败" in error_html
        
        # 测试加载状态HTML创建
        loading_html = self.component.createLoadingHTML()
        assert "加载中" in loading_html
        assert "loading" in loading_html.lower() or "加载" in loading_html


if __name__ == "__main__":
    pytest.main([__file__])
