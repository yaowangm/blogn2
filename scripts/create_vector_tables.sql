-- BERT全文检索向量存储表结构创建脚本
-- 执行前请确保已安装pgvector扩展: CREATE EXTENSION IF NOT EXISTS vector;

-- ===========================================
-- 1. 文章向量表 (主表)
-- ===========================================
CREATE TABLE IF NOT EXISTS article_vectors (
    id SERIAL PRIMARY KEY,
    projectitem_id INTEGER UNIQUE REFERENCES projectitem(id) ON DELETE CASCADE,
    
    -- 标题向量（直接存储，无需分片）- 与 paraphrase-multilingual-MiniLM-L12-v2 一致，384 维
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
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 约束
    CONSTRAINT chk_segment_count CHECK (segment_count > 0),
    CONSTRAINT chk_avg_confidence CHECK (avg_confidence >= 0.0 AND avg_confidence <= 1.0),
    CONSTRAINT chk_key_segment_ratio CHECK (key_segment_ratio >= 0.0 AND key_segment_ratio <= 1.0)
);

-- ===========================================
-- 2. 片段向量表 (详细存储)
-- ===========================================
CREATE TABLE IF NOT EXISTS content_segment_vectors (
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
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 约束
    CONSTRAINT chk_segment_index CHECK (segment_index >= 0),
    CONSTRAINT chk_segment_length CHECK (segment_length > 0),
    CONSTRAINT chk_overlap_ratio CHECK (overlap_ratio >= 0.0 AND overlap_ratio <= 1.0),
    CONSTRAINT chk_confidence_score CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    UNIQUE(article_vector_id, segment_index)
);

-- ===========================================
-- 3. 评论向量表
-- ===========================================
CREATE TABLE IF NOT EXISTS comment_vectors (
    id SERIAL PRIMARY KEY,
    post_id INTEGER UNIQUE REFERENCES post(id) ON DELETE CASCADE,
    
    -- 评论向量（与 BERT 模型 384 维一致）
    title_vector VECTOR(384),
    content_vector VECTOR(384),
    title_text TEXT,
    content_text TEXT,
    
    -- 元数据
    segment_count INTEGER DEFAULT 1,
    vectorization_method VARCHAR(50) DEFAULT 'direct',
    total_text_length INTEGER,
    max_segment_length INTEGER,
    
    -- 质量指标
    avg_confidence FLOAT DEFAULT 1.0,
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 约束
    CONSTRAINT chk_comment_segment_count CHECK (segment_count > 0),
    CONSTRAINT chk_comment_avg_confidence CHECK (avg_confidence >= 0.0 AND avg_confidence <= 1.0)
);

-- ===========================================
-- 4. 创建索引
-- ===========================================

-- 文章向量表索引
CREATE INDEX IF NOT EXISTS idx_article_vectors_projectitem_id ON article_vectors(projectitem_id);
CREATE INDEX IF NOT EXISTS idx_article_vectors_created_at ON article_vectors(created_at);
CREATE INDEX IF NOT EXISTS idx_article_vectors_updated_at ON article_vectors(updated_at);

-- 文章向量HNSW索引（用于快速相似度搜索）
CREATE INDEX IF NOT EXISTS idx_article_vectors_title_hnsw ON article_vectors USING hnsw (title_vector vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_article_vectors_content_hnsw ON article_vectors USING hnsw (content_vector vector_cosine_ops);

-- 片段向量表索引
CREATE INDEX IF NOT EXISTS idx_segment_vectors_article_id ON content_segment_vectors(article_vector_id);
CREATE INDEX IF NOT EXISTS idx_segment_vectors_segment_index ON content_segment_vectors(article_vector_id, segment_index);
CREATE INDEX IF NOT EXISTS idx_segment_vectors_created_at ON content_segment_vectors(created_at);
CREATE INDEX IF NOT EXISTS idx_segment_vectors_key_segment ON content_segment_vectors(is_key_segment) WHERE is_key_segment = TRUE;

-- 片段向量HNSW索引
CREATE INDEX IF NOT EXISTS idx_segment_vectors_vector_hnsw ON content_segment_vectors USING hnsw (segment_vector vector_cosine_ops);

-- 评论向量表索引
CREATE INDEX IF NOT EXISTS idx_comment_vectors_post_id ON comment_vectors(post_id);
CREATE INDEX IF NOT EXISTS idx_comment_vectors_created_at ON comment_vectors(created_at);
CREATE INDEX IF NOT EXISTS idx_comment_vectors_updated_at ON comment_vectors(updated_at);

-- 评论向量HNSW索引
CREATE INDEX IF NOT EXISTS idx_comment_vectors_title_hnsw ON comment_vectors USING hnsw (title_vector vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_comment_vectors_content_hnsw ON comment_vectors USING hnsw (content_vector vector_cosine_ops);

-- ===========================================
-- 5. 创建触发器函数（更新时间戳）
-- ===========================================

-- 文章向量表更新时间戳触发器
CREATE OR REPLACE FUNCTION update_article_vectors_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_article_vectors_updated_at
    BEFORE UPDATE ON article_vectors
    FOR EACH ROW
    EXECUTE FUNCTION update_article_vectors_updated_at();

-- 评论向量表更新时间戳触发器
CREATE OR REPLACE FUNCTION update_comment_vectors_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_comment_vectors_updated_at
    BEFORE UPDATE ON comment_vectors
    FOR EACH ROW
    EXECUTE FUNCTION update_comment_vectors_updated_at();

-- ===========================================
-- 6. 创建视图（便于查询）
-- ===========================================

-- 文章向量详细信息视图
CREATE OR REPLACE VIEW article_vector_details AS
SELECT 
    av.id,
    av.projectitem_id,
    av.title_text,
    av.content_text,
    av.segment_count,
    av.vectorization_method,
    av.total_text_length,
    av.avg_confidence,
    av.key_segment_ratio,
    av.created_at,
    av.updated_at,
    pi.name as article_name,
    pi.comment as article_content,
    p.name as project_name,
    u.name as author_name
FROM article_vectors av
LEFT JOIN projectitem pi ON av.projectitem_id = pi.id
LEFT JOIN project p ON pi.projectid = p.id
LEFT JOIN users u ON pi.userid = u.id;

-- 片段向量详细信息视图
CREATE OR REPLACE VIEW segment_vector_details AS
SELECT 
    csv.id,
    csv.article_vector_id,
    csv.segment_index,
    csv.segment_text,
    csv.segment_length,
    csv.confidence_score,
    csv.is_key_segment,
    csv.segment_type,
    csv.created_at,
    av.projectitem_id,
    pi.name as article_name
FROM content_segment_vectors csv
LEFT JOIN article_vectors av ON csv.article_vector_id = av.id
LEFT JOIN projectitem pi ON av.projectitem_id = pi.id;

-- ===========================================
-- 7. 创建统计函数
-- ===========================================

-- 获取向量化统计信息
CREATE OR REPLACE FUNCTION get_vectorization_stats()
RETURNS TABLE (
    total_articles INTEGER,
    vectorized_articles INTEGER,
    total_segments BIGINT,
    avg_segments_per_article NUMERIC,
    total_comments INTEGER,
    vectorized_comments INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        (SELECT COUNT(*)::INTEGER FROM projectitem WHERE status = 1) as total_articles,
        (SELECT COUNT(*)::INTEGER FROM article_vectors) as vectorized_articles,
        (SELECT COUNT(*) FROM content_segment_vectors) as total_segments,
        (SELECT COALESCE(AVG(segment_count), 0) FROM article_vectors) as avg_segments_per_article,
        (SELECT COUNT(*)::INTEGER FROM post WHERE projectitemid > 0) as total_comments,
        (SELECT COUNT(*)::INTEGER FROM comment_vectors) as vectorized_comments;
END;
$$ LANGUAGE plpgsql;

-- ===========================================
-- 8. 创建清理函数
-- ===========================================

-- 清理孤立向量数据
CREATE OR REPLACE FUNCTION cleanup_orphaned_vectors()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER := 0;
BEGIN
    -- 清理孤立的文章向量
    DELETE FROM article_vectors 
    WHERE projectitem_id NOT IN (SELECT id FROM projectitem);
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- 清理孤立的片段向量
    DELETE FROM content_segment_vectors 
    WHERE article_vector_id NOT IN (SELECT id FROM article_vectors);
    
    -- 清理孤立的评论向量
    DELETE FROM comment_vectors 
    WHERE post_id NOT IN (SELECT id FROM post);
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- ===========================================
-- 9. 权限设置
-- ===========================================

-- 为应用用户授予必要的权限
-- GRANT SELECT, INSERT, UPDATE, DELETE ON article_vectors TO wy;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON content_segment_vectors TO wy;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON comment_vectors TO wy;
-- GRANT USAGE, SELECT ON SEQUENCE article_vectors_id_seq TO wy;
-- GRANT USAGE, SELECT ON SEQUENCE content_segment_vectors_id_seq TO wy;
-- GRANT USAGE, SELECT ON SEQUENCE comment_vectors_id_seq TO wy;

-- ===========================================
-- 10. 验证脚本
-- ===========================================

-- 验证表是否创建成功
SELECT 
    schemaname,
    tablename,
    tableowner
FROM pg_tables 
WHERE tablename IN ('article_vectors', 'content_segment_vectors', 'comment_vectors')
ORDER BY tablename;

-- 验证索引是否创建成功
SELECT 
    indexname,
    tablename,
    indexdef
FROM pg_indexes 
WHERE tablename IN ('article_vectors', 'content_segment_vectors', 'comment_vectors')
ORDER BY tablename, indexname;

-- 验证扩展是否可用
SELECT 
    extname,
    extversion,
    extnamespace::regnamespace as schema
FROM pg_extension 
WHERE extname = 'vector';

-- 测试向量功能
SELECT 
    '[1,2,3]'::vector as test_vector,
    '[1,2,3]'::vector <-> '[1,2,4]'::vector as cosine_distance;
