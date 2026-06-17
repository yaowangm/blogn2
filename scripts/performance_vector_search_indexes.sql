-- Optional vector-search performance indexes for BlogN2.
--
-- Do not run inside a transaction: CREATE INDEX CONCURRENTLY requires
-- autocommit. These indexes are safe to create repeatedly and do not change
-- application-visible data or query results.
--
-- Run manually when you are ready to update the database:
--   psql blogn -f scripts/performance_vector_search_indexes.sql

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_article_vectors_title_hnsw
    ON article_vectors USING hnsw (title_vector vector_cosine_ops);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_article_vectors_content_hnsw
    ON article_vectors USING hnsw (content_vector vector_cosine_ops);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_segment_vectors_vector_hnsw
    ON content_segment_vectors USING hnsw (segment_vector vector_cosine_ops);

ANALYZE article_vectors;
ANALYZE content_segment_vectors;
