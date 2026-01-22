# 搜索功能 NaN 值修复

## 问题描述

搜索某些关键词时，前端显示"搜索失败，请稍后重试"，后端日志报错：

```
ValueError: Out of range float values are not JSON compliant: nan
```

## 根本原因

在向量相似度计算过程中，当出现以下情况时可能产生 NaN（Not a Number）值：

1. **向量计算异常**：零向量、空向量或向量计算错误
2. **数据库查询结果**：PostgreSQL 的向量距离计算在某些边界情况下可能返回 NaN
3. **相似度分数**：`relevance_score` 可能包含 NaN 值
4. **动态阈值**：`dynamic_threshold` 计算可能产生 NaN

JSON 标准不支持 NaN 和 Infinity 值，导致序列化失败。

## 修复内容

### 1. 格式化结果函数中添加 NaN 检查

在以下三个格式化函数中添加了 NaN 和 Infinity 检查：

- `_format_article_result()` - 文章搜索结果格式化
- `_format_hybrid_article_result()` - 混合搜索文章结果格式化
- `_format_comment_result()` - 评论搜索结果格式化

**修复逻辑**：
```python
# 安全地处理 relevance_score，避免 NaN 值
relevance_score = 0.0
if item[5] is not None:
    try:
        score = float(item[5])
        # 检查是否为 NaN 或 Infinity
        if not (np.isnan(score) or np.isinf(score)):
            relevance_score = score
    except (ValueError, TypeError):
        relevance_score = 0.0
```

### 2. 动态阈值处理

在 `search()` 方法中添加了 `dynamic_threshold` 的 NaN 检查：

```python
# 安全地处理 dynamic_threshold，避免 NaN 值
dynamic_threshold = results.get("dynamic_threshold", 0.45)
if dynamic_threshold is not None:
    try:
        threshold = float(dynamic_threshold)
        if np.isnan(threshold) or np.isinf(threshold):
            dynamic_threshold = 0.45
        else:
            dynamic_threshold = threshold
    except (ValueError, TypeError):
        dynamic_threshold = 0.45
```

### 3. 阈值计算方法增强

在 `calculate_dynamic_threshold()` 方法中添加了额外的 NaN 检查：

```python
# 确保阈值在合理范围内，并检查 NaN
threshold = max(0.1, min(0.9, dynamic_threshold))
# 额外检查 NaN 和 Infinity
if np.isnan(threshold) or np.isinf(threshold):
    return 0.45  # 返回默认值
return threshold
```

### 4. 向量转换方法增强

在 `_vector_to_json()` 方法中添加了 NaN 检查：

```python
# 检查并替换 NaN 和 Infinity 值
if np.any(np.isnan(vector)) or np.any(np.isinf(vector)):
    # 如果向量包含 NaN 或 Infinity，替换为零向量
    vector = np.nan_to_num(vector, nan=0.0, posinf=0.0, neginf=0.0)
return json.dumps(vector.tolist())
```

## 修复效果

修复后，即使向量计算产生 NaN 值，系统也会：

1. **自动处理**：将 NaN 值替换为安全的默认值（0.0 或 0.45）
2. **正常返回**：搜索结果可以正常序列化为 JSON
3. **用户体验**：用户不会看到错误提示，搜索功能正常工作

## 测试建议

1. **测试边界情况**：
   - 搜索空字符串
   - 搜索特殊字符
   - 搜索非常长的查询

2. **验证修复**：
   - 检查日志中不再出现 NaN 相关错误
   - 搜索功能正常返回结果
   - JSON 响应格式正确

## 相关文件

- `src/services/search_service.py` - 搜索服务（已修复）
