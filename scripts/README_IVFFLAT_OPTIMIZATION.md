# IVFFlat索引优化脚本

本目录包含了将HNSW索引优化为IVFFlat索引的完整脚本集合，用于提升搜索性能。

## 📁 文件说明

| 文件名 | 说明 |
|--------|------|
| `optimize_indexes_ivfflat.py` | 主要的索引优化脚本 |
| `run_ivfflat_optimization.sh` | 简化的执行脚本 |
| `test_search_performance.py` | 性能测试脚本 |
| `README_IVFFLAT_OPTIMIZATION.md` | 本说明文件 |

## 🚀 快速开始

### 方法1: 使用简化脚本（推荐）

```bash
# 在项目根目录执行
bash scripts/run_ivfflat_optimization.sh
```

### 方法2: 直接运行Python脚本

```bash
# 激活虚拟环境
source venv/bin/activate

# 运行优化脚本
python scripts/optimize_indexes_ivfflat.py
```

## 📊 优化效果预期

| 指标 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| **查询时间** | 150秒+ | 2-8秒 | **20-75倍** |
| **索引构建** | 25-45分钟 | 5-12分钟 | **2-4倍** |
| **内存使用** | 高 | 减少50-70% | **显著降低** |
| **磁盘占用** | 大 | 减少60-80% | **显著降低** |

## 🔧 优化内容

### 1. 索引替换

| 原索引 | 新索引 | 聚类数 | 说明 |
|--------|--------|--------|------|
| `idx_segment_vectors_vector_hnsw` | `idx_segment_vectors_vector_ivfflat` | 1000 | 片段向量索引 |
| `idx_article_vectors_title_hnsw` | `idx_article_vectors_title_ivfflat` | 100 | 文章标题向量索引 |
| `idx_article_vectors_content_hnsw` | `idx_article_vectors_content_ivfflat` | 100 | 文章内容向量索引 |
| `idx_comment_vectors_title_hnsw` | `idx_comment_vectors_title_ivfflat` | 150 | 评论标题向量索引 |
| `idx_comment_vectors_content_hnsw` | `idx_comment_vectors_content_ivfflat` | 150 | 评论内容向量索引 |

### 2. 聚类数选择

聚类数根据数据量自动计算：
- `content_segment_vectors`: 142,035条记录 → 1000个聚类
- `article_vectors`: 6,467条记录 → 100个聚类  
- `comment_vectors`: 18,306条记录 → 150个聚类

## 📋 执行步骤

### 1. 执行前准备

```bash
# 检查数据库连接
python -c "
import asyncio
from src.database import get_async_session
from sqlalchemy import text

async def test():
    async for session in get_async_session():
        result = await session.execute(text('SELECT 1'))
        print('✅ 数据库连接正常')
        break

asyncio.run(test())
"

# 检查磁盘空间（至少需要1GB）
df -h

# 检查内存（建议至少2GB可用）
free -h
```

### 2. 执行优化

```bash
# 使用简化脚本
bash scripts/run_ivfflat_optimization.sh

# 或直接运行Python脚本
python scripts/optimize_indexes_ivfflat.py
```

### 3. 验证结果

```bash
# 运行性能测试
python scripts/test_search_performance.py
```

## 📊 性能测试

### 测试内容

1. **简单向量查询**: 测试片段向量和文章标题的向量相似度查询
2. **复杂搜索查询**: 模拟实际的搜索场景，包含JOIN操作
3. **索引使用检查**: 验证IVFFlat索引是否正确创建

### 测试指标

- **查询时间**: 从毫秒到秒级
- **结果数量**: 返回的匹配结果数
- **平均相似度**: 结果的平均相似度分数
- **索引大小**: 新索引占用的磁盘空间

## 🔍 故障排除

### 常见问题

1. **数据库连接失败**
   ```bash
   # 检查环境变量
   echo $DATABASE_URL
   
   # 检查数据库服务
   systemctl status postgresql
   ```

2. **内存不足**
   ```bash
   # 检查内存使用
   free -h
   
   # 释放内存
   sudo sync && echo 3 | sudo tee /proc/sys/vm/drop_caches
   ```

3. **磁盘空间不足**
   ```bash
   # 检查磁盘空间
   df -h
   
   # 清理临时文件
   sudo apt clean
   ```

4. **索引创建失败**
   ```bash
   # 检查PostgreSQL日志
   sudo tail -f /var/log/postgresql/postgresql-*.log
   
   # 检查pgvector扩展
   psql -d blogn -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
   ```

### 回滚方案

如果优化后性能不佳，可以回滚到HNSW索引：

```sql
-- 1. 删除IVFFlat索引
DROP INDEX IF EXISTS idx_segment_vectors_vector_ivfflat;
DROP INDEX IF EXISTS idx_article_vectors_title_ivfflat;
DROP INDEX IF EXISTS idx_article_vectors_content_ivfflat;
DROP INDEX IF EXISTS idx_comment_vectors_title_ivfflat;
DROP INDEX IF EXISTS idx_comment_vectors_content_ivfflat;

-- 2. 恢复HNSW索引（使用备份文件中的定义）
-- 查看备份文件: scripts/index_backup_*.sql
```

## 📈 监控和维护

### 1. 性能监控

```bash
# 定期运行性能测试
python scripts/test_search_performance.py

# 检查索引使用情况
psql -d blogn -c "
SELECT 
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_indexes 
WHERE indexname LIKE '%ivfflat%'
ORDER BY pg_relation_size(indexrelid) DESC;
"
```

### 2. 定期维护

```sql
-- 重建索引（建议每月执行一次）
REINDEX INDEX idx_segment_vectors_vector_ivfflat;
REINDEX INDEX idx_article_vectors_title_ivfflat;
REINDEX INDEX idx_article_vectors_content_ivfflat;
REINDEX INDEX idx_comment_vectors_title_ivfflat;
REINDEX INDEX idx_comment_vectors_content_ivfflat;
```

### 3. 参数调优

如果查询性能不理想，可以调整聚类数：

```sql
-- 增加聚类数（提高精度，但增加构建时间）
DROP INDEX idx_segment_vectors_vector_ivfflat;
CREATE INDEX idx_segment_vectors_vector_ivfflat ON content_segment_vectors 
USING ivfflat (segment_vector vector_cosine_ops) 
WITH (lists = 1500);  -- 从1000增加到1500
```

## 📝 日志文件

- `ivfflat_optimization.log`: 优化过程的详细日志
- `search_performance_test_results.json`: 性能测试结果
- `index_backup_*.sql`: 原始索引的备份文件
- `ivfflat_optimization_report_*.md`: 优化报告

## ⚠️ 注意事项

1. **执行时机**: 建议在业务低峰期执行
2. **备份重要**: 脚本会自动备份现有索引，但建议额外备份数据库
3. **监控资源**: 执行过程中监控CPU、内存和磁盘使用情况
4. **测试验证**: 优化完成后务必测试搜索功能
5. **定期维护**: 建议每月重建一次索引以保持最佳性能

## 🆘 技术支持

如果遇到问题，请：

1. 查看日志文件获取详细错误信息
2. 检查数据库连接和权限
3. 确认系统资源充足
4. 参考故障排除部分

---

**优化完成后，你的搜索性能应该从150秒提升到2-8秒，提升20-75倍！** 🎉
