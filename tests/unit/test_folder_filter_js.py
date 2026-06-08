"""
博客分类 folderid 筛选 JS 工具模块的静态检查

验证 folder-filter.js 存在且导出 FolderFilter API，
确保 folderid=0（未分类）被当作有效筛选条件。
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
FOLDER_FILTER_JS = PROJECT_ROOT / "src" / "static" / "js" / "utils" / "folder-filter.js"
BLOG_HTML = PROJECT_ROOT / "src" / "static" / "blog.html"
INDEX_HTML = PROJECT_ROOT / "src" / "static" / "index.html"
BLOG_LIST_CARD_JS = PROJECT_ROOT / "src" / "static" / "js" / "components" / "blog_list_card.js"
BLOG_POSTS_LIST_CARD_JS = PROJECT_ROOT / "src" / "static" / "js" / "components" / "blog-posts-list-card.js"


class TestFolderFilterJs:
    def test_folder_filter_js_file_exists(self):
        assert FOLDER_FILTER_JS.exists(), f"Expected script at {FOLDER_FILTER_JS}"

    def test_exports_window_folder_filter(self):
        content = FOLDER_FILTER_JS.read_text(encoding="utf-8")
        assert "normalizeFolderId" in content
        assert "shouldIncludeFolderInApi" in content
        assert "getCategoryLabel" in content
        assert "isUncategorizedFolderId" in content
        assert "window.FolderFilter" in content

    def test_blog_pages_load_folder_filter_before_list_cards(self):
        for html_path in (BLOG_HTML, INDEX_HTML):
            content = html_path.read_text(encoding="utf-8")
            filter_pos = content.index("folder-filter.js")
            list_pos = content.index("blog_list_card.js")
            assert filter_pos < list_pos, f"{html_path.name} must load folder-filter.js before blog_list_card.js"

    def test_list_cards_use_folder_filter_util(self):
        for js_path in (BLOG_LIST_CARD_JS, BLOG_POSTS_LIST_CARD_JS):
            content = js_path.read_text(encoding="utf-8")
            assert "FolderFilter.shouldIncludeFolderInApi" in content, js_path.name
            assert "FolderFilter.normalizeFolderId" in content, js_path.name
            assert "FolderFilter.getCategoryLabel" in content, js_path.name
            assert "this.shouldIncludeFolderInApi" not in content, js_path.name
