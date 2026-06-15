/**
 * 博客文章表单草稿本地缓存
 * 每 2 秒在内容变化时写入 localStorage，页面恢复后读取。
 */
class PostFormDraftCache {
    static STORAGE_PREFIX = 'blogn_post_draft';
    static AUTOSAVE_INTERVAL_MS = 2000;
    static DRAFT_FIELDS = ['name', 'comment', 'folderid', 'allowpost'];

    static getCreateKey(userId, projectId) {
        return `${this.STORAGE_PREFIX}:create:${userId}:${projectId}`;
    }

    static getEditKey(userId, articleId) {
        return `${this.STORAGE_PREFIX}:edit:${userId}:${articleId}`;
    }

    static pickDraftFields(source) {
        const draft = {};
        for (const field of this.DRAFT_FIELDS) {
            if (Object.prototype.hasOwnProperty.call(source, field)) {
                draft[field] = source[field];
            }
        }
        return draft;
    }

    static serializeDraft(formData) {
        return JSON.stringify(this.pickDraftFields(formData));
    }

    static isDraftEmpty(draft) {
        const name = typeof draft.name === 'string' ? draft.name.trim() : '';
        const comment = typeof draft.comment === 'string' ? draft.comment.trim() : '';
        return !name && !comment;
    }

    static normalizeDraftFieldValue(field, value) {
        if (field === 'folderid') {
            return value == null || value === '' ? null : Number(value);
        }
        if (field === 'allowpost') {
            return value == null || value === '' ? null : Number(value);
        }
        return value ?? '';
    }

    static draftDiffersFrom(draft, baseline) {
        for (const field of this.DRAFT_FIELDS) {
            const left = this.normalizeDraftFieldValue(field, draft[field]);
            const right = this.normalizeDraftFieldValue(field, baseline[field]);
            if (left !== right) {
                return true;
            }
        }
        return false;
    }

    static load(key) {
        try {
            const raw = localStorage.getItem(key);
            if (!raw) {
                return null;
            }
            const data = JSON.parse(raw);
            if (!data || typeof data !== 'object') {
                return null;
            }
            return this.pickDraftFields(data);
        } catch (error) {
            console.warn('Failed to load post draft:', error);
            return null;
        }
    }

    static save(key, formData) {
        try {
            const draft = this.pickDraftFields(formData);
            if (this.isDraftEmpty(draft)) {
                localStorage.removeItem(key);
                return false;
            }
            const payload = {
                ...draft,
                savedAt: Date.now(),
                userId: UserManager.getCurrentUserId()
            };
            localStorage.setItem(key, JSON.stringify(payload));
            return true;
        } catch (error) {
            console.warn('Failed to save post draft:', error);
            return false;
        }
    }

    static clear(key) {
        try {
            localStorage.removeItem(key);
        } catch (error) {
            console.warn('Failed to clear post draft:', error);
        }
    }

    static clearAllForUser(userId = null) {
        UserManager.clearPostFormDrafts(userId);
    }

    static createAutoSaver({ key, getFormData }) {
        return new PostFormDraftAutoSaver(key, getFormData);
    }

    static showDraftSavedHint(shadowRoot) {
        const hint = shadowRoot?.querySelector('.draft-cache-hint');
        if (hint) {
            hint.textContent = '草稿已经保存到本地缓存';
            hint.hidden = false;
        }
    }

    static showDraftRestoredHint(shadowRoot, message = '已恢复未保存的草稿') {
        const hint = shadowRoot?.querySelector('.draft-cache-hint');
        if (hint) {
            hint.textContent = message;
            hint.hidden = false;
        }
    }

    static hideDraftSavedHint(shadowRoot) {
        const hint = shadowRoot?.querySelector('.draft-cache-hint');
        if (hint) {
            hint.hidden = true;
        }
    }
}

class PostFormDraftAutoSaver {
    constructor(key, getFormData) {
        this.key = key;
        this.getFormData = getFormData;
        this._component = null;
        this._intervalId = null;
        this._lastSavedSnapshot = null;
        this._onPageShow = null;
    }

    resetSavedSnapshot() {
        this._lastSavedSnapshot = null;
    }

    syncSavedSnapshotFromStorage() {
        const draft = PostFormDraftCache.load(this.key);
        this._lastSavedSnapshot = draft ? PostFormDraftCache.serializeDraft(draft) : null;
    }

    tick() {
        if (!UserManager.isLoggedIn()) {
            return;
        }

        const formData = this.getFormData();
        const snapshot = PostFormDraftCache.serializeDraft(formData);
        if (snapshot === this._lastSavedSnapshot) {
            return;
        }

        if (PostFormDraftCache.save(this.key, formData)) {
            this._lastSavedSnapshot = snapshot;
            PostFormDraftCache.showDraftSavedHint(this._component?.shadowRoot);
            return;
        }

        if (PostFormDraftCache.isDraftEmpty(PostFormDraftCache.pickDraftFields(formData))) {
            this._lastSavedSnapshot = null;
        }
    }

    start(component) {
        this.stop();
        this._component = component;
        this.syncSavedSnapshotFromStorage();
        this._intervalId = window.setInterval(
            () => this.tick(),
            PostFormDraftCache.AUTOSAVE_INTERVAL_MS
        );

        this._onPageShow = () => {
            if (!UserManager.isLoggedIn()) {
                return;
            }
            const draft = PostFormDraftCache.load(this.key);
            if (!draft) {
                return;
            }
            component.applyDraft(draft);
            component.syncFormFieldsFromDraft(draft);
            this.syncSavedSnapshotFromStorage();
        };
        window.addEventListener('pageshow', this._onPageShow);
    }

    stop() {
        if (this._intervalId !== null) {
            window.clearInterval(this._intervalId);
            this._intervalId = null;
        }
        if (this._onPageShow) {
            window.removeEventListener('pageshow', this._onPageShow);
            this._onPageShow = null;
        }
        this._component = null;
    }
}
