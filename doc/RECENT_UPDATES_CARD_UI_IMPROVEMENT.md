# 最近更新卡片 UI 改进总结

## 改进概述

最近更新卡片（`recent-updates-card.js`）在条目头部行内显示 **24×24** 小头像，样式与 `blog-list-card` 文章列表的作者 meta 一致；整行可点击跳转至文章页。

## 当前布局

```
┌─────────────────────────────────────────┐
│ [24px头像] 博客名称          时间       │
│ 文章标题（截断）                        │
└─────────────────────────────────────────┘
```

- 头像与名称在同一行（`.meta-item-author`），不再使用左侧 40px 大头像列
- 点击整行（`<a class="update-link">`）打开 `/article/{id}`，新标签页

## 头像显示逻辑

与 `blog-list-card` 的 `renderAuthorMetaItem` 对齐：

```javascript
getSmallAvatarPath(userId) {
    if (!userId) return null;
    const prefix = Math.floor(userId / 10000) + 1;
    return `/avatar/${prefix}/s_${userId}.jpg`;
}

renderAuthorMetaItem(authorName, avatar, userId) {
    const avatarPath = avatar || this.getSmallAvatarPath(userId);
    // 24×24 .author-avatar + .author-name
}
```

- **显示名称**：`blog_name`（博客名）
- **头像来源**：API 字段 `avatar`，或按 `userid` 推导小图路径
- **fallback**：无图时显示名称首字母

## 样式要点

```css
.author-avatar {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    border: 1px solid var(--gray-200);
}

.meta-item-author {
    display: flex;
    align-items: center;
    gap: var(--spacing-2);
    min-width: 0;
}

.author-name {
    font-weight: 700;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
```

## 数据与 API

数据来源仍为 `GET /api/blogs/posts/latest?limit=5`（博客页可加 `exclude={project_id}`）。响应中每条 post 含 `id`、`title`、`blog_name`、`author`、`avatar`、`userid`、`time` 等字段。

## 相关组件

- `recent-comments-card.js`：同样采用 24px 内联头像，显示 **作者名**（`author`）
- `blog-list-card.js`：作者 meta 的参考实现
- `messages-list-card.js`、`thread-card.js`：留言/帖子页亦使用相同 24px 头像约定

## 历史变更说明

早期版本曾在条目左侧使用 **40×40** 大头像列；自 UI 统一化后改为与文章列表一致的内联小头像，以减少侧边栏横向占用并保持视觉一致。
