# Markdown 与数学公式（KaTeX）

BlogN2 文章正文与编辑器预览使用 **marked** 解析 GitHub 风格 Markdown，并使用本地部署的 **KaTeX** 渲染数学公式与化学式。

所有相关脚本与字体均存放在 `src/static/js/libs/`，页面通过 `/static/...` 引用，**不依赖外网 CDN**。

## 适用页面

| 页面 | 路径 |
|------|------|
| 文章阅读 | `/article/{id}` |
| 发表文章 | `/create-post` |
| 编辑文章 | `/edit-article` |

2026-03-28 及之后发表的文章按 Markdown 渲染；更早文章仍为纯文本 + 自动链接。

## 支持的 Markdown 能力

由 **marked**（GFM）提供：

- 标题、段落、换行
- **粗体**、*斜体*、~~删除线~~
- 有序/无序列表、任务列表（`- [ ]` / `- [x]`）
- 引用、分隔线
- 围栏代码块与行内代码
- 表格
- 链接与图片

## 数学与化学公式（KaTeX）

在 marked 解析前，公式会从正文中抽出；解析完成后再由 KaTeX 渲染，避免与 Markdown 语法冲突。

### 行内公式

```markdown
爱因斯坦质能方程 $E=mc^2$ 在物理学中非常重要。
亦可用 \(...\)：\(a^2 + b^2 = c^2\)
```

### 块级公式

```markdown
$$
\int_{-\infty}^{\infty} e^{-x^2}\,dx = \sqrt{\pi}
$$

或：

\[
\sum_{n=1}^{\infty} \frac{1}{n^2} = \frac{\pi^2}{6}
\]
```

### 化学式（mhchem 扩展）

需使用数学定界符包裹，例如：

```markdown
水的化学式 $ \ce{H2O} $，反应式：

$$
\ce{2H2 + O2 -> 2H2O}
$$
```

### 注意事项

- 代码块与行内代码 **不会** 解析其中的 `$` 或 `\ce{}`。
- 公式语法错误时显示原文（`math-fallback`），不阻断整篇文章渲染。
- 摘要列表等场景会剥离公式标记，见 `HtmlUtils.stripMarkdown()`。
- 公式在 `marked` 转 HTML 并消毒 **之后** 才由 KaTeX 渲染，避免安全过滤破坏公式内部结构。
- 文章页使用 Shadow DOM 时，通过 `MarkdownUtils.ensureKatexStyles()` 注入本地 `katex.min.css`（不用 `@import`，以确保字体路径正确）。

## 本地资源路径

```
src/static/js/libs/
├── marked.min.js
└── katex/
    ├── LICENSE
    ├── katex.min.js
    ├── katex.min.css
    ├── mhchem.min.js
    └── fonts/          # KaTeX 字体（woff2 等）
```

页面加载顺序（节选）：

1. `katex.min.js`
2. `mhchem.min.js`（注册化学式宏）
3. `marked.min.js`
4. `html-utils.js`
5. `markdown-utils.js`

统一解析入口：`MarkdownUtils.parseMarkdown(source)`（`src/static/js/utils/markdown-utils.js`）。

## 第三方版权与许可

### KaTeX

- 项目：https://katex.org/
- 源码：https://github.com/KaTeX/KaTeX
- 版本：0.16.11（与 `src/static/js/libs/katex/` 中文件一致）
- 许可：**MIT License**
- 完整许可正文：`src/static/js/libs/katex/LICENSE`

```
Copyright (c) 2013-2020 Khan Academy and other contributors
```

KaTeX 使用的字体亦受其各自许可约束，详见 KaTeX 仓库中的 `fonts/` 说明。

### mhchem（KaTeX contrib）

- 用于 `\ce{}`、`\pu{}` 等化学式语法
- 随 KaTeX 发行版 `contrib/mhchem` 一并分发
- 许可：与 KaTeX 相同（MIT），详见 KaTeX 官方文档

### marked

- 项目：https://marked.js.org/
- 文件：`src/static/js/libs/marked.min.js`（v9.1.6）
- 许可：**MIT License**（文件头部注释含版权与仓库链接）

```
Copyright (c) 2018+, MarkedJS (https://github.com/markedjs/marked)
```

## 相关代码

| 模块 | 说明 |
|------|------|
| `markdown-utils.js` | marked + KaTeX 编排 |
| `article-content-card.js` | 文章页正文渲染 |
| `create-post-form.js` / `edit-post-form.js` | 编辑器预览 |
| `components.css` | `.markdown-content` 与公式展示样式 |
