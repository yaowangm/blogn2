"""
Markdown功能测试模块

测试Markdown相关的功能，包括：
- Markdown解析和渲染
- 实时预览功能
- 样式应用
- 安全过滤
"""

import pytest
from unittest.mock import patch, MagicMock
import json


class TestMarkdownFeatures:
    """Markdown功能测试类"""
    
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
    
    def test_markdown_heading_parsing(self):
        """测试Markdown标题解析"""
        test_cases = [
            ("# 一级标题", "一级标题"),
            ("## 二级标题", "二级标题"),
            ("### 三级标题", "三级标题"),
            ("#### 四级标题", "四级标题"),
            ("##### 五级标题", "五级标题"),
            ("###### 六级标题", "六级标题"),
        ]
        
        for markdown, expected in test_cases:
            result = self.component.stripMarkdown(markdown)
            assert result == expected, f"Failed for: {markdown}"
    
    def test_markdown_emphasis_parsing(self):
        """测试Markdown强调标记解析"""
        test_cases = [
            ("**粗体文本**", "粗体文本"),
            ("*斜体文本*", "斜体文本"),
            ("__粗体文本__", "粗体文本"),
            ("_斜体文本_", "斜体文本"),
            ("~~删除线文本~~", "删除线文本"),
            ("`行内代码`", "行内代码"),
        ]
        
        for markdown, expected in test_cases:
            result = self.component.stripMarkdown(markdown)
            assert result == expected, f"Failed for: {markdown}"
    
    def test_markdown_list_parsing(self):
        """测试Markdown列表解析"""
        test_cases = [
            ("- 无序列表项", "无序列表项"),
            ("* 无序列表项", "无序列表项"),
            ("+ 无序列表项", "无序列表项"),
            ("1. 有序列表项", "有序列表项"),
            ("2. 有序列表项", "有序列表项"),
        ]
        
        for markdown, expected in test_cases:
            result = self.component.stripMarkdown(markdown)
            assert result == expected, f"Failed for: {markdown}"
    
    def test_markdown_link_parsing(self):
        """测试Markdown链接解析"""
        test_cases = [
            ("[链接文本](https://example.com)", "链接文本"),
            ("[链接文本](http://example.com)", "链接文本"),
            ("[链接文本](mailto:test@example.com)", "链接文本"),
        ]
        
        for markdown, expected in test_cases:
            result = self.component.stripMarkdown(markdown)
            assert result == expected, f"Failed for: {markdown}"
    
    def test_markdown_image_parsing(self):
        """测试Markdown图片解析"""
        test_cases = [
            ("![图片描述](https://example.com/image.jpg)", "图片描述"),
            ("![图片描述](http://example.com/image.png)", "图片描述"),
            ("![](https://example.com/image.gif)", ""),
        ]
        
        for markdown, expected in test_cases:
            result = self.component.stripMarkdown(markdown)
            assert result == expected, f"Failed for: {markdown}"
    
    def test_markdown_code_block_parsing(self):
        """测试Markdown代码块解析"""
        test_cases = [
            ("```python\nprint('hello')\n```", ""),
            ("```javascript\nconsole.log('hello')\n```", ""),
            ("```\nplain text\n```", ""),
            ("~~~python\nprint('hello')\n~~~", ""),
        ]
        
        for markdown, expected in test_cases:
            result = self.component.stripMarkdown(markdown)
            assert result == expected, f"Failed for: {markdown}"
    
    def test_markdown_quote_parsing(self):
        """测试Markdown引用解析"""
        test_cases = [
            ("> 引用内容", "引用内容"),
            ("> 多行引用\n> 第二行", "多行引用\n第二行"),
        ]
        
        for markdown, expected in test_cases:
            result = self.component.stripMarkdown(markdown)
            assert result == expected, f"Failed for: {markdown}"
    
    def test_markdown_table_parsing(self):
        """测试Markdown表格解析"""
        test_cases = [
            ("| 列1 | 列2 |", "列1 列2"),
            ("| 列1 | 列2 |\n| 值1 | 值2 |", "列1 列2\n值1 值2"),
        ]
        
        for markdown, expected in test_cases:
            result = self.component.stripMarkdown(markdown)
            assert result == expected, f"Failed for: {markdown}"
    
    def test_markdown_horizontal_rule_parsing(self):
        """测试Markdown水平线解析"""
        test_cases = [
            ("---", ""),
            ("***", ""),
            ("___", ""),
        ]
        
        for markdown, expected in test_cases:
            result = self.component.stripMarkdown(markdown)
            assert result == expected, f"Failed for: {markdown}"
    
    def test_markdown_complex_parsing(self):
        """测试复杂Markdown内容解析"""
        complex_markdown = """
# 标题

这是一个**粗体**和*斜体*的段落。

- 列表项1
- 列表项2

```python
def hello():
    print("Hello World")
```

[链接](https://example.com)

> 这是一个引用
"""
        
        result = self.component.stripMarkdown(complex_markdown)
        
        # 检查各种标记都被正确移除
        assert "#" not in result
        assert "**" not in result
        assert "*" not in result
        assert "-" not in result
        assert "```" not in result
        assert "[" not in result
        assert "]" not in result
        assert "(" not in result
        assert ")" not in result
        assert ">" not in result
        
        # 检查内容被保留
        assert "标题" in result
        assert "粗体" in result
        assert "斜体" in result
        assert "列表项1" in result
        assert "列表项2" in result
        assert "链接" in result
        assert "引用" in result
    
    def test_markdown_whitespace_handling(self):
        """测试Markdown空白字符处理"""
        test_cases = [
            ("   \n\n   \n   ", ""),  # 只有空白字符
            ("  \n  \n  ", ""),  # 只有空白字符和换行
            ("文本\n\n\n文本", "文本 文本"),  # 多个换行符
            ("文本   \n   \n   文本", "文本 文本"),  # 混合空白字符
        ]
        
        for markdown, expected in result:
            result = self.component.stripMarkdown(markdown)
            assert result == expected, f"Failed for: {markdown}"
    
    def test_markdown_edge_cases(self):
        """测试Markdown边界情况"""
        test_cases = [
            ("", ""),  # 空字符串
            (None, ""),  # None值
            (123, ""),  # 非字符串类型
            ("普通文本", "普通文本"),  # 无Markdown标记
            ("#", ""),  # 只有标记符号
            ("**", ""),  # 只有标记符号
            ("*", ""),  # 只有标记符号
        ]
        
        for markdown, expected in test_cases:
            result = self.component.stripMarkdown(markdown)
            assert result == expected, f"Failed for: {markdown}"
    
    def test_markdown_nested_elements(self):
        """测试嵌套Markdown元素"""
        test_cases = [
            ("**粗体*斜体*粗体**", "粗体斜体粗体"),
            ("*斜体**粗体**斜体*", "斜体粗体斜体"),
            ("[**粗体链接**](https://example.com)", "粗体链接"),
            ("![*斜体图片*](https://example.com/image.jpg)", "斜体图片"),
        ]
        
        for markdown, expected in test_cases:
            result = self.component.stripMarkdown(markdown)
            assert result == expected, f"Failed for: {markdown}"
    
    def test_markdown_special_characters(self):
        """测试Markdown特殊字符处理"""
        test_cases = [
            ("文本 & 符号", "文本 & 符号"),
            ("文本 < 符号", "文本 < 符号"),
            ("文本 > 符号", "文本 > 符号"),
            ("文本 \" 引号", "文本 \" 引号"),
            ("文本 ' 引号", "文本 ' 引号"),
        ]
        
        for markdown, expected in test_cases:
            result = self.component.stripMarkdown(markdown)
            assert result == expected, f"Failed for: {markdown}"
    
    def test_markdown_multiline_handling(self):
        """测试多行Markdown处理"""
        multiline_markdown = """
# 标题1

段落1

## 标题2

段落2

- 列表项1
- 列表项2

```python
代码块
```

> 引用内容
"""
        
        result = self.component.stripMarkdown(multiline_markdown)
        
        # 检查多行内容被正确处理
        lines = result.split('\n')
        non_empty_lines = [line.strip() for line in lines if line.strip()]
        
        assert len(non_empty_lines) > 0
        assert "标题1" in result
        assert "段落1" in result
        assert "标题2" in result
        assert "段落2" in result
        assert "列表项1" in result
        assert "列表项2" in result
        assert "引用内容" in result


class TestMarkdownSecurity:
    """Markdown安全测试类"""
    
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
    
    def test_markdown_xss_protection(self):
        """测试Markdown XSS防护"""
        # 测试脚本注入
        malicious_markdown = "正常文本<script>alert('xss')</script>"
        result = self.component.stripMarkdown(malicious_markdown)
        assert "<script>" not in result
        assert "alert('xss')" not in result
        assert "正常文本" in result
        
        # 测试事件处理器
        malicious_markdown = "正常文本<img src='x' onerror='alert(1)'>"
        result = self.component.stripMarkdown(malicious_markdown)
        assert "onerror" not in result
        assert "alert(1)" not in result
        assert "正常文本" in result
        
        # 测试JavaScript协议
        malicious_markdown = "[链接](javascript:alert('xss'))"
        result = self.component.stripMarkdown(malicious_markdown)
        assert "javascript:" not in result
        assert "alert('xss')" not in result
        assert "链接" in result
    
    def test_markdown_html_escaping(self):
        """测试Markdown HTML转义"""
        test_cases = [
            ("文本 & 符号", "文本 & 符号"),
            ("文本 < 符号", "文本 < 符号"),
            ("文本 > 符号", "文本 > 符号"),
            ("文本 \" 引号", "文本 \" 引号"),
            ("文本 ' 引号", "文本 ' 引号"),
        ]
        
        for markdown, expected in test_cases:
            result = self.component.stripMarkdown(markdown)
            assert result == expected, f"Failed for: {markdown}"


if __name__ == "__main__":
    pytest.main([__file__])
