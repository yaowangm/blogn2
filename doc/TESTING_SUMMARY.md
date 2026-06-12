# BlogN2 测试框架总结

## 📊 测试概览

### 测试统计（2026-06 更新）

运行 `python -m pytest --collect-only -q` 可得到当前数量；最近一次全量结果：

- **总测试数量**: 827
- **单元测试**: 677（`tests/unit/`）
- **集成测试**: 126（`tests/integration/`）
- **其他**: 22（`tests/test_*.py`、`tests/performance/`）
- **测试文件**: 82 个 `test_*.py`
- **通过率**: 100%（827/827）

覆盖率随代码增长而变化，请用 `python -m pytest --cov=src --cov-report=term-missing` 查看当前值；下文「99% / 622 行」为历史快照，不再维护。

### 测试框架配置
- **测试框架**: Pytest 7.4+
- **异步支持**: pytest-asyncio
- **代码覆盖率**: pytest-cov
- **超时控制**: pytest-timeout
- **数据库**: PostgreSQL（集成测试使用真实库或 test tracker 清理）

## 🏗️ 测试目录结构

```
tests/
├── conftest.py
├── test_article_page_features.py
├── test_bert_vectorization_basic.py
├── unit/                    # 单元测试（677）
├── integration/             # 集成测试（126）
└── performance/             # 性能相关测试
```

完整文件列表见 `tests/unit/`、`tests/integration/`；逐条用例索引见 [UNIT_TESTS_TABLE.md](UNIT_TESTS_TABLE.md)（部分条目可能滞后于新增测试文件）。

## 🎯 测试覆盖重点

### 后端
- Controllers、Services、Repositories
- 缓存键与装饰器（`tests/unit/test_cache.py`）
- 文章评论分页与 `{comments, pagination, comment_count}` 响应格式
- 留言本 JOIN 查询（`tests/unit/test_post_repository.py`）

### 前端（静态资源）
- Markdown / KaTeX 工具（`test_markdown_utils_js.py` 等）
- 部分组件行为（`test_components_enhanced.py`）

Web Components 运行时无独立 JS 测试框架；行为通过集成测试与手工验证补充。

## 🔧 运行测试

激活虚拟环境（见 `.cursor/rules/my-clues.mdc`）：

```bash
source ~/blogn2-env/bin/activate
cd /home/wy/blogn2

# 全量
python -m pytest -q

# 单元 / 集成
python -m pytest tests/unit/ -q
python -m pytest tests/integration/ -q

# 覆盖率
python -m pytest --cov=src --cov-report=html
```

## 📝 相关文档

- [UNIT_TESTS_TABLE.md](UNIT_TESTS_TABLE.md) — 部分历史用例索引
- [CONFIG_LOADING_TESTS.md](CONFIG_LOADING_TESTS.md)
- [REAL_DATABASE_TESTING_SUMMARY.md](REAL_DATABASE_TESTING_SUMMARY.md)

---

**最后更新**: 2026-06
