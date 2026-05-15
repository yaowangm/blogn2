# 分享与爬虫预览（Open Graph）

## 目的

微信、Slack、Telegram 等客户端在展开链接时往往**不执行 JavaScript**，只抓取首包 HTML。本站对若干页面在服务端读出静态模板后，注入 **Open Graph**（`og:title`、`og:description`、`og:url`、`og:image` 等）及站点 favicon 的绝对地址，使预览卡片正常；普通浏览器仍使用同一套 HTML，由前端 SPA 接管交互。

## 代码入口

| 模块 | 职责 |
|------|------|
| `src/utils/share_preview.py` | 判断爬虫 UA（`is_share_preview_crawler`，可用于其它逻辑）、根据请求头推断公网前缀（`get_request_public_base_url`）、与配置中的 `BASE_URL` 合并（`merge_public_base_with_config`）、把 meta 写入 HTML 字符串（`inject_article_share_preview` 等） |
| `src/utils/page_handlers.py` | `PageHandler._maybe_share_preview_html`：对博客首页、文章详情、留言主题等路由读取模板、拉取分享元数据、调用 `inject_*` 并返回 `HTMLResponse` |
| `src/config/app.py` | `get_base_url()` 读取环境变量 `BASE_URL`（默认 `http://localhost:8000`） |

`og:image` 使用站内 PNG：`/static/images/site-share-icon.png`（常量 `SITE_OG_IMAGE_PATH`）。注入时使用**绝对 URL**（`public_base_url + 路径`），避免相对路径被部分爬虫忽略。

## `BASE_URL` 与反向代理

- **配置**：生产环境应将 `BASE_URL` 设为对外 HTTPS 根地址（与浏览器用户看到的域名一致）。
- **合并规则**：`merge_public_base_with_config` 将 `get_request_public_base_url`（优先 `X-Forwarded-Proto` / `X-Forwarded-Host`）与 `get_base_url()` 合并；当推断结果为 `http` 而配置主机名一致时，可抬升为 `https`（避免反代未传准 `X-Forwarded-Proto` 时 og 链接降级）。细节见 `share_preview.py` 内文档字符串。
- **Docker**：若编排层已注入旧的 `BASE_URL=http...`，`load_dotenv(..., override=False)` 可能阻止配置文件里的 HTTPS 进入进程环境。`docker/docker-entrypoint.sh` 会用 `dotenv_values` 从配置文件再次 `export BASE_URL`，与 `get_base_url()` 文档说明一致。

## 单元测试

- `tests/unit/test_share_preview.py`：`merge_public_base_with_config`、注入 HTML、UA 识别等。
- `tests/unit/test_page_handlers_share_preview.py`：页面处理器与分享元数据加载的集成行为。

## 相关文档

- 根 `README.md` 环境变量中的 `BASE_URL` 说明。
- 密码重置邮件中的绝对链接：`doc/EMAIL_PASSWORD_RESET_DESIGN.md`（同样依赖 `BASE_URL`）。
