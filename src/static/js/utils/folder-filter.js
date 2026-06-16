/**
 * 博客分类 folderid 筛选工具（folderid=0 表示未分类，为有效值）
 */
const FolderFilter = {
    normalizeFolderId(folderId) {
        if (folderId === '' || folderId === undefined || folderId === null) {
            return null;
        }
        return folderId;
    },

    shouldIncludeFolderInApi(folderId) {
        return folderId !== null && folderId !== undefined && folderId !== '';
    },

    isUncategorizedFolderId(folderId) {
        const normalized = FolderFilter.normalizeFolderId(folderId);
        return normalized === '0' || normalized === 0;
    },

    getCategoryLabel(folderId, apiCategory = null, explicitName = null) {
        if (explicitName) {
            return explicitName;
        }
        if (FolderFilter.isUncategorizedFolderId(folderId)) {
            return '未分类';
        }
        if (!FolderFilter.shouldIncludeFolderInApi(FolderFilter.normalizeFolderId(folderId))) {
            return apiCategory || '全部文章';
        }
        return apiCategory || '全部文章';
    },

    syncFolderIdToUrl(folderId) {
        const url = new URL(window.location);
        const normalizedId = FolderFilter.normalizeFolderId(folderId);
        if (FolderFilter.shouldIncludeFolderInApi(normalizedId)) {
            url.searchParams.set('folderid', normalizedId);
        } else {
            url.searchParams.delete('folderid');
        }
        return url;
    },
};

window.FolderFilter = FolderFilter;
