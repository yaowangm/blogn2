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
};

window.FolderFilter = FolderFilter;
