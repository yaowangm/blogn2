# BERT全文检索技术方案

## 项目概述

本文档详细描述了基于BERT和pgvector的全文检索系统技术方案，用于在BlogN2博客系统中实现智能语义搜索功能。

## 1. 技术架构

### 1.1 整体架构
```
用户查询 → 查询向量化 → 向量检索 → 结果排序 → 返回结果
    ↓
BERT模型 → pgvector → PostgreSQL → 混合搜索
```

### 1.2 核心组件
- **BERT模型**: `google-bert-base-chinese` (768维向量)
- **向量数据库**: PostgreSQL + pgvector扩展
- **文本处理**: 滑动窗口 + 向量聚合
- **搜索策略**: 分层检索（文章级 + 片段级）

## 2. 数据库设计

### 2.1 表结构设计

#### 2.1.1 主向量表 (article_vectors)
```sql
CREATE TABLE article_vectors (
    id SERIAL PRIMARY KEY,
    projectitem_id INTEGER UNIQUE REFERENCES projectitem(id),
    
    -- 标题向量（直接存储）
    title_vector VECTOR(768),
    title_text TEXT,
    
    -- 内容向量（聚合后的最终向量）
    content_vector VECTOR(768),
    content_text TEXT,
    
    -- 多片段元数据
    segment_count INTEGER DEFAULT 1,
    vectorization_method VARCHAR(50) DEFAULT 'direct',
    total_text_length INTEGER,
    max_segment_length INTEGER,
    
    -- 聚合策略参数
    aggregation_weights JSONB,
    overlap_strategy VARCHAR(20) DEFAULT 'sliding_window',
    window_size INTEGER DEFAULT 400,
    step_size INTEGER DEFAULT 200,
    
    -- 质量指标
    avg_confidence FLOAT DEFAULT 1.0,
    key_segment_ratio FLOAT DEFAULT 0.0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建向量索引
CREATE INDEX ON article_vectors USING hnsw (title_vector vector_cosine_ops);
CREATE INDEX ON article_vectors USING hnsw (content_vector vector_cosine_ops);
```

#### 2.1.2 片段向量表 (content_segment_vectors)
```sql
CREATE TABLE content_segment_vectors (
    id SERIAL PRIMARY KEY,
    article_vector_id INTEGER REFERENCES article_vectors(id) ON DELETE CASCADE,
    
    -- 片段标识
    segment_index INTEGER NOT NULL,
    segment_hash VARCHAR(64),
    
    -- 片段内容
    segment_text TEXT,
    segment_vector VECTOR(768),
    
    -- 片段统计
    segment_length INTEGER,
    token_count INTEGER,
    word_count INTEGER,
    
    -- 位置信息
    start_char_pos INTEGER,
    end_char_pos INTEGER,
    start_token_pos INTEGER,
    end_token_pos INTEGER,
    
    -- 重叠信息
    prev_overlap_chars INTEGER DEFAULT 0,
    next_overlap_chars INTEGER DEFAULT 0,
    overlap_ratio FLOAT DEFAULT 0.0,
    
    -- 片段质量
    confidence_score FLOAT DEFAULT 1.0,
    semantic_density FLOAT,
    keyword_density FLOAT,
    is_key_segment BOOLEAN DEFAULT FALSE,
    
    -- 片段类型
    segment_type VARCHAR(20) DEFAULT 'body',
    contains_title BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(article_vector_id, segment_index)
);

-- 创建片段向量索引
CREATE INDEX ON content_segment_vectors USING hnsw (segment_vector vector_cosine_ops);
CREATE INDEX ON content_segment_vectors (article_vector_id, segment_index);
```

#### 2.1.3 评论向量表 (comment_vectors)
```sql
CREATE TABLE comment_vectors (
    id SERIAL PRIMARY KEY,
    post_id INTEGER UNIQUE REFERENCES post(id),
    
    -- 评论向量
    title_vector VECTOR(768),
    content_vector VECTOR(768),
    title_text TEXT,
    content_text TEXT,
    
    -- 元数据
    segment_count INTEGER DEFAULT 1,
    vectorization_method VARCHAR(50),
    total_text_length INTEGER,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建评论向量索引
CREATE INDEX ON comment_vectors USING hnsw (title_vector vector_cosine_ops);
CREATE INDEX ON comment_vectors USING hnsw (content_vector vector_cosine_ops);
```

### 2.2 关系设计
- `article_vectors` ←→ `content_segment_vectors` (一对多)
- `article_vectors` ←→ `projectitem` (一对一)
- `comment_vectors` ←→ `post` (一对一)

## 3. 文本处理策略

### 3.1 长文本处理方案

#### 3.1.1 滑动窗口策略
```python
class SlidingWindowProcessor:
    def __init__(self):
        self.max_tokens = 512
        self.window_size = 400
        self.step_size = 200
        self.overlap_ratio = 0.5
    
    def split_text(self, text: str) -> List[Dict]:
        """使用滑动窗口分割长文本"""
        segments = []
        sentences = self.split_by_sentences(text)
        
        current_segment = ""
        current_length = 0
        
        for sentence in sentences:
            if current_length + len(sentence) > self.window_size:
                if current_segment:
                    segments.append({
                        'text': current_segment.strip(),
                        'length': len(current_segment),
                        'start_pos': len(segments) * self.step_size,
                        'end_pos': len(segments) * self.step_size + len(current_segment)
                    })
                current_segment = sentence
                current_length = len(sentence)
            else:
                current_segment += sentence
                current_length += len(sentence)
        
        return segments
```

#### 3.1.2 向量聚合策略
```python
class VectorAggregator:
    def aggregate_vectors(self, segments: List[Dict]) -> np.ndarray:
        """聚合多个片段向量"""
        vectors = [seg['vector'] for seg in segments]
        weights = self.compute_weights(segments)
        
        # 加权平均聚合
        return np.average(vectors, axis=0, weights=weights)
    
    def compute_weights(self, segments: List[Dict]) -> List[float]:
        """计算片段权重"""
        weights = []
        for i, seg in enumerate(segments):
            weight = (
                seg['confidence_score'] * 0.3 +
                seg['semantic_density'] * 0.25 +
                seg['keyword_density'] * 0.2 +
                (1.2 if seg['is_key_segment'] else 1.0) * 0.15 +
                self.position_weight(i, len(segments)) * 0.1
            )
            weights.append(weight)
        
        return np.array(weights) / np.sum(weights)
```

### 3.2 文本预处理
```python
class TextPreprocessor:
    def preprocess(self, text: str) -> str:
        """文本预处理"""
        # 1. 清理HTML标签
        text = self.clean_html(text)
        
        # 2. 处理特殊字符
        text = self.normalize_text(text)
        
        # 3. 长度限制
        text = text[:128000]  # 128K字符限制
        
        return text
    
    def clean_html(self, text: str) -> str:
        """清理HTML标签"""
        import re
        return re.sub(r'<[^>]+>', '', text)
    
    def normalize_text(self, text: str) -> str:
        """文本标准化"""
        # 统一换行符
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        # 清理多余空白
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
```

## 4. 向量化服务

### 4.1 BERT向量化服务
```python
class BERTVectorizationService:
    def __init__(self):
        self.model_name = "google-bert-base-chinese"
        self.model = None
        self.tokenizer = None
        self.device = "cpu"  # 无GPU环境
    
    async def load_model(self):
        """加载BERT模型"""
        from transformers import BertModel, BertTokenizer
        
        self.tokenizer = BertTokenizer.from_pretrained(self.model_name)
        self.model = BertModel.from_pretrained(self.model_name)
        self.model.eval()
    
    async def vectorize_text(self, text: str) -> np.ndarray:
        """向量化文本"""
        if not self.model:
            await self.load_model()
        
        # 文本预处理
        text = self.preprocess_text(text)
        
        # 分词和编码
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            max_length=512,
            truncation=True,
            padding=True
        )
        
        # 生成向量
        with torch.no_grad():
            outputs = self.model(**inputs)
            # 使用[CLS] token的向量
            vector = outputs.last_hidden_state[:, 0, :].numpy()
        
        return vector[0]  # 返回768维向量
```

### 4.2 批量处理服务
```python
class BatchVectorizationService:
    def __init__(self, vectorization_service: BERTVectorizationService):
        self.vectorization_service = vectorization_service
        self.batch_size = 32
    
    async def vectorize_articles(self, article_ids: List[int]):
        """批量向量化文章"""
        articles = await self.get_articles(article_ids)
        
        # 分批处理
        for i in range(0, len(articles), self.batch_size):
            batch = articles[i:i + self.batch_size]
            await self.process_batch(batch)
    
    async def process_batch(self, articles: List[Dict]):
        """处理一批文章"""
        tasks = []
        for article in articles:
            task = self.vectorize_single_article(article)
            tasks.append(task)
        
        # 并行处理
        await asyncio.gather(*tasks)
```

## 5. 搜索服务

### 5.1 分层搜索策略

#### 5.1.1 相似度计算策略
在基于BERT的全文检索中，我们采用**最大段相似度**策略而非段相似度之和，原因如下：

1. **语义匹配的准确性**: 最大段相似度能够准确识别文档中最相关的片段，避免不相关片段对整体相似度的干扰
2. **避免长度偏差**: 段相似度之和会导致长文档在搜索中具有不公平的优势，即使其相关性较低
3. **提高搜索精度**: 最大段相似度更符合用户期望，即找到包含最相关内容片段的文档
4. **计算效率**: 使用`MIN()`函数和窗口函数可以高效地找到最佳匹配片段

```python
class HierarchicalSearchService:
    def __init__(self, db_session):
        self.db = db_session
    
    async def search(self, query: str, limit: int = 10) -> List[Dict]:
        """分层搜索"""
        # 1. 查询向量化
        query_vector = await self.vectorize_query(query)
        
        # 2. 快速筛选（基于内容向量）
        candidates = await self.fast_search(query_vector, limit=50)
        
        # 3. 精确匹配（基于片段向量）
        detailed_results = await self.detailed_search(candidates, query_vector)
        
        # 4. 结果排序
        return self.rank_results(detailed_results, limit)
    
    async def fast_search(self, query_vector: np.ndarray, limit: int) -> List[Dict]:
        """快速搜索（基于聚合向量）"""
        query = """
        SELECT 
            av.projectitem_id,
            av.title_text,
            av.content_text,
            (av.title_vector <=> %s) * 0.3 + (av.content_vector <=> %s) * 0.7 AS distance
        FROM article_vectors av
        WHERE av.avg_confidence > 0.7
        ORDER BY distance
        LIMIT %s
        """
        
        result = await self.db.execute(query, [
            self.vector_to_json(query_vector),
            self.vector_to_json(query_vector),
            limit
        ])
        
        return result.fetchall()
    
    async def detailed_search(self, candidates: List[Dict], query_vector: np.ndarray) -> List[Dict]:
        """详细搜索（基于片段向量，使用最大段相似度）"""
        candidate_ids = [c['projectitem_id'] for c in candidates]
        
        query = """
        WITH best_segments AS (
            SELECT 
                av.projectitem_id,
                csv.segment_index,
                csv.segment_text,
                csv.start_char_pos,
                csv.end_char_pos,
                (csv.segment_vector <=> %s) AS segment_distance,
                ROW_NUMBER() OVER (PARTITION BY av.projectitem_id ORDER BY (csv.segment_vector <=> %s)) as rn
            FROM article_vectors av
            JOIN content_segment_vectors csv ON av.id = csv.article_vector_id
            WHERE av.projectitem_id = ANY(%s)
                AND csv.confidence_score > 0.8
        )
        SELECT 
            projectitem_id,
            segment_index,
            segment_text,
            start_char_pos,
            end_char_pos,
            segment_distance
        FROM best_segments
        WHERE rn = 1
        ORDER BY segment_distance
        """
        
        result = await self.db.execute(query, [
            self.vector_to_json(query_vector),
            self.vector_to_json(query_vector),
            candidate_ids
        ])
        
        return result.fetchall()
```

#### 5.1.2 性能优化查询
为了高效计算最大段相似度，我们使用以下优化策略：

```sql
-- 优化后的最大段相似度查询
WITH ranked_segments AS (
    SELECT 
        av.projectitem_id,
        csv.segment_index,
        csv.segment_text,
        csv.start_char_pos,
        csv.end_char_pos,
        (csv.segment_vector <=> %s) AS segment_distance,
        ROW_NUMBER() OVER (
            PARTITION BY av.projectitem_id 
            ORDER BY (csv.segment_vector <=> %s)
        ) as similarity_rank
    FROM article_vectors av
    JOIN content_segment_vectors csv ON av.id = csv.article_vector_id
    WHERE csv.confidence_score >= 0.8
        AND av.projectitem_id = ANY(%s)
)
SELECT 
    projectitem_id,
    segment_index,
    segment_text,
    start_char_pos,
    end_char_pos,
    segment_distance
FROM ranked_segments
WHERE similarity_rank = 1
ORDER BY segment_distance
LIMIT %s;
```

**性能优化要点**：
- 使用`ROW_NUMBER()`窗口函数避免子查询
- 在`ORDER BY`子句中直接计算相似度，利用索引
- 通过`PARTITION BY`确保每个文档只返回最佳片段
- 添加`confidence_score`过滤条件提高质量

### 5.2 混合搜索
```python
class HybridSearchService:
    async def hybrid_search(self, query_vector: np.ndarray, 
                           article_weight: float = 0.6,
                           segment_weight: float = 0.4,
                           limit: int = 10) -> List[Dict]:
        """混合搜索：结合文章级和片段级相似度，使用最大段相似度"""
        query = """
        WITH article_scores AS (
            SELECT 
                av.projectitem_id,
                av.title_text,
                av.content_text,
                (av.title_vector <=> %s) * 0.3 + (av.content_vector <=> %s) * 0.7 AS article_distance
            FROM article_vectors av
            WHERE av.avg_confidence > 0.7
        ),
        best_segments AS (
            SELECT 
                av.projectitem_id,
                MIN(csv.segment_vector <=> %s) AS best_segment_distance
            FROM article_vectors av
            JOIN content_segment_vectors csv ON av.id = csv.article_vector_id
            WHERE csv.confidence_score >= 0.8
            GROUP BY av.projectitem_id
        )
        SELECT 
            as.projectitem_id,
            as.title_text,
            as.content_text,
            as.article_distance * %s + bs.best_segment_distance * %s AS combined_distance
        FROM article_scores as
        JOIN best_segments bs ON as.projectitem_id = bs.projectitem_id
        ORDER BY combined_distance
        LIMIT %s
        """
        
        result = await self.db.execute(query, [
            self.vector_to_json(query_vector),
            self.vector_to_json(query_vector),
            self.vector_to_json(query_vector),
            article_weight,
            segment_weight,
            limit
        ])
        
        return result.fetchall()
```

## 6. API设计

### 6.1 搜索API端点
```python
@router.get("/api/search")
async def search_articles(
    q: str = Query(..., description="搜索关键词"),
    type: str = Query("all", description="搜索类型: all/articles/comments"),
    limit: int = Query(10, ge=1, le=100, description="返回结果数量"),
    offset: int = Query(0, ge=0, description="分页偏移"),
    session: AsyncSession = Depends(get_async_session)
):
    """全文检索API"""
    search_service = HierarchicalSearchService(session)
    results = await search_service.search(q, limit)
    
    return {
        "query": q,
        "total": len(results),
        "results": results
    }
```

### 6.2 管理API端点
```python
@router.post("/api/admin/vectorize")
async def vectorize_content(
    type: str = Query(..., description="向量化类型: articles/comments"),
    ids: Optional[List[int]] = Query(None, description="指定ID列表"),
    batch_size: int = Query(100, description="批处理大小"),
    current_user: Dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """内容向量化API"""
    vectorization_service = BatchVectorizationService(session)
    
    if type == "articles":
        await vectorization_service.vectorize_articles(ids)
    elif type == "comments":
        await vectorization_service.vectorize_comments(ids)
    
    return {"message": "向量化完成"}
```

## 7. 性能优化

### 7.1 硬件性能分析
- **CPU**: i7-1065G7 (4核8线程)
- **内存**: 16GB
- **预估处理时间**: 1-2小时（优化后）

### 7.2 优化策略
```python
class PerformanceOptimizer:
    def __init__(self):
        self.parallel_workers = 6  # 保留2个线程给系统
        self.batch_size = 100
        self.cache_size = 1000
    
    async def parallel_vectorization(self, texts: List[str]):
        """并行向量化"""
        with ThreadPoolExecutor(max_workers=self.parallel_workers) as executor:
            tasks = [executor.submit(self.vectorize_text, text) for text in texts]
            results = [task.result() for task in tasks]
        return results
    
    def batch_database_operations(self, operations: List[Dict]):
        """批量数据库操作"""
        # 分批执行数据库操作
        for i in range(0, len(operations), self.batch_size):
            batch = operations[i:i + self.batch_size]
            self.execute_batch(batch)
```

### 7.3 缓存策略
```python
class VectorCache:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.cache_ttl = 3600  # 1小时
    
    async def get_cached_vector(self, text_hash: str) -> Optional[np.ndarray]:
        """获取缓存的向量"""
        cached = await self.redis.get(f"vector:{text_hash}")
        if cached:
            return np.frombuffer(cached, dtype=np.float32)
        return None
    
    async def cache_vector(self, text_hash: str, vector: np.ndarray):
        """缓存向量"""
        await self.redis.setex(
            f"vector:{text_hash}",
            self.cache_ttl,
            vector.tobytes()
        )
```

## 8. 数据迁移

### 8.1 迁移脚本
```python
class DataMigrationService:
    def __init__(self, db_session):
        self.db = db_session
        self.vectorization_service = BERTVectorizationService()
    
    async def migrate_articles(self, batch_size: int = 100):
        """迁移文章数据"""
        # 获取所有文章
        articles = await self.get_all_articles()
        
        # 分批处理
        for i in range(0, len(articles), batch_size):
            batch = articles[i:i + batch_size]
            await self.process_article_batch(batch)
            
            # 显示进度
            progress = (i + len(batch)) / len(articles) * 100
            print(f"迁移进度: {progress:.1f}%")
    
    async def migrate_comments(self, batch_size: int = 200):
        """迁移评论数据"""
        comments = await self.get_all_comments()
        
        for i in range(0, len(comments), batch_size):
            batch = comments[i:i + batch_size]
            await self.process_comment_batch(batch)
```

### 8.2 增量更新
```python
class IncrementalUpdateService:
    async def update_new_articles(self):
        """更新新文章"""
        # 查找未向量化的文章
        new_articles = await self.get_unvectorized_articles()
        
        for article in new_articles:
            await self.vectorize_article(article)
    
    async def update_modified_articles(self):
        """更新修改的文章"""
        # 查找修改时间晚于向量化时间的文章
        modified_articles = await self.get_modified_articles()
        
        for article in modified_articles:
            await self.update_article_vectors(article)
```

## 9. 监控和维护

### 9.1 性能监控
```python
class SearchPerformanceMonitor:
    def __init__(self):
        self.metrics = {
            'search_count': 0,
            'avg_search_time': 0,
            'cache_hit_rate': 0,
            'error_count': 0
        }
    
    def record_search(self, search_time: float, cache_hit: bool):
        """记录搜索性能"""
        self.metrics['search_count'] += 1
        self.metrics['avg_search_time'] = (
            (self.metrics['avg_search_time'] * (self.metrics['search_count'] - 1) + search_time) 
            / self.metrics['search_count']
        )
        
        if cache_hit:
            self.metrics['cache_hit_rate'] = (
                (self.metrics['cache_hit_rate'] * (self.metrics['search_count'] - 1) + 1) 
                / self.metrics['search_count']
            )
```

### 9.2 数据质量检查
```python
class DataQualityChecker:
    async def check_vector_quality(self):
        """检查向量数据质量"""
        # 检查缺失向量
        missing_vectors = await self.find_missing_vectors()
        
        # 检查向量质量
        low_quality_vectors = await self.find_low_quality_vectors()
        
        # 检查数据一致性
        inconsistent_data = await self.find_inconsistent_data()
        
        return {
            'missing_vectors': len(missing_vectors),
            'low_quality_vectors': len(low_quality_vectors),
            'inconsistent_data': len(inconsistent_data)
        }
```

## 10. 部署和配置

### 10.1 环境要求
```bash
# Python依赖
pip install transformers==4.35.0
pip install torch==2.1.0
pip install numpy==1.24.0
pip install pgvector==0.2.4

# PostgreSQL扩展
CREATE EXTENSION IF NOT EXISTS vector;
```

### 10.2 配置文件
```python
# config/vector_search.py
class VectorSearchConfig:
    # BERT模型配置
    MODEL_NAME = "google-bert-base-chinese"
    MAX_LENGTH = 512
    BATCH_SIZE = 32
    
    # 文本处理配置
    WINDOW_SIZE = 400
    STEP_SIZE = 200
    MAX_TEXT_LENGTH = 128000
    
    # 搜索配置
    DEFAULT_LIMIT = 10
    MAX_LIMIT = 100
    CACHE_TTL = 3600
    
    # 性能配置
    PARALLEL_WORKERS = 6
    VECTOR_CACHE_SIZE = 1000
```

## 11. 测试策略

### 11.1 单元测试
```python
class TestVectorizationService:
    async def test_short_text_vectorization(self):
        """测试短文本向量化"""
        service = BERTVectorizationService()
        text = "这是一篇短文章"
        vector = await service.vectorize_text(text)
        
        assert vector.shape == (768,)
        assert not np.allclose(vector, 0)
    
    async def test_long_text_segmentation(self):
        """测试长文本分割"""
        processor = SlidingWindowProcessor()
        long_text = "很长的文章内容..." * 1000
        
        segments = processor.split_text(long_text)
        assert len(segments) > 1
        assert all(seg['length'] <= 400 for seg in segments)
```

### 11.2 集成测试
```python
class TestSearchIntegration:
    async def test_end_to_end_search(self):
        """测试端到端搜索"""
        # 1. 创建测试数据
        article = await self.create_test_article()
        
        # 2. 向量化
        await self.vectorize_article(article)
        
        # 3. 搜索
        results = await self.search_articles("测试关键词")
        
        # 4. 验证结果
        assert len(results) > 0
        assert results[0]['projectitem_id'] == article.id
```

## 12. 风险评估和缓解

### 12.1 技术风险
- **模型加载时间**: 首次加载BERT模型需要时间
  - 缓解: 预加载模型，使用缓存
- **内存占用**: BERT模型和向量数据占用大量内存
  - 缓解: 使用量化模型，分批处理
- **处理时间**: 大量数据向量化需要时间
  - 缓解: 并行处理，增量更新

### 12.2 数据风险
- **数据一致性**: 向量数据与原文数据不同步
  - 缓解: 定期同步检查，增量更新
- **向量质量**: 低质量向量影响搜索效果
  - 缓解: 质量检查，重新向量化

## 13. 未来扩展

### 13.1 功能扩展
- **多语言支持**: 支持英文等其他语言
- **实时搜索**: 实现实时搜索建议
- **个性化搜索**: 基于用户历史的个性化推荐
- **搜索分析**: 搜索行为分析和优化

### 13.2 技术升级
- **模型升级**: 升级到更先进的预训练模型
- **硬件优化**: 使用GPU加速向量化
- **分布式部署**: 支持分布式向量搜索

## 14. 总结

本技术方案提供了完整的BERT全文检索解决方案，包括：

1. **完整的数据模型设计** - 支持多片段存储和高效检索
2. **智能的文本处理策略** - 解决长文本向量化问题
3. **高效的搜索算法** - 分层搜索和混合检索
4. **完善的API接口** - 支持多种搜索场景
5. **详细的性能优化** - 针对硬件特点的优化策略
6. **可靠的数据迁移** - 平滑的现有数据迁移方案

该方案在保证搜索质量的同时，充分考虑了性能、可维护性和可扩展性，为BlogN2系统提供了强大的智能搜索能力。

---

**文档版本**: v1.0  
**创建日期**: 2024年12月  
**最后更新**: 2024年12月  
**维护者**: BlogN2开发团队
