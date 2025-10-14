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
- 博客头部信息卡片
- 博客文章列表卡片

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
