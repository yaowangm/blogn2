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
- **多语言模型**: `paraphrase-multilingual-MiniLM-L12-v2` (384维向量)
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
    title_vector VECTOR(384),
    title_text TEXT,
    
    -- 内容向量（聚合后的最终向量）
    content_vector VECTOR(384),
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
    segment_vector VECTOR(384),
    
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
    title_vector VECTOR(384),
    content_vector VECTOR(384),
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
        self.model_name = "paraphrase-multilingual-MiniLM-L12-v2"
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
        
        return vector[0]  # 返回384维向量
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

当前实现统一在 `HierarchicalSearchService`（`src/services/search_service.py`）中：文章检索入口为 `hybrid_search_articles`，采用「all_segments → best_segments → article_scores → ranked」单次 SQL + 应用层过量拉取与过滤。**与代码一致的描述见 5.3**；5.1、5.2 为概念与权重说明。

### 5.1 分层搜索策略（概念）

#### 5.1.1 相似度计算策略
在基于 BERT 的全文检索中，我们采用**最大段相似度**策略而非段相似度之和，原因如下：

1. **语义匹配的准确性**: 最大段相似度能够准确识别文档中最相关的片段，避免不相关片段对整体相似度的干扰
2. **避免长度偏差**: 段相似度之和会导致长文档在搜索中具有不公平的优势，即使其相关性较低
3. **提高搜索精度**: 最大段相似度更符合用户期望，即找到包含最相关内容片段的文档
4. **计算效率**: 使用窗口函数可高效得到每篇的最佳匹配片段

**说明**：当前代码并未采用「先 fast_search 再 detailed_search」的两阶段，而是一体化混合检索（见 5.3.6）。

#### 5.1.2 性能优化查询（概念）
使用 `DISTINCT ON` / `ROW_NUMBER()` 按篇取最佳片段、`confidence_score >= 0.8` 过滤，与实现中 `best_segments` 的 `DISTINCT ON (projectitem_id)` 思路一致。实际 SQL 结构见 5.3.6。

### 5.2 混合搜索权重与双通道排布（当前实现）

1. **语义候选（hybrid_search_articles 内部）**  
   - 仍使用 **文章级 10% + 片段级 90%**（`article_weight=0.1`, `segment_weight=0.9`），文章级内部为标题 30%、内容 70%。  
   - 相似度为 `1 - (vector <=> query_vector)`（越大越相似），组合公式见 5.3.1。  
2. **最终排序（search() 顶层）**  
   - 搜索服务不再直接使用 SQL 侧的组合相似度做“唯一排序依据”，而是同时考虑：  
     - **lexical_score**：标题/正文/作者是否包含查询串（关键词通道）；  
     - **semantic_score**：由向量检索得到的相似度（语义通道）。  
   - 根据查询类型（短中文实体/普通短语/长查询）在应用层做加权：  
     - 短中文实体：词面匹配权重更高（lexical 0.7 + semantic 0.3）；  
     - 长查询：语义权重更高（lexical 0.3 + semantic 0.7）；  
     - 其他：约 0.5 / 0.5。  
   - 这使得查询如“爱因斯坦”一类在**真实包含该串的文档**上有更稳定的召回。

### 5.3 业务场景与实现细节（当前实现）

本节对应代码：`src/services/search_service.py` 中的 `HierarchicalSearchService`，以及控制器 `src/controllers/search.py` 的搜索接口。以下为已实现的业务场景与对应实现要点。

#### 5.3.1 阈值与常量

| 常量 | 值 | 用途 |
|------|-----|------|
| `DEFAULT_THRESHOLD` | 0.55 | 相似度兜底阈值，用于：`relevance_score` 为 0 或缺失时的展示兜底（避免前端显示 0%）、以及无向量时的关键词搜索默认阈值 |
| `TITLE_ONLY_MIN_SIMILARITY` | 0.85 | 仅在语义候选生成阶段（`hybrid_search_articles` 内部）用于过滤“无正文+低相关标题”的候选，避免类似「上头像」这类泛匹配标题进入语义候选池 |

**组合相似度公式（语义候选阶段）**：

```text
semantic_relevance = COALESCE(article_similarity, 0) * 0.1 + segment_similarity * 0.9
```

- 有正文：在生成语义候选时，主要依赖片段相似度与动态阈值过滤，`TITLE_ONLY_MIN_SIMILARITY` 只起到兜底作用。  
- 无正文：仅当 `semantic_relevance >= TITLE_ONLY_MIN_SIMILARITY` 时才作为语义候选，避免无正文+低语义相关标题被后续排序带入前几页；但若标题文本本身包含查询串，则关键词通道仍可将其召回。

#### 5.3.2 相似度展示与兜底（避免前端 0%）

**场景**：向量检索或格式化后可能出现 `relevance_score` 为 0 或缺失，前端会显示「0% 相似度」。

**实现**：

1. **服务层** `_clamp_items_relevance(items, threshold)`（`search_service.py`）：仅当 `relevance_score` 为 0 或缺失时，将其设为当前请求的 `dynamic_threshold`（或 `DEFAULT_THRESHOLD`），有真实分数则不改。
2. **控制器层**（`search.py`）：对返回的 `results` 中每条做同样逻辑：`relevance_score = dynamic_threshold if (cur <= 0) else cur`，保证前端不会收到 0。

SQL 中不再对 `relevance_score` 做 `GREATEST(..., threshold)`，直接返回原始相似度，由上述两层做兜底。

#### 5.3.3 作者/标题关键词匹配与双通道合并

**场景**：用户搜作者名（如「左轻侯」）、具体实体（如「爱因斯坦」）或明显关键词时，希望“文本中确实包含该串”的结果优先展示。

**实现（最新版）**：

1. **关键词检索通道（lexical）**：  
   - `_keyword_search_articles` / `_keyword_search_comments` 在 WHERE 中对标题、正文与作者名做 `ILIKE` 匹配。  
   - 对关键词结果在应用层打 `lexical_score`：  
     - 若标题/正文/作者中包含完整查询串，则记为 1.0；  
     - 否则（只是 ILIKE 命中）则记为 0.5。  
2. **语义检索通道（semantic）**：  
   - 使用 `hybrid_search_articles` / `_search_comments` 生成语义候选，得到 `semantic_score`。  
3. **统一合并与排序**：  
   - 将两通道的候选按 ID 合并，保留更高的 `semantic_score`，并对 `lexical_score` / `semantic_score` 做批内归一化。  
   - 根据查询类型（短中文实体/长查询等）选择权重，计算最终 `relevance_score = w_lex * lexical + w_sem * semantic` 并排序。  
4. **强兜底规则（articles, page=1）**：  
   - 若第一页结果中没有任何“标题/正文/作者真正包含查询串”的条目，则从候选中强制提取若干此类条目，插入到榜首再补满 `limit` 条，避免用户遇到“明明有这几个字却完全搜不到”的体验。

#### 5.3.4 无正文文章：标题泛匹配排除、精确匹配保留

**场景**：  
- 无正文文章若标题与查询仅语义泛匹配（如「上头像」对「邱华栋」约 60%），不应排在前面；  
- 若标题即查询词（如「邱华栋」/「爱因斯坦」）或高度相关，应可被搜到。

**实现（语义候选 + 双通道）**：

1. **语义候选阶段**（`hybrid_search_articles` 的 `ranked` CTE）：  
   - 对“无正文+语义相似度低于 `TITLE_ONLY_MIN_SIMILARITY`”的标题，直接在候选层剔除，避免这类条目凭借向量噪声挤入候选池。  
2. **关键词通道补充**：  
   - 只要标题文本本身包含查询串（如标题恰为「邱华栋」或「爱因斯坦」），即使语义相似度略低，仍会通过关键词通道进入候选池，并在最终排序时获得较高 `lexical_score`。  

效果：  
- 类似“上头像”这类与查询仅有语义泛关联但既无正文、又不包含查询串的标题会被过滤；  
- 真实标题为实体词本身的无正文文章仍能通过关键词通道被稳定召回。

#### 5.3.5 每页固定条数、分页与候选池限制

**场景**：  
分页后每页应尽量为固定条数（如 10 条），且前几页的结果质量和排序要稳定，同时又要避免“深度分页”对向量检索和 SQL 带来过大压力。

**实现（最新版）**：

1. **语义候选（articles, `hybrid_search_articles`）**：  
   - 仍然按批从数据库拉取（每批 `batch_size = max(limit*5, 50)`），过滤后累积到 `all_valid`。  
   - 对于仅 `type="articles"` 的场景，分页与 `total` 逻辑与此前版本一致：  
     - `items_for_page = all_valid[(page-1)*limit : page*limit]`；  
     - `total = len(all_valid)`；  
     - `has_more = (page * limit) < total`。  
2. **双通道合并与候选池（search 顶层）**：  
   - 为保证性能，顶层只从关键词/语义两通道各取前 `limit*5` 条作为候选池（评论亦然），在此集合内做排序和分页。  
   - 换言之，对于特别多的匹配结果，只保证“前若干页”（由候选池大小决定）结果的质量和完整性，而不是支持无限深度分页。  

这样既保证了**前几页的排序质量与分页稳定**，又避免了在向量检索场景下对“第几百页”的深度分页开销失控。

#### 5.3.6 混合搜索权重与 SQL 结构概要

- **权重**：文章级 10%、片段级 90%（`article_weight=0.1`, `segment_weight=0.9`）；文章级内部为标题 30%、内容 70%。
- **流程概要**：  
  `all_segments`（标题片段 + 内容片段）→ `best_segments`（每篇取相似度最高的一段，且相似度 ≥ `adjusted_threshold`）→ `article_scores`（文章级相似度）→ `ranked`（组合相似度 ≥ 0.85）→ 应用层按批拉取、过滤、累积 → 分页取 `items_for_page`，`total = len(all_valid)`。

#### 5.3.7 测试覆盖与评估脚本

单元测试位于 `tests/unit/test_bert_vectorization_services.py` 的 `TestHierarchicalSearchService`，覆盖包括：

- **常量**：`test_constants` 校验 `DEFAULT_THRESHOLD == 0.55`、`TITLE_ONLY_MIN_SIMILARITY == 0.85`。
- **关键词合并**：`test_merge_keyword_skips_no_content`（无正文不并入）、`test_merge_keyword_keeps_items_with_content`（有正文并入并 0.95）、`test_merge_keyword_respects_limit_and_dedup`（去重与 limit）。
- **混合搜索过滤与分页**：`test_hybrid_search_filters_low_relevance_no_content`（无正文且低相似度被过滤）、`test_hybrid_search_page_size_and_total`（每页条数 ≤ limit、total 为有效条数）、`test_hybrid_search_pagination_second_page`（第二页条数与 has_more、total 一致）。
- **相似度兜底**：`test_clamp_items_relevance`（仅 0/缺失时改为阈值）；**行解析**：`test_row_relevance_extraction`（从 tuple/Row/dict 正确取 `relevance_score`）。

本地验证建议：  
- 修改搜索逻辑后运行上述单元测试；  
- 对搜索 API 做一次 curl 或前端验证（如搜索「邱华栋」检查无 id=1022、total 与每页条数符合预期）；  
- 运行评估脚本 `scripts/eval_fulltext_search.py`，通过“从真实文章中抽取短语再反查”的方式量化 `Recall@K` / `MRR@K`，对比不同参数组合（例如候选池大小、lexical/semantic 权重）对召回率和排序质量的影响。

## 6. API设计

### 6.1 搜索API端点（当前实现）

- **静态搜索页**：`GET /search`（`src/utils/page_handlers.py`）返回 `search.html`，由前端调用下方 JSON API。
- **搜索 JSON API**：`GET /api/search`（`src/controllers/search.py` 的路由器在 `src/utils/api_handlers.py` 中以 `prefix="/api"` 挂载）。需向量化服务（`request.app.state.model_cache` 或 `get_cached_model()`）与异步数据库会话。

**请求参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| `q` | string | 搜索关键词（必填） |
| `type` | string | 搜索类型：`all` / `articles` / `comments`，默认 `all` |
| `sort` | string | 排序：`relevance` / `date` / `popularity`，默认 `relevance` |
| `page` | int | 页码，从 1 开始，默认 1 |
| `limit` | int | 每页条数，默认 10，上限 100 |

**响应**：`search_service.search()` 返回的 `items`、`total`、`has_more`、`dynamic_threshold` 等经控制器组装后返回；控制器会对每条结果的 `relevance_score` 做兜底（0 或缺失时设为 `dynamic_threshold`）。返回字段包括 `query`、`type`、`sort`、`page`、`limit`、`total`、`results`、`has_more`、`search_time`、`dynamic_threshold`、`search_method` 等。

**评论类结果（`type: "comment"`）字段约定（与当前 SQL / `_format_comment_result` 一致）**：

| 字段 | 含义 |
|------|------|
| `id` | `post` 表主键，即该条评论（或回复）记录 ID |
| `projectitem_id` / `article_id` | 所属博文的 `projectitem.id`；二者相同。关键词与向量评论查询的 SELECT 均附带该列 |
| 其余 | `title`、`content`、`author`、`created_at`、`relevance_score` 等与文章条目结构类似 |

前端（`src/static/js/pages/search.js`）对博文评论生成 `/article/{projectitem_id}#post{id}`，与文章页 `article-comments-card` 的 `#post{id}` 锚点滚动一致；无有效博文 id 时（如留言本 `projectitem_id` 为 0）可退化为 `/thread/{id}`。

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
    MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
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

搜索相关业务场景的单元测试见 **5.3.7 测试覆盖**，位于 `tests/unit/test_bert_vectorization_services.py` 的 `TestHierarchicalSearchService`，覆盖阈值常量、关键词合并（无正文不并入/去重/limit）、混合搜索过滤与分页、相似度兜底与行解析等。

通用向量化与分割示例：

```python
class TestVectorizationService:
    async def test_short_text_vectorization(self):
        """测试短文本向量化"""
        service = BERTVectorizationService()
        text = "这是一篇短文章"
        vector = await service.vectorize_text(text)
        
        assert vector.shape == (384,)  # 当前模型 384 维
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

**文档版本**: v1.1  
**创建日期**: 2024年12月  
**最后更新**: 2025年2月  
**维护者**: BlogN2开发团队  

**v1.1 更新说明**：新增「5.3 业务场景与实现细节」，汇总相似度兜底、作者/标题关键词合并、无正文文章过滤、分页与 total 一致等场景及对应代码实现与测试覆盖；修正 5.1/5.2 为概念说明并注明当前实现以 5.3 为准（混合权重 0.1/0.9）；6.1 按当前搜索 API（page、sort、控制器兜底）更新。
