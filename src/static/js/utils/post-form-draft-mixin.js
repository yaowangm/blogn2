/**
 * Shared draft-cache helpers for create/edit post form components.
 */
const PostFormDraftMixin = {
    disconnected(component) {
        component._draftAutoSaver?.stop();
    },

    init(component, cacheKey) {
        component._draftCacheKey = cacheKey;
        component._draftAutoSaver = PostFormDraftCache.createAutoSaver({
            key: component._draftCacheKey,
            getFormData: () => PostFormDraftMixin.getDraftFormData(component)
        });
    },

    getDraftFormData(component) {
        const root = component.shadowRoot;
        if (!root) {
            return PostFormDraftCache.pickDraftFields(component.formData);
        }

        const folderSelect = root.querySelector('#folderid');
        const allowpostSelect = root.querySelector('#allowpost');
        return {
            name: root.querySelector('#name')?.value ?? component.formData.name ?? '',
            comment: root.querySelector('#comment')?.value ?? component.formData.comment ?? '',
            folderid: folderSelect?.value
                ? parseInt(folderSelect.value, 10)
                : component.formData.folderid,
            allowpost: allowpostSelect?.value
                ? parseInt(allowpostSelect.value, 10)
                : component.formData.allowpost
        };
    },

    restoreDraftIfAny(component, baseline = null) {
        const draft = PostFormDraftCache.load(component._draftCacheKey);
        if (!draft) {
            return false;
        }
        if (baseline && !PostFormDraftCache.draftDiffersFrom(draft, baseline)) {
            return false;
        }
        PostFormDraftMixin.applyDraft(component, draft);
        return true;
    },

    applyDraft(component, draft) {
        if (draft.name !== undefined) {
            component.formData.name = draft.name;
        }
        if (draft.comment !== undefined) {
            component.formData.comment = draft.comment;
        }
        if (draft.folderid !== undefined) {
            component.formData.folderid = draft.folderid;
        }
        if (draft.allowpost !== undefined) {
            component.formData.allowpost = draft.allowpost;
        }
    },

    syncFormFieldsFromDraft(component, draft) {
        PostFormDraftMixin.applyDraft(component, draft);
        const root = component.shadowRoot;
        if (!root) {
            return;
        }

        const nameEl = root.querySelector('#name');
        const commentEl = root.querySelector('#comment');
        const folderEl = root.querySelector('#folderid');
        const allowpostEl = root.querySelector('#allowpost');
        if (nameEl && draft.name !== undefined) {
            nameEl.value = draft.name;
        }
        if (commentEl && draft.comment !== undefined) {
            commentEl.value = draft.comment;
        }
        if (folderEl && draft.folderid != null) {
            folderEl.value = String(draft.folderid);
        }
        if (allowpostEl && draft.allowpost != null) {
            allowpostEl.value = String(draft.allowpost);
        }
    },

    clearDraftCache(component) {
        if (component._draftCacheKey) {
            PostFormDraftCache.clear(component._draftCacheKey);
        }
        component._draftAutoSaver?.resetSavedSnapshot();
        PostFormDraftCache.hideDraftSavedHint(component.shadowRoot);
    },

    clearDraftOnSessionInvalid(component) {
        UserManager.clearPostFormDrafts();
        component._draftAutoSaver?.resetSavedSnapshot();
        component._draftAutoSaver?.stop();
        PostFormDraftCache.hideDraftSavedHint(component.shadowRoot);
    },

    startDraftAutoSave(component) {
        component._draftAutoSaver?.start(component);
    }
};
