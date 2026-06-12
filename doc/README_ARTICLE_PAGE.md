# 博客文章页面 (Article Page) 开发总结

## 概述

已成功创建博客文章页面，访问路径为：`http://blogn2.local/article/<article_id>`

## 功能特性

### 1. 页面结构
- **顶栏和底栏**: 使用现有的 `header-component` 和 `footer-component`
- **左边栏**: 与博客页面侧边栏一致，包含：
  - 用户头像和博客名称 (`blog-profile-card`)
  - 博客导航 (`blog-navigation-card`)
  - 最近评论 (`recent-comments-card`，作者名左侧 24px 内联头像)
  - 最近更新的博客 (`recent-updates-card`，博客名左侧 24px 内联头像)
  - 外站链接 (`friend-links-card`)

- **右边栏**: 文章主体内容，包含：
  - 文章头部信息 (`article-header-card`)
  - 文章内容 (`article-content-card`)
  - 评论区 (`article-comments-card`)
  - 评论表单 (`comment-form-card`)

### 2. 新增Web Components

#### article-header-card
- 显示文章标题、作者、发布时间、更新时间、博客名称、点击数、评论数
- 响应式布局，支持不同屏幕尺寸
- 自动从URL获取文章ID并加载数据
- **单列模式**：与博客页一致，当 `body` 带有 `layout-single-column` 时，工具栏按钮纵向排列；宿主通过 `BaseComponent._attachLayoutSingleColumnObserver()` 同步 `data-layout-single-column`，在 Shadow 中用 `:host([data-layout-single-column])` 控制样式

#### article-content-card
- 显示文章的完整内容
- **Markdown 渲染**：2026-03-28 及之后发表的文章使用 GFM Markdown；更早文章为纯文本 + 自动链接
- **数学公式**：通过本地 KaTeX 渲染行内（`$...$`、`\(...\)`）与块级（`$$...$$`、`\[...\]`）公式
- 自动检测并显示附件（图片或文件链接）
- 经 `HtmlUtils.sanitizeHtml` 过滤后再注入 KaTeX 输出，详见 [MARKDOWN_KATEX.md](MARKDOWN_KATEX.md)

#### article-comments-card
- 通过 `GET /api/articles/{article_id}/comments?page=&limit=` 加载评论（不重复请求文章正文）
- 每条评论含 `author_name`、`author_avatar`，无需再逐条请求 `/api/users/{id}`
- 支持分页；无评论时显示友好提示
- 可根据 URL hash（`#post{id}`）滚动到指定楼层

#### comment-form-card
- 评论输入表单
- 实时表单验证
- 提交状态管理
- 成功/错误消息提示
- 评论提交后自动刷新

### 3. 新增API端点

#### GET /api/articles/{article_id}
获取指定文章的详细信息，包括：
- 文章基本信息（标题、内容、附件）
- 作者信息
- 项目信息
- 分类信息
- 统计信息（点击数、评论数）

评论列表请使用下方独立接口，不包含在本响应中。

#### GET /api/articles/{article_id}/comments
获取指定文章的评论列表（分页），响应格式：

```json
{
  "comments": [
    {
      "id": 1,
      "content": "评论内容",
      "user_id": 1,
      "author_name": "用户名",
      "author_avatar": "/avatar/1/s_1.jpg",
      "post_time": "2024-01-01T12:00:00",
      "reply_count": 0
    }
  ],
  "pagination": {
    "current_page": 1,
    "per_page": 20,
    "total": 1,
    "total_pages": 1,
    "has_prev": false,
    "has_next": false
  },
  "comment_count": 1
}
```

查询参数：`page`（默认 1）、`limit`（默认 20）。

#### POST /api/articles/{article_id}/comments
为指定文章创建评论，包括：
- 评论内容
- 用户ID
- 自动更新文章评论数

## 技术实现

### 1. 路由配置
在 `src/main.py` 中添加了新的页面路由：
```python
@app.get("/article/{article_id}")
async def article_page(article_id: int):
    return FileResponse("src/static/article.html")
```

### 2. API控制器
文章相关 API 位于 `src/controllers/article.py`：
- `get_article_detail()`：获取文章详情
- `get_article_comments()`：获取评论列表（分页）
- `create_article_comment()`：创建评论

### 3. 数据库关系
- `user` 表和 `projectitem` 表：一对多关系 (user.id → projectitem.userid)
- `project` 表和 `projectitem` 表：一对多关系 (project.id → projectitem.projectid)
- `projectitem` 表和 `post` 表：一对多关系 (projectitem.id → post.projectitemid)

### 4. 组件复用
- 左边栏完全复用现有的web components
- 右边栏新增4个专用组件
- 所有组件都继承自 `BaseComponent`，共享基础功能

## 文件结构

```
src/
├── static/
│   ├── article.html                    # 文章页面HTML
│   └── js/components/
│       ├── article-header-card.js      # 文章头部组件
│       ├── article-content-card.js     # 文章内容组件
│       ├── article-comments-card.js    # 评论列表组件
│       └── comment-form-card.js        # 评论表单组件
├── controllers/
│   └── article.py                      # 文章与评论 API
└── main.py                             # 文章页面路由
```

## 使用方法

### 1. 访问文章页面
```
http://blogn2.local/article/123
```

### 2. 查看文章详情
```
GET /api/articles/123
```

### 3. 查看评论列表
```
GET /api/articles/123/comments?page=1&limit=20
```

### 4. 发表评论
```
POST /api/articles/123/comments
Content-Type: application/json

{
    "content": "这是一条评论",
    "user_id": 1
}
```

## 样式特点

- 响应式设计，支持不同屏幕尺寸
- 使用CSS变量系统，保持与现有页面风格一致
- 卡片式布局，清晰的信息层次
- 现代化的交互效果（悬停、过渡动画等）
- 统一的颜色方案和字体系统

## 后续优化建议

1. **用户认证**: 集成用户登录系统，获取真实用户ID
2. **评论回复**: 支持评论的回复功能
3. ~~**富文本编辑**~~: 已支持 Markdown 与 KaTeX 预览（发表/编辑页）；详见 [MARKDOWN_KATEX.md](MARKDOWN_KATEX.md)
4. **图片预览**: 支持图片的缩略图预览和放大查看
5. **分页加载**: 评论列表已通过 `/api/articles/{id}/comments` 分页实现
6. **实时更新**: 使用WebSocket实现评论的实时更新
7. **SEO优化**: 添加meta标签和结构化数据
8. **性能优化**: 实现评论的懒加载和虚拟滚动

## 测试状态

- ✅ 页面路由正常工作
- ✅ HTML页面正确加载
- ✅ 所有web components正确注册
- ✅ API端点正确响应
- ✅ 页面样式正确应用
- ✅ 现有组件在文章页面中正常工作
- ✅ 新组件正确获取文章ID

## 问题修复

### 组件兼容性问题
在开发过程中发现，现有的 web components（如 `blog-profile-card` 等）期望从 URL 中获取项目 ID（如 `/blog/123`），但文章页面的 URL 格式是 `/article/123`。

### 解决方案
1. **扩展BaseComponent**: 在基类中添加了统一的方法：
   - `getProjectId()`: 统一处理博客页面和文章页面的项目ID获取
   - `getArticleId()`: 获取文章ID
   - `isArticlePage()`: 检查当前是否在文章页面

2. **修改现有组件**: 所有现有组件都改为使用基类的统一方法，确保在两种页面中都能正常工作

3. **特殊处理逻辑**: 在`blog-profile-card`中添加了文章页面的特殊处理，当在文章页面时，会从文章ID获取项目ID

### 技术细节
- 现有组件通过`getProjectIdFromUrl()`方法获取项目ID
- 新组件通过`getArticleIdFromUrl()`方法获取文章ID
- 两种方法都使用基类的统一实现，确保代码的一致性和可维护性

博客文章页面已成功创建并可以正常访问！所有组件都能在文章页面中正常工作。
