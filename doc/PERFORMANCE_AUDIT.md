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
- `article-comments-card`（带 page 参数，语义略不同但可能含文章基础信息）
- `comment-form-card`
- `comment-settings-card`

**已实现**：在 `BaseComponent` 中增加静态方法 `getArticle(articleId)`，同页多组件共用同一请求。文章页的 article-header-card、article-content-card、comment-form-card、comment-settings-card 以及 edit-post-form 均改为调用 `BaseComponent.getArticle(this.articleId)`。article-comments-card 仍单独请求（带 page/per_page 的列表接口）。

---

## 4. 串行 await checkOwnership 再 loadData

**位置**：
- `subscriptions-list-card.js`：`await checkOwnership()` 后再 `loadSubscriptions()`
- `categories-card.js`：`await checkOwnership()` 后再 `loadData()`
- `friend-links-card.js`：`await checkOwnership()` 后再 `loadData()`

**问题**：与 09c3ccf 修复前的博客列表类似，首屏需等 project 请求完成再请求列表，总耗时 = 两次串行往返。

**建议**：将「所有权检查」与「列表数据加载」并行（例如 `Promise.all([checkOwnership(), loadData()])`），或先发起列表请求，再在后台做 checkOwnership，仅用于更新 UI（如显示/隐藏维护按钮），不阻塞首屏列表展示。

---

## 5. 搜索页

**位置**：`src/static/js/pages/search.js`

**现状**：已通过 `loadSearchParams()` 从 URL 读取 `q`、`type`、`sort`、`page` 并用于请求，无同类问题。

---

## 已实现修复汇总

- **留言列表**：`messages-list-card` 从 URL 读取 `page` 并用于首屏请求。
- **订阅列表**：`subscriptions-list-card` 中 checkOwnership 与 loadSubscriptions 并行执行；首屏从 URL 读取 `page` 并请求对应页。
- **分类卡片**：`categories-card` 中 checkOwnership 与 loadData 并行执行。
- **友链卡片**：`friend-links-card` 中 checkOwnership 与 loadData 并行执行。
- **博客页**：`BaseComponent.getProject(projectId)` 共享项目数据，blog-header、blog-posts-list-card、categories、blog-navigation、blog-profile、friend-links、subscriptions、manage-friend-links 等均改用该接口。
- **文章页**：`BaseComponent.getArticle(articleId)` 共享文章数据，article-header、article-content、comment-form、comment-settings、edit-post-form、blog-profile（文章页分支）等均改用该接口。
