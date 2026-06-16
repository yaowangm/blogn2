# 全站性能检查报告（基于 09c3ccf 同类问题）

参考提交 09c3ccf 的优化模式：
1. 从 URL 读取分页等参数，避免首屏错加载
2. 避免串行等待（如先 await checkOwnership 再 loadData）
3. 避免同一数据被多处重复请求

---

## 1. 留言列表页：未从 URL 读 page

**位置**：`src/static/js/components/messages-list-card.js`

**问题**：`currentPage` 固定为 1，未从 URL 读取。若用户打开 `/messages?page=3` 或从分页跳转带 `?page=`，仍会请求第 1 页。

**已实现**：在 `connectedCallback` 中设置 `this.currentPage = this.getCurrentPageFromUrl()`，再调用 `loadMessages()`。

---

## 2. 博客页：多处重复请求 /api/projects/{id}

**位置**：博客页 `blog.html` 上的多个组件

**问题**：以下组件在挂载时各自请求同一条项目接口，同一博客页会触发多次相同请求：
- `blog-posts-list-card`（checkOwnership）
- `blog-header-card`（约 2 次）
- `categories-card`（checkOwnership）
- `blog-navigation-card`
- `blog-profile-card`
- `friend-links-card`（checkOwnership）
- `subscriptions-list-card`（checkOwnership）
- `recent-updates-card`（按 projectId 排除时用）

**已实现**：在 `BaseComponent` 中增加静态方法 `getProject(projectId)`，同页多组件共用同一请求（内存缓存 + 进行中 Promise 复用）。博客页各组件均改为调用 `BaseComponent.getProject(this.projectId)`。

---

## 3. 文章页：多处重复请求 /api/articles/{id}

**位置**：文章页 `article.html` 上的组件

**问题**：以下组件各自请求同一条文章接口：
- `article-header-card`
- `article-content-card`
- `comment-form-card`
- `comment-settings-card`

**已实现**：
- 在 `BaseComponent` 中增加静态方法 `getArticle(articleId)`，上述组件共用同一请求。
- `article-comments-card` 改为请求独立接口 `GET /api/articles/{id}/comments?page=&limit=`，不再拉取整篇文章；评论项含 `author_name`、`author_avatar`，避免逐条请求 `/api/users/{id}`。

---

## 4. 串行 await checkOwnership 再 loadData

**位置**：
- `subscriptions-list-card.js`
- `friend-links-card.js`
- `blog_list_card.js`（分类菜单）

**问题**：首屏需等 project 请求完成再请求列表，总耗时 = 两次串行往返。

**已实现**：
- `subscriptions-list-card`、`friend-links-card`：`checkOwnership` 与列表加载并行。
- `blog_list_card`：分类/所有权与 `loadContent` 并行；`loadPageSizeConfig` 通过 `BaseComponent.getAppConfig()` 共享。

---

## 5. 搜索页

**位置**：`src/static/js/pages/search.js`

**现状**：已通过 `loadSearchParams()` 从 URL 读取 `q`、`type`、`sort`、`page` 并用于请求，无同类问题。

---

## 已实现修复汇总

- **留言列表**：`messages-list-card` 从 URL 读取 `page` 并用于首屏请求。
- **订阅列表**：`subscriptions-list-card` 中 checkOwnership 与 loadSubscriptions 并行执行；首屏从 URL 读取 `page` 并请求对应页。
- **友链卡片**：`friend-links-card` 中 checkOwnership 与 loadData 并行执行。
- **博客页**：`BaseComponent.getProject()` / `getUser()` / `getMetadata()` / `getAppConfig()` 共享请求；侧边栏卡片可见时再加载。
- **文章页**：`getArticle()` 共享正文；评论走 `/api/articles/{id}/comments`。
- **博文列表 API**：响应只含摘要，避免传输完整正文。

---

## 6. 前端共享请求与首屏加载

**位置**：`base-component.js`、`header-component.js`、各 sidebar 卡片

**已实现**：
- `getMetadata()` / `getUser()` / `getAppConfig()`：同页多组件共用内存缓存与进行中的 Promise。
- `blog_list_card`：翻页时只更新列表区域，不全量重建 shadow DOM。
- `article.html`：脚本使用 `defer`。
- `recent-comments-card`、`recent-updates-card`、`friend-links-card`：进入视口后再 `loadData()`。
