# BlogN2 博客页面

## 访问路径
```
http://blogn2.local/blog/{project_id}
```

## 页面结构

### 左边栏
- 博客用户资料卡片
- 博客导航卡片  
- 分类列表卡片
- 最近评论卡片
- 最近更新卡片
- 外站链接卡片

### 右边栏
- 博客头部信息卡片（`blog-header-card`）
- 博客文章列表卡片

### 博客头部卡片（`blog-header-card`）

- **统计区**：文章 / 评论 / 访问 / 历史天数（自 `createtime` 起算），文案为「标签 + 粗体数字」同行；第四项为「历史」+ 数字 +「天」。
- **单列模式**（`body.layout-single-column`，由 `sidebar-collapse` 切换）：统计四项改为纵向单列；下方元信息区改为两行——第一行「创建于」「更新于」并排，第二行「修改博客信息」「订阅」并排。
- 宿主上的 `data-layout-single-column` 由 `BaseComponent._attachLayoutSingleColumnObserver()` 与 `body` 的 class 同步，Shadow 内用 `:host([data-layout-single-column])` 写响应式样式（避免依赖 `:host-context`）。

## Web Components
所有组件继承自BaseComponent，提供统一的元数据加载和错误处理。

## API端点
- `/api/projects/{project_id}` - 项目信息
- `/api/projects/{project_id}/posts` - 文章列表
- `/api/projects/{project_id}/comments/recent` - 最近评论
- `/api/projects/{project_id}/categories` - 分类列表
- `/api/projects/{project_id}/external-links` - 外站链接
- `/api/projects/{project_id}/rss` - RSS订阅

## 数据库关系
- user.projectid 对应 project.id (一对一)
- project.id 对应 projectitem.projectid (一对多)
- project.id 对应 post.projectid (一对多，通过projectitem关联)
