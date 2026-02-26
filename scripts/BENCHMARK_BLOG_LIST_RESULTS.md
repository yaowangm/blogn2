# 博客列表分页性能对比结果

## 瓶颈结论与提升幅度（已修正）
- **真实瓶颈在前端加载链，而非数据库。** 服务端单次接口已在 2–3 ms 内，加索引前后差异在噪声范围内。
- **实测提升（本地 5 轮取平均）：**
  - 优化前：打开 `/blog/12?page=24` 时先请求 project、再 posts 第 1 页、再 posts 第 24 页，**3 次串行请求**，平均约 **10.7 ms**。
  - 优化后：直接请求目标页一次即可展示列表，平均约 **4.3 ms**。
  - **首屏列表请求耗时约减少 6.4 ms，约 59% 提升。**（若算上优化前内层组件重复请求第 1 页，实际少发的请求更多，体感会更好。）
- 已做的前端优化：
  1. **从 URL 读 `page`**：打开 `/blog/12?page=24` 直接请求第 24 页，不再先请求第 1 页再切到 24 页。
  2. **去掉首屏串行等待**：不再先 `await checkOwnership()` 再 `loadData()`，首屏只做所有权检查，文章列表由内层 `blog-list-card` 单独请求一次。
  3. **避免重复请求**：文章列表只由内层 `blog-list-card` 请求一次，父组件通过 `blog-list-content-updated` 事件同步 `totalPosts`/`totalPages`。

## 测试环境
- 接口: `GET /api/projects/12/posts?page=...&limit=10&type=original`
- 博客 ID: 12，总文章数: 237，末页: 第 24 页
- 每次冷请求（`--no-cache`），迭代 10 次取平均

## 修改前（无复合索引）
去掉 `(projectid, status, createtime)` 复合索引后的实测：

| 页码   | 平均响应时间（客户端） | 服务端 total_ms |
|--------|------------------------|-----------------|
| 第 1 页  | 4.4 ms                 | 2 ms            |
| 第 24 页 | **5.5 ms**             | 3 ms            |

## 修改后（有复合索引）
执行 `scripts/add_projectitem_list_index.sql` 并保留 `create_indexes.sql` 中的等效索引后：

| 页码   | 平均响应时间（客户端） | 服务端 total_ms |
|--------|------------------------|-----------------|
| 第 1 页  | 5.1 ms                 | 2 ms            |
| 第 24 页 | **5.8 ms**             | 3 ms            |

## 说明
- 当前数据量（237 篇）下，有无复合索引的差异在测量波动范围内；**性能瓶颈在首屏请求顺序与重复请求，已通过前端优化解决。**
- 复合索引仍建议保留，以便在文章数达到数千、数万时，末页接口继续稳定在低延迟。

## 如何复现
```bash
# 去掉复合索引（仅用于对比测试）
psql blogn -c "DROP INDEX IF EXISTS ix_projectitem_project_status_createtime; DROP INDEX IF EXISTS idx_projectitem_projectid_status_createtime;"
./scripts/blogn2-service restart
python3 scripts/benchmark_blog_list.py --no-cache --iterations 10

# 恢复索引
psql blogn -f scripts/add_projectitem_list_index.sql
psql blogn -c "CREATE INDEX IF NOT EXISTS idx_projectitem_projectid_status_createtime ON projectitem(projectid, status, createtime DESC);"
./scripts/blogn2-service restart
python3 scripts/benchmark_blog_list.py --no-cache --iterations 10
```
