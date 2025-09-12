"""
CSS提取功能测试模块

测试CSS提取和重构功能，包括：
- CSS文件提取和合并
- 样式去重
- 变量使用
- 响应式设计
- 动画效果
"""

import pytest
import os
import re
from pathlib import Path


class TestCSSExtraction:
    """CSS提取功能测试类"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.css_dir = Path("/home/wy/blogn2/src/static/css")
        self.form_components_css = self.css_dir / "form-components.css"
        self.components_css = self.css_dir / "components.css"
    
    def test_form_components_css_exists(self):
        """测试form-components.css文件存在"""
        assert self.form_components_css.exists(), "form-components.css文件不存在"
    
    def test_form_components_css_size(self):
        """测试form-components.css文件大小"""
        if self.form_components_css.exists():
            size = self.form_components_css.stat().st_size
            assert size > 0, "form-components.css文件为空"
            assert size > 1000, "form-components.css文件过小，可能缺少内容"
    
    def test_form_components_css_structure(self):
        """测试form-components.css文件结构"""
        if not self.form_components_css.exists():
            pytest.skip("form-components.css文件不存在")
        
        with open(self.form_components_css, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查文件头部注释
        assert "/* 表单组件公共样式 */" in content, "缺少文件头部注释"
        
        # 检查主要样式块
        main_sections = [
            "/* 表单基础样式 */",
            "/* 按钮样式 */",
            "/* 消息样式 */",
            "/* 加载状态 */",
            "/* 预览功能样式 */",
            "/* Markdown预览样式 */",
            "/* 图片上传样式 */",
            "/* 登录要求样式 */"
        ]
        
        for section in main_sections:
            assert section in content, f"缺少{section}部分"
    
    def test_css_variables_usage(self):
        """测试CSS变量使用"""
        if not self.form_components_css.exists():
            pytest.skip("form-components.css文件不存在")
        
        with open(self.form_components_css, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查CSS变量使用模式
        var_pattern = r'var\(--[a-zA-Z-]+\)'
        variables = re.findall(var_pattern, content)
        
        assert len(variables) > 0, "没有使用CSS变量"
        assert len(variables) > 20, "CSS变量使用过少"
        
        # 检查常用变量
        common_vars = [
            "var(--spacing-",
            "var(--gray-",
            "var(--primary-color)",
            "var(--radius-",
            "var(--font-size-",
            "var(--transition-",
            "var(--white)",
            "var(--error-color)"
        ]
        
        for var in common_vars:
            assert var in content, f"缺少{var}变量使用"
    
    def test_css_selector_organization(self):
        """测试CSS选择器组织"""
        if not self.form_components_css.exists():
            pytest.skip("form-components.css文件不存在")
        
        with open(self.form_components_css, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查选择器组织
        selectors = re.findall(r'^\.([a-zA-Z-]+)', content, re.MULTILINE)
        
        # 检查表单相关选择器
        form_selectors = [s for s in selectors if s.startswith('form-')]
        assert len(form_selectors) > 0, "缺少表单相关选择器"
        
        # 检查按钮相关选择器
        button_selectors = [s for s in selectors if s.startswith('btn')]
        assert len(button_selectors) > 0, "缺少按钮相关选择器"
        
        # 检查消息相关选择器
        message_selectors = [s for s in selectors if 'message' in s]
        assert len(message_selectors) > 0, "缺少消息相关选择器"
        
        # 检查加载相关选择器
        loading_selectors = [s for s in selectors if 'loading' in s]
        assert len(loading_selectors) > 0, "缺少加载相关选择器"
        
        # 检查预览相关选择器
        preview_selectors = [s for s in selectors if 'preview' in s]
        assert len(preview_selectors) > 0, "缺少预览相关选择器"
        
        # 检查图片相关选择器
        image_selectors = [s for s in selectors if 'image' in s]
        assert len(image_selectors) > 0, "缺少图片相关选择器"
    
    def test_css_responsive_design(self):
        """测试响应式设计"""
        if not self.form_components_css.exists():
            pytest.skip("form-components.css文件不存在")
        
        with open(self.form_components_css, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查响应式相关属性
        responsive_properties = [
            "max-width: 100%",
            "height: auto",
            "grid-template-columns",
            "minmax(",
            "auto-fill",
            "auto-fit"
        ]
        
        for prop in responsive_properties:
            assert prop in content, f"缺少响应式属性: {prop}"
    
    def test_css_animations(self):
        """测试动画效果"""
        if not self.form_components_css.exists():
            pytest.skip("form-components.css文件不存在")
        
        with open(self.form_components_css, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查动画相关属性
        animation_properties = [
            "@keyframes",
            "animation:",
            "transition:",
            "transform:"
        ]
        
        for prop in animation_properties:
            assert prop in content, f"缺少动画属性: {prop}"
        
        # 检查特定动画
        assert "@keyframes spin" in content, "缺少旋转动画"
        assert "animation: spin" in content, "缺少旋转动画应用"
    
    def test_css_accessibility(self):
        """测试无障碍设计"""
        if not self.form_components_css.exists():
            pytest.skip("form-components.css文件不存在")
        
        with open(self.form_components_css, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查无障碍相关属性
        accessibility_properties = [
            "cursor: pointer",
            "cursor: not-allowed",
            ":focus",
            ":hover",
            ":disabled"
        ]
        
        for prop in accessibility_properties:
            assert prop in content, f"缺少无障碍属性: {prop}"
    
    def test_css_consistency(self):
        """测试CSS一致性"""
        if not self.form_components_css.exists():
            pytest.skip("form-components.css文件不存在")
        
        with open(self.form_components_css, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查缩进一致性
        lines = content.split('\n')
        indent_sizes = set()
        
        for line in lines:
            if line.strip() and not line.startswith('/*'):
                leading_spaces = len(line) - len(line.lstrip())
                if leading_spaces > 0:
                    indent_sizes.add(leading_spaces)
        
        # 应该只有一种缩进大小
        assert len(indent_sizes) <= 2, f"缩进不一致，发现多种缩进大小: {indent_sizes}"
        
        # 检查分号使用
        semicolon_lines = [line for line in lines if ';' in line and not line.strip().startswith('/*')]
        assert len(semicolon_lines) > 0, "没有使用分号"
        
        # 检查大括号使用
        brace_lines = [line for line in lines if '{' in line or '}' in line]
        assert len(brace_lines) > 0, "没有使用大括号"
    
    def test_css_duplication_removal(self):
        """测试CSS重复移除"""
        if not self.form_components_css.exists():
            pytest.skip("form-components.css文件不存在")
        
        with open(self.form_components_css, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查重复的CSS规则
        lines = content.split('\n')
        rule_lines = [line.strip() for line in lines if line.strip() and not line.strip().startswith('/*')]
        
        # 检查重复的选择器
        selectors = []
        for line in rule_lines:
            if line.endswith('{'):
                selector = line[:-1].strip()
                selectors.append(selector)
        
        # 检查是否有重复的选择器
        duplicate_selectors = [s for s in set(selectors) if selectors.count(s) > 1]
        assert len(duplicate_selectors) == 0, f"发现重复的选择器: {duplicate_selectors}"
    
    def test_css_file_encoding(self):
        """测试CSS文件编码"""
        if not self.form_components_css.exists():
            pytest.skip("form-components.css文件不存在")
        
        # 尝试用UTF-8编码读取文件
        try:
            with open(self.form_components_css, 'r', encoding='utf-8') as f:
                content = f.read()
            assert True, "文件编码正确"
        except UnicodeDecodeError:
            pytest.fail("文件编码不是UTF-8")
    
    def test_css_file_permissions(self):
        """测试CSS文件权限"""
        if not self.form_components_css.exists():
            pytest.skip("form-components.css文件不存在")
        
        # 检查文件是否可读
        assert os.access(self.form_components_css, os.R_OK), "文件不可读"
        
        # 检查文件是否可写
        assert os.access(self.form_components_css, os.W_OK), "文件不可写"


class TestCSSIntegration:
    """CSS集成测试类"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.css_dir = Path("/home/wy/blogn2/src/static/css")
        self.form_components_css = self.css_dir / "form-components.css"
        self.components_css = self.css_dir / "components.css"
    
    def test_css_file_dependencies(self):
        """测试CSS文件依赖关系"""
        if not self.form_components_css.exists():
            pytest.skip("form-components.css文件不存在")
        
        with open(self.form_components_css, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否有外部依赖
        import_pattern = r'@import\s+["\']([^"\']+)["\']'
        imports = re.findall(import_pattern, content)
        
        # 如果有导入，检查文件是否存在
        for import_path in imports:
            if not import_path.startswith('http'):
                full_path = self.css_dir / import_path
                assert full_path.exists(), f"导入的CSS文件不存在: {import_path}"
    
    def test_css_variable_consistency(self):
        """测试CSS变量一致性"""
        if not self.form_components_css.exists():
            pytest.skip("form-components.css文件不存在")
        
        with open(self.form_components_css, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取所有使用的变量
        var_pattern = r'var\(--([a-zA-Z-]+)\)'
        used_vars = re.findall(var_pattern, content)
        
        # 检查变量命名一致性
        for var in used_vars:
            assert '-' in var or var.islower(), f"变量命名不一致: --{var}"
    
    def test_css_selector_specificity(self):
        """测试CSS选择器特异性"""
        if not self.form_components_css.exists():
            pytest.skip("form-components.css文件不存在")
        
        with open(self.form_components_css, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查选择器特异性
        lines = content.split('\n')
        for line in lines:
            if line.strip() and not line.strip().startswith('/*'):
                # 检查是否有过于具体的选择器
                if line.count(' ') > 3:
                    pytest.warn(f"选择器过于具体: {line.strip()}")
    
    def test_css_performance(self):
        """测试CSS性能"""
        if not self.form_components_css.exists():
            pytest.skip("form-components.css文件不存在")
        
        with open(self.form_components_css, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查文件大小
        file_size = len(content)
        assert file_size < 100000, f"CSS文件过大: {file_size} 字节"
        
        # 检查选择器数量
        selector_count = len(re.findall(r'^\.([a-zA-Z-]+)', content, re.MULTILINE))
        assert selector_count < 200, f"选择器过多: {selector_count} 个"
        
        # 检查规则数量
        rule_count = len(re.findall(r'\{[^}]*\}', content))
        assert rule_count < 500, f"CSS规则过多: {rule_count} 个"


if __name__ == "__main__":
    pytest.main([__file__])
