# 博客列表分页性能对比结果

## 本次修改包含哪些部分

- **前端**：从 URL 读 `page`、首屏只发一次文章列表请求、用事件同步分页总数。
- **缓存**：项目文章列表缓存键增加 `folderid`。
- **数据库**：在 `projectitem` 上增加复合索引 `(projectid, status, createtime)`（见 `src/models/project_item.py` 的 `__table_args__` 与 `scripts/add_projectitem_list_index.sql`，需在库上执行该 SQL 才生效）。

---

## 瓶颈结论：在前端，不在数据库

- 单次接口 `GET /api/projects/12/posts?page=24` 在有、无复合索引时，耗时都在约 5–6 ms，差异在测量噪声内（见下节「有无复合索引」对比）。
- 因此**真实瓶颈在首屏的请求次数与顺序**，已通过前端优化（少发请求、直接请求目标页）解决。

**数据库索引的意义**：当前体感上的提升来自前端优化；数据库加索引**不解决**当前体感到的“慢”。索引建议保留，用于数据量增大后（如数千、数万篇）保持末页接口延迟稳定，避免大 offset 分页变慢。

---

## 提升幅度（来自前端优化）

对比的是「为展示列表而发出的请求」总耗时，不是单次接口有无索引：

| 场景 | 行为 | 平均耗时（5 轮） |
|------|------|------------------|
| **优化前** | 串行 3 次：project → posts 第 1 页 → posts 第 24 页 | **约 10.7 ms** |
| **优化后** | 只请求 posts 第 24 页 1 次即可展示列表 | **约 4.3 ms** |

**首屏列表相关请求约减少 6.4 ms，约 59% 提升。** 该提升来自减少请求次数与直接请求目标页，与是否加复合索引无关。

---

## 有无复合索引（单次接口对比）

下面是在「单次请求 `/api/projects/12/posts?page=...`」的前提下，有、无复合索引的对比，用来说明**加索引对单次接口影响很小**，故瓶颈不在数据库。

**无复合索引时**（已去掉 `ix_projectitem_project_status_createtime` 与 `idx_projectitem_projectid_status_createtime`）：

| 页码   | 平均响应时间（客户端） |
|--------|------------------------|
| 第 1 页  | 4.4 ms                 |
| 第 24 页 | 5.5 ms                 |

**有复合索引时**（执行 `scripts/add_projectitem_list_index.sql` 且保留 `create_indexes.sql` 中的等效索引）：

| 页码   | 平均响应时间（客户端） |
|--------|------------------------|
| 第 1 页  | 5.1 ms                 |
| 第 24 页 | 5.8 ms                 |

结论：当前数据量（237 篇）下，有无索引差异在波动范围内；复合索引仍建议保留，以便文章数达到数千、数万时末页接口保持稳定。

---

## 测试环境与复现

- 接口：`GET /api/projects/12/posts?page=...&limit=10&type=original`
- 博客 ID：12，总文章数：237，末页：第 24 页
- 测速脚本：`python3 scripts/benchmark_blog_list.py --no-cache --iterations 10`

**复现「有无复合索引」单次接口对比：**

```bash
# 去掉复合索引
psql blogn -c "DROP INDEX IF EXISTS ix_projectitem_project_status_createtime; DROP INDEX IF EXISTS idx_projectitem_projectid_status_createtime;"
./scripts/blogn2-service restart
python3 scripts/benchmark_blog_list.py --no-cache --iterations 10

# 恢复索引
psql blogn -f scripts/add_projectitem_list_index.sql
psql blogn -c "CREATE INDEX IF NOT EXISTS idx_projectitem_projectid_status_createtime ON projectitem(projectid, status, createtime DESC);"
./scripts/blogn2-service restart
python3 scripts/benchmark_blog_list.py --no-cache --iterations 10
```
