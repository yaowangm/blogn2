"""post-form-draft-cache.js 与表单草稿集成的静态检查。"""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DRAFT_CACHE_JS = PROJECT_ROOT / "src" / "static" / "js" / "utils" / "post-form-draft-cache.js"
DRAFT_MIXIN_JS = PROJECT_ROOT / "src" / "static" / "js" / "utils" / "post-form-draft-mixin.js"
CREATE_POST_HTML = PROJECT_ROOT / "src" / "static" / "create-post.html"
EDIT_ARTICLE_HTML = PROJECT_ROOT / "src" / "static" / "edit-article.html"
CREATE_POST_FORM_JS = PROJECT_ROOT / "src" / "static" / "js" / "components" / "create-post-form.js"
EDIT_POST_FORM_JS = PROJECT_ROOT / "src" / "static" / "js" / "components" / "edit-post-form.js"
PROFILE_JS = PROJECT_ROOT / "src" / "static" / "js" / "profile.js"
REGKEY_JS = PROJECT_ROOT / "src" / "static" / "js" / "regkey.js"


class TestPostFormDraftCacheJs:
    def test_draft_cache_utility_exports(self):
        content = DRAFT_CACHE_JS.read_text(encoding="utf-8")
        assert "class PostFormDraftCache" in content
        assert "class PostFormDraftAutoSaver" in content
        assert "AUTOSAVE_INTERVAL_MS = 2000" in content
        assert "getCreateKey" in content
        assert "getEditKey" in content
        assert "localStorage" in content
        assert "showDraftSavedHint" in content
        assert "showDraftRestoredHint" in content
        assert "draftDiffersFrom" in content
        assert "clearAllForUser" in content

    def test_draft_mixin_exports_shared_helpers(self):
        content = DRAFT_MIXIN_JS.read_text(encoding="utf-8")
        assert "const PostFormDraftMixin" in content
        for helper in (
            "init",
            "getDraftFormData",
            "restoreDraftIfAny",
            "applyDraft",
            "syncFormFieldsFromDraft",
            "clearDraftCache",
            "clearDraftOnSessionInvalid",
            "startDraftAutoSave",
            "disconnected",
        ):
            assert helper in content

    def test_user_manager_clears_post_form_drafts(self):
        content = (PROJECT_ROOT / "src" / "static" / "js" / "utils" / "user-manager.js").read_text(encoding="utf-8")
        assert "clearPostFormDrafts" in content
        assert "blogn_post_draft:" in content

    def test_logout_clears_post_form_drafts(self):
        header = (PROJECT_ROOT / "src" / "static" / "js" / "components" / "header-component.js").read_text(encoding="utf-8")
        token_manager = (PROJECT_ROOT / "src" / "static" / "js" / "services" / "token-manager.js").read_text(encoding="utf-8")
        assert "UserManager.clearPostFormDrafts" in header
        assert "UserManager.clearPostFormDrafts" in token_manager

    def test_profile_and_regkey_clear_drafts_before_token_removal(self):
        token_remove = re.compile(r"localStorage\.removeItem\('access_token'\)")
        for path in (PROFILE_JS, REGKEY_JS):
            content = path.read_text(encoding="utf-8")
            assert "UserManager.clearPostFormDrafts" in content
            for match in token_remove.finditer(content):
                prefix = content[max(0, match.start() - 240):match.start()]
                assert "UserManager.clearPostFormDrafts" in prefix

    def test_post_form_pages_load_draft_cache_script(self):
        for path in (CREATE_POST_HTML, EDIT_ARTICLE_HTML):
            html = path.read_text(encoding="utf-8")
            assert "/static/js/utils/post-form-draft-cache.js" in html
            assert "/static/js/utils/post-form-draft-mixin.js" in html
            assert "/static/js/utils/user-manager.js" in html
            mixin_pos = html.index("post-form-draft-mixin.js")
            form_pos = html.index("-post-form.js")
            assert mixin_pos < form_pos

    def test_post_forms_integrate_draft_cache(self):
        for path in (CREATE_POST_FORM_JS, EDIT_POST_FORM_JS):
            text = path.read_text(encoding="utf-8")
            assert "PostFormDraftMixin" in text
            assert "initDraftCache" in text
            assert "startDraftAutoSave" in text
            assert "clearDraftCache" in text
            assert "clearDraftOnSessionInvalid" in text
            assert "PostFormDraftCache" in text
            assert "draft-cache-hint" in text
            assert "resetSubmitState()" in text
            assert "!tokenManager" in text
            assert "!token" in text

    def test_edit_form_shows_restore_hint_after_draft_recovery(self):
        text = EDIT_POST_FORM_JS.read_text(encoding="utf-8")
        assert "showDraftRestoredHint" in text
        assert "draftRestored" in text
