# 搜索阈值过滤修复

## 问题描述

当搜索某些关键词（如"书本"）时，虽然阈值设置为50%，但是会搜出来很多相似度为0的帖子。

## 根本原因

在混合搜索的SQL查询中，虽然对片段相似度进行了阈值过滤，但在计算最终的 `relevance_score`（混合相似度）时存在问题：

1. **混合相似度计算问题**：
   - 混合相似度 = 10%文章级相似度 + 90%片段级相似度
   - 如果 `article_similarity` 为 NULL（LEFT JOIN 没有匹配），使用 `COALESCE(art.article_similarity, 0)` 会变成 0
   - 即使片段相似度刚好达到阈值（如0.5），如果文章级相似度为0，最终结果可能低于阈值

2. **缺少最终结果过滤**：
   - SQL查询中只对片段相似度进行了过滤
   - 没有对最终计算出的 `relevance_score` 进行阈值过滤
   - 导致一些混合后相似度低于阈值的结果被返回

## 修复内容

### 1. 修复混合相似度计算逻辑

**修改前**：
```sql
(COALESCE(art.article_similarity, 0) * 0.1 + 
 bs.segment_similarity * 0.9) as relevance_score
```

**修改后**：
```sql
(COALESCE(art.article_similarity, bs.segment_similarity) * 0.1 + 
 bs.segment_similarity * 0.9) as relevance_score
```

**改进**：如果 `article_similarity` 为 NULL，使用 `segment_similarity` 而不是 0，确保混合相似度不会因为文章级相似度缺失而降低。

### 2. 添加最终结果阈值过滤

在SQL查询中添加了 `final_results` CTE，并在最终SELECT中添加了阈值过滤：

```sql
final_results AS (
    SELECT 
        ...
        (COALESCE(art.article_similarity, bs.segment_similarity) * 0.1 + 
         bs.segment_similarity * 0.9) as relevance_score,
        ...
    FROM best_segments bs
    ...
)
SELECT 
    id, title, content, author, createtime,
    relevance_score, best_match_text, match_type
FROM final_results
WHERE relevance_score >= {adjusted_threshold}  -- 添加阈值过滤
ORDER BY relevance_score DESC
```

### 3. 在格式化结果时添加额外检查

在 `hybrid_search_articles()` 和 `_search_articles()` 方法中，格式化结果后再次过滤：

```python
# 格式化结果并过滤掉相似度为0或小于阈值的结果
formatted_items = []
for item in items:
    formatted = self._format_hybrid_article_result(item)
    # 过滤掉相似度为0或小于阈值的结果
    if formatted.get("relevance_score", 0) > 0 and formatted.get("relevance_score", 0) >= adjusted_threshold:
        formatted_items.append(formatted)
```

### 4. 修复计数查询

在计数查询中也添加了相同的 `final_results` CTE 和阈值过滤，确保总数统计准确：

```sql
final_results AS (
    SELECT 
        bs.projectitem_id,
        (COALESCE(art.article_similarity, bs.segment_similarity) * 0.1 + 
         bs.segment_similarity * 0.9) as relevance_score
    FROM best_segments bs
    LEFT JOIN article_scores art ON bs.projectitem_id = art.projectitem_id
)
SELECT COUNT(DISTINCT projectitem_id)
FROM final_results
WHERE relevance_score >= {adjusted_threshold}  -- 添加阈值过滤
```

## 修复效果

修复后：

1. **准确的阈值过滤**：所有返回的结果的 `relevance_score` 都大于等于设定的阈值
2. **不会返回相似度为0的结果**：在SQL层面和格式化层面都进行了过滤
3. **更准确的计数**：总数统计也考虑了最终相似度阈值
4. **更好的混合相似度计算**：当文章级相似度缺失时，使用片段相似度作为默认值，而不是0

## 测试建议

1. **测试阈值过滤**：
   - 搜索"书本"等关键词
   - 检查返回结果的 `relevance_score` 是否都大于等于阈值
   - 确认没有相似度为0的结果

2. **测试边界情况**：
   - 搜索非常短的关键词（阈值会提高）
   - 搜索非常长的关键词（阈值会降低）
   - 验证阈值调整是否正常工作

3. **验证计数准确性**：
   - 检查返回的总数是否与实际结果数量一致
   - 验证分页是否正确

## 相关文件

- `src/services/search_service.py` - 搜索服务（已修复）
