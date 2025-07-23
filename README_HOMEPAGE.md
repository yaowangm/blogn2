# BlogN2 首页使用说明

## 概述

BlogN2首页已经成功创建并部署，可以通过 `http://localhost:8000/` 或 `http://blogn2.local/` 访问。

## 技术栈

- **前端**: HTML5, CSS3, Web Components (原生JavaScript)
- **后端**: FastAPI (Python)
- **设计**: 响应式设计，支持桌面和移动设备
- **字体**: Inter (Google Fonts)

## 页面结构

### 公有元素
1. **顶栏 (Header)**
   - 左侧：网站Logo和名称 "BlogN2"
   - 右侧：用户操作区域
     - 未登录：搜索按钮 + 登录按钮
     - 已登录：用户头像 + 用户名 + 我的首页 + 搜索按钮 + 退出按钮

2. **底栏 (Footer)**
   - 网站Logo和名称
   - 版权声明

### 主要内容区域
采用两栏布局设计：

#### 左边栏 (占三分之一宽)
1. **网站统计卡片** - 显示用户数量和博文总数
2. **全站导航卡片** - 用户列表、RSS链接、分类浏览、标签云
3. **最新加入博客列表** - 显示最近注册的博客
4. **最热门博客列表** - 显示关注者最多的博客
5. **最近评论列表** - 显示最新的评论内容
6. **友情链接** - 外部网站链接

#### 右边栏
1. **网站介绍卡片** - 关于BlogN2的详细介绍
2. **最近留言卡片** - 用户留言内容
3. **最新博文摘要列表** - 包含标题、作者、发布日期、摘要和特色图片

## Web Components

页面使用Web Components实现模块化设计，每个功能区域都是独立的组件：

- `header-component` - 顶栏组件
- `footer-component` - 底栏组件
- `stats-card` - 统计卡片
- `navigation-card` - 导航卡片
- `recent-blogs-card` - 最新博客列表
- `popular-blogs-card` - 热门博客列表
- `recent-comments-card` - 最近评论列表
- `friend-links-card` - 友情链接
- `about-card` - 关于卡片
- `recent-messages-card` - 最近留言
- `latest-posts-card` - 最新博文列表

## 设计特点

### 可用性与创造力平衡
- 简洁的界面设计
- 清晰的信息层次
- 直观的导航结构

### 一致性
- 统一的颜色方案 (蓝色主题)
- 一致的字体 (Inter)
- 统一的卡片设计风格

### 响应式设计
- 桌面优先设计
- 移动设备适配
- 灵活的网格布局

### 无障碍性
- 遵循WCAG标准
- 高对比度颜色
- 键盘导航支持
- 语义化HTML结构

### 性能优化
- CSS变量系统
- 优化的字体加载
- 合理的组件结构

## 文件结构

```
src/
├── static/
│   ├── index.html              # 主页面
│   ├── css/
│   │   ├── main.css            # 主要样式
│   │   └── components.css      # 组件样式
│   └── js/
│       └── components/         # Web Components
│           ├── header-component.js
│           ├── footer-component.js
│           ├── stats-card.js
│           ├── navigation-card.js
│           ├── recent-blogs-card.js
│           ├── popular-blogs-card.js
│           ├── recent-comments-card.js
│           ├── friend-links-card.js
│           ├── about-card.js
│           ├── recent-messages-card.js
│           └── latest-posts-card.js
└── main.py                     # FastAPI应用
```

## 启动应用

1. 激活虚拟环境：
   ```bash
   source venv/bin/activate
   ```

2. 启动应用：
   ```bash
   python src/main.py
   ```

3. 访问首页：
   - 本地访问：http://localhost:8000/
   - 域名访问：http://blogn2.local/ (需要配置hosts文件)

## 当前状态

- ✅ 静态页面已创建
- ✅ Web Components已实现
- ✅ 响应式设计已完成
- ✅ FastAPI集成已完成
- ✅ 静态文件服务已配置
- ⏳ 数据库集成 (待实现)
- ⏳ 动态内容生成 (待实现)

## 下一步计划

1. 集成数据库连接
2. 实现动态内容加载
3. 添加用户认证系统
4. 实现搜索功能
5. 添加更多交互功能

## 注意事项

- 当前页面使用静态示例数据
- 所有链接都是示例链接，实际功能待实现
- 用户登录状态是模拟的，实际需要后端支持
- 建议在Chrome、Firefox、Safari等现代浏览器中访问以获得最佳体验 