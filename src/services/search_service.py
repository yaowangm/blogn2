"""
搜索服务

实现基于BERT向量的智能搜索功能，支持文章和评论的语义搜索。
使用分层搜索策略，结合向量相似度计算和动态阈值调整。

主要功能：
- 语义搜索（基于BERT向量相似度）
- 动态阈值调整（根据查询特征）
- 多类型内容搜索（文章+评论）
- 结果排序和分页

技术特性：
- 使用pgvector进行高效向量检索
- 智能阈值计算提高搜索精度
- 支持多种排序方式
- 错误降级处理
"""

import json
import logging
import math
import time
from typing import Dict, Any, List, Optional

import numpy as np
from sqlalchemy import text
from sqlmodel.ext.asyncio.session import AsyncSession

logger = logging.getLogger(__name__)

# 默认相似度阈值 55%，仅用于兜底（0/缺失时）及关键词回退时的返回值
DEFAULT_THRESHOLD = 0.55
# 无正文文章仅当标题与查询相似度 >= 此值时才保留（避免“上头像”等泛匹配），有正文仍用动态阈值
TITLE_ONLY_MIN_SIMILARITY = 0.85


class HierarchicalSearchService:
    """
    分层搜索服务

    基于BERT向量实现智能语义搜索，支持文章和评论的混合搜索。
    使用优化的混合搜索策略：10%文章级 + 90%片段级相似度。
    使用动态阈值调整和智能排序提高搜索质量。
    """

    def __init__(self, vectorization_service, session: AsyncSession):
        """
        初始化搜索服务

        Args:
            vectorization_service: 向量化服务实例
            session: 数据库会话
        """
        self.vectorization_service = vectorization_service
        self.session = session

        # 混合搜索权重配置（优化后：10%文章级 + 90%片段级）
        self.article_weight = 0.1  # 文章级权重
        self.segment_weight = 0.9  # 片段级权重

        # 文章级内部权重（标题 vs 内容）
        self.title_weight = 0.3    # 标题权重
        self.content_weight = 0.7  # 内容权重

    @staticmethod
    def _safe_float(value: Any, default: float = 0.0) -> float:
        """将可能为 nan/inf 的浮点数转为合法 JSON 数值，避免序列化报错。"""
        if value is None:
            return default
        try:
            f = float(value)
            if math.isnan(f) or math.isinf(f):
                return default
            return f
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _row_relevance(row: Any, index: int = 5, default: float = 0.0) -> float:
        """从 SQL 结果行取 relevance_score：索引 → _mapping → 字典 key。"""
        try:
            if hasattr(row, "__getitem__") and len(row) > index:
                return HierarchicalSearchService._safe_float(row[index], default)
            if hasattr(row, "_mapping") and "relevance_score" in row._mapping:
                return HierarchicalSearchService._safe_float(row._mapping["relevance_score"], default)
            if isinstance(row, dict) and "relevance_score" in row:
                return HierarchicalSearchService._safe_float(row["relevance_score"], default)
        except (TypeError, IndexError, KeyError):
            pass
        return default

    @staticmethod
    def _clamp_items_relevance(items: List[Dict], threshold: float) -> None:
        """仅当 relevance_score 为 0 或缺失时设为 threshold，避免前端显示 0%；有真实分数则不改。"""
        if threshold <= 0:
            return
        for it in items:
            cur = HierarchicalSearchService._safe_float(it.get("relevance_score"), 0.0) if "relevance_score" in it else 0.0
            if cur <= 0:
                it["relevance_score"] = threshold

    @staticmethod
    def _merge_keyword_into_article_items(
        vector_items: List[Dict], keyword_items: List[Dict], limit: int
    ) -> List[Dict]:
        """第一页时：把关键词（含作者名）匹配并入向量结果；无正文文章不并入，避免仅靠作者匹配的无内容条目标题无关却排前面。"""
        seen = {it["id"] for it in vector_items}
        combined = list(vector_items)
        for kw in keyword_items:
            if kw.get("id") in seen:
                continue
            content = (kw.get("content") or kw.get("comment") or "").strip()
            if not content:
                continue
            combined.append({**kw, "relevance_score": 0.95})
            seen.add(kw["id"])
        combined.sort(key=lambda x: HierarchicalSearchService._safe_float(x.get("relevance_score", 0)), reverse=True)
        return combined[:limit]

    async def _merge_keyword_into_article_results(
        self, article_results: Dict[str, Any], query: str, limit: int
    ) -> Dict[str, Any]:
        """第一页且有关键词时：把关键词（标题/内容/作者）匹配并入文章结果并重排序。"""
        if not query or not query.strip():
            return article_results
        kw = await self._keyword_search_articles(query.strip(), 1, limit * 2)
        article_results["items"] = self._merge_keyword_into_article_items(
            article_results.get("items", []), kw.get("items", []), limit
        )
        return article_results

    @staticmethod
    def _escape_like_pattern(s: str) -> str:
        """Escape \\, % and _ for safe literal use inside a LIKE/ILIKE pattern (PostgreSQL)."""
        return s.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

    @staticmethod
    def _is_invalid_query_vector(vector: np.ndarray) -> bool:
        """查询向量无效（全零、含 nan、或范数过小）时无法做向量检索，应走关键词回退。"""
        if vector is None or len(vector) == 0:
            return True
        try:
            if np.any(np.isnan(vector)):
                return True
            if np.all(vector == 0):
                return True
            # 范数过小说明模型输出异常，避免误匹配大量结果
            norm = float(np.linalg.norm(vector))
            if norm < 1e-6:
                return True
            return False
        except Exception:
            return True

    def calculate_dynamic_threshold(self, query: str, query_vector_json: str) -> float:
        """
        计算动态阈值

        根据查询特征动态调整相似度阈值，提高搜索精度。
        短查询使用更高阈值，复杂查询使用较低阈值。

        Args:
            query: 搜索查询
            query_vector_json: 查询向量JSON字符串（未使用，保留接口兼容性）

        Returns:
            float: 动态阈值 (0.1-0.9)
        """
        # 基础阈值（默认 55%），再按查询长度/复杂度微调
        base_threshold = DEFAULT_THRESHOLD

        # 根据查询长度调整阈值
        query_length = len(query.strip())
        if query_length <= 2:  # 短查询，提高阈值
            length_factor = 0.1
        elif query_length <= 5:  # 中等查询
            length_factor = 0.05
        else:  # 长查询，降低阈值
            length_factor = 0.0

        # 根据查询复杂度调整阈值
        word_count = len(query.split())
        if word_count >= 3:  # 复杂查询
            complexity_factor = -0.05
        else:
            complexity_factor = 0.0

        # 根据查询类型调整阈值
        has_numbers = any(char.isdigit() for char in query)
        has_special = any(char in '!@#$%^&*()' for char in query)

        if has_numbers or has_special:  # 精确查询，提高阈值
            precision_factor = 0.05
        else:
            precision_factor = 0.0

        # 计算最终阈值
        dynamic_threshold = base_threshold + length_factor + complexity_factor + precision_factor

        # 确保阈值在合理范围内
        return max(0.1, min(0.9, dynamic_threshold))

    def _classify_query(self, query: str) -> str:
        """
        粗略判断查询类型：
        - simple_entity: 短中文实体词（2-6 个汉字、无空格）
        - keyword_phrase: 一般长度关键词/短语
        - long_query: 较长或复杂查询
        """
        if not query:
            return "keyword_phrase"
        q = query.strip()
        # 全是中文且长度在 2-6 之间，视为实体
        if 2 <= len(q) <= 6 and all("\u4e00" <= ch <= "\u9fff" for ch in q):
            return "simple_entity"
        if len(q) > 20:
            return "long_query"
        return "keyword_phrase"

    @staticmethod
    def _candidate_pool_size(page: int, limit: int, *, factor: int = 5, min_cap: int = 50, max_cap: int = 200) -> int:
        """
        计算候选池大小（用于顶层 search 的 lexical/semantic 候选获取）。

        目标：既能覆盖当前请求页码的切片，又避免随 API limit 放大导致 DB/应用层开销失控。
        """
        end = max(1, int(page)) * max(1, int(limit))
        desired = end * max(1, int(factor))
        return max(min_cap, min(max_cap, desired))

    async def hybrid_search_articles(
        self,
        query_vector_json: str,
        sort_by: str,
        page: int,
        limit: int,
        query: str = "",
        max_items: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        混合搜索文章（优化版：10%文章级 + 90%片段级）

        结合标题、内容和最佳片段的相似度，使用优化的权重分配。

        Args:
            query_vector_json: 查询向量JSON字符串
            sort_by: 排序方式
            page: 页码
            limit: 每页数量
            query: 原始查询字符串

        Returns:
            Dict[str, Any]: 搜索结果
        """
        offset = (page - 1) * limit

        # 计算动态阈值
        dynamic_threshold = self.calculate_dynamic_threshold(query, query_vector_json)
        adjusted_threshold = dynamic_threshold

        # 过滤掉过短的段落
        keyword_length = len(query.strip()) if query else 0
        min_segment_length = max(3, keyword_length)

        # 有正文：按动态阈值；无正文：仅当标题与查询相似度 >= TITLE_ONLY_MIN_SIMILARITY 时保留（标题即“邱华栋”可搜到，“上头像”等泛匹配排除）
        sql = f"""
            WITH all_segments AS (
                -- 标题作为特殊片段（权重更高）
                SELECT
                    av.projectitem_id,
                    0 as segment_index,
                    av.title_text as segment_text,
                    av.title_vector as segment_vector,
                    1.0 as confidence_score,
                    'title' as segment_type,
                    1.2 as segment_weight  -- 标题片段权重更高
                FROM article_vectors av
                WHERE av.title_vector IS NOT NULL
                AND av.projectitem_id IN (
                    SELECT DISTINCT av2.projectitem_id FROM article_vectors av2
                    LEFT JOIN projectitem pi2 ON av2.projectitem_id = pi2.id
                    WHERE pi2.status = 1
                )

                UNION ALL

                -- 内容片段
                SELECT
                    av.projectitem_id,
                    csv.segment_index,
                    csv.segment_text,
                    csv.segment_vector,
                    csv.confidence_score,
                    'content' as segment_type,
                    1.0 as segment_weight  -- 内容片段标准权重
                FROM article_vectors av
                JOIN content_segment_vectors csv ON av.id = csv.article_vector_id
                LEFT JOIN projectitem pi ON av.projectitem_id = pi.id
                WHERE pi.status = 1
                AND csv.confidence_score >= 0.8
                AND LENGTH(TRIM(csv.segment_text)) >= {min_segment_length}
            ),
            best_segments AS (
                -- 选择每篇文章中相似度最高的片段
                SELECT DISTINCT ON (projectitem_id)
                    projectitem_id,
                    segment_text,
                    segment_type,
                    (1 - (segment_vector <=> '{query_vector_json}'::vector)) as segment_similarity,
                    segment_weight
                FROM all_segments
                WHERE (1 - (segment_vector <=> '{query_vector_json}'::vector)) >= {adjusted_threshold}
                ORDER BY projectitem_id, (1 - (segment_vector <=> '{query_vector_json}'::vector)) DESC
            ),
            article_scores AS (
                -- 文章级相似度（仅作为参考，权重很低）
                SELECT
                    av.projectitem_id,
                    (1 - (av.title_vector <=> '{query_vector_json}'::vector)) * 0.3 +
                    (1 - (av.content_vector <=> '{query_vector_json}'::vector)) * 0.7 as article_similarity
                FROM article_vectors av
                LEFT JOIN projectitem pi ON av.projectitem_id = pi.id
                WHERE pi.status = 1
                AND av.title_vector IS NOT NULL
                AND av.content_vector IS NOT NULL
            ),
            ranked AS (
                SELECT
                    bs.projectitem_id as id,
                    pi.name as title,
                    pi.comment as content,
                    u.name as author,
                    pi.createtime,
                    (COALESCE(art.article_similarity, 0) * 0.1 + bs.segment_similarity * 0.9) as relevance_score,
                    bs.segment_text as best_match_text,
                    bs.segment_type as match_type
                FROM best_segments bs
                LEFT JOIN projectitem pi ON bs.projectitem_id = pi.id
                LEFT JOIN users u ON pi.userid = u.id
                LEFT JOIN article_scores art ON bs.projectitem_id = art.projectitem_id
                WHERE (COALESCE(art.article_similarity, 0) * 0.1 + bs.segment_similarity * 0.9) >= {TITLE_ONLY_MIN_SIMILARITY}
            )
            SELECT id, title, content, author, createtime, relevance_score, best_match_text, match_type
            FROM ranked
            ORDER BY relevance_score DESC
            LIMIT {{batch_limit}} OFFSET {{batch_offset}}
        """

        # 过量拉取再过滤，保证每页返回固定条数：每批取 batch_size 条，过滤后累积；拉取到无更多数据为止，用实际有效条数作 total
        # batch_size 上限用于避免外部传入较大 limit 时 DB 批量拉取过大
        batch_size = max(min(limit * 5, 250), 50)
        all_valid: List[Dict[str, Any]] = []
        batch_offset = 0

        while True:
            batch_sql = sql.replace("{batch_limit}", str(batch_size)).replace("{batch_offset}", str(batch_offset))
            result = await self.session.exec(text(batch_sql))
            batch_items = result.fetchall()
            if not batch_items:
                break
            formatted_batch = [self._format_hybrid_article_result(row) for row in batch_items]
            for x in formatted_batch:
                if (x.get("content") or "").strip() or self._safe_float(x.get("relevance_score"), 0) >= TITLE_ONLY_MIN_SIMILARITY:
                    all_valid.append(x)
                    if max_items is not None and len(all_valid) >= max_items:
                        break
            if max_items is not None and len(all_valid) >= max_items:
                break
            if len(batch_items) < batch_size:
                break
            batch_offset += batch_size

        items_for_page = all_valid[(page - 1) * limit : page * limit]
        # 若 max_items 生效，则 total 代表“候选池内的有效条目数”，并不一定是全量真实匹配数
        total = len(all_valid)

        self._clamp_items_relevance(items_for_page, dynamic_threshold)
        return {
            "items": items_for_page,
            "total": total,
            "has_more": (page * limit) < total,
            "dynamic_threshold": self._safe_float(dynamic_threshold),
            "search_strategy": "hybrid_optimized"
        }

    async def search(self, query: str, search_type: str = "all",
                    sort_by: str = "relevance", page: int = 1, limit: int = 10) -> Dict[str, Any]:
        """
        执行搜索

        根据搜索类型执行相应的搜索策略，返回格式化的搜索结果。

        Args:
            query: 搜索查询
            search_type: 搜索类型 (all/articles/comments)
            sort_by: 排序方式 (relevance/date/popularity)
            page: 页码
            limit: 每页结果数

        Returns:
            Dict[str, Any]: 搜索结果，包含items、total、has_more等信息
        """
        start_time = time.time()

        try:
            # 1. 将查询文本向量化（如果向量无效，语义通道会自动降级为仅关键词）
            query_vector = await self.vectorization_service.vectorize_text(query)
            query_vector_json: str = ""
            vector_valid = not self._is_invalid_query_vector(query_vector)
            if vector_valid:
                query_vector_json = self._vector_to_json(query_vector)
            else:
                logger.warning("查询向量无效（全零/含 nan/范数过小），本次仅使用关键词检索: query=%s", query[:50] if query else "")

            query_type = self._classify_query(query or "")
            results: Dict[str, Any]

            # 2. 文章搜索：同时使用关键词 + 语义通道，再在应用层合并
            if search_type == "articles":
                lexical_n = self._candidate_pool_size(page, limit, factor=5, min_cap=50, max_cap=200)
                semantic_n = self._candidate_pool_size(page, limit, factor=5, min_cap=50, max_cap=200)
                # 关键词通道：始终启用，保证包含查询串的文章尽量被召回
                kw_results = await self._keyword_search_articles(query, page=1, limit=lexical_n)
                # 语义通道：仅在向量有效时启用；否则为空
                if vector_valid:
                    sem_results = await self.hybrid_search_articles(
                        query_vector_json,
                        sort_by,
                        page=1,
                        limit=semantic_n,
                        query=query,
                        max_items=semantic_n,
                    )
                else:
                    sem_results = {"items": [], "total": 0, "has_more": False, "dynamic_threshold": DEFAULT_THRESHOLD}

                merged_items: List[Dict[str, Any]] = []
                by_id: Dict[Any, Dict[str, Any]] = {}

                # 为关键词结果打一个粗略 lexical_score
                for it in kw_results.get("items", []):
                    text = ((it.get("title") or "") + " " + (it.get("content") or "") + " " + (it.get("author") or "")).strip()
                    contains = 1.0 if query and query in text else 0.5
                    item = dict(it)
                    item["lexical_score"] = contains
                    # 关键词候选不应“冒充”语义命中；语义分只来自语义通道
                    item["semantic_score"] = 0.0
                    by_id[item["id"]] = item

                # 合并语义结果
                for it in sem_results.get("items", []):
                    existing = by_id.get(it["id"])
                    if existing:
                        # 保留更高的语义分
                        existing["semantic_score"] = max(
                            existing.get("semantic_score", 0.0),
                            float(it.get("relevance_score") or 0.0),
                        )
                    else:
                        item = dict(it)
                        item["lexical_score"] = 0.0
                        item["semantic_score"] = float(item.get("relevance_score") or 0.0)
                        by_id[item["id"]] = item

                merged_items = list(by_id.values())

                # 简单归一化与加权打分
                if merged_items:
                    max_lex = max(self._safe_float(x.get("lexical_score"), 0.0) for x in merged_items) or 1.0
                    max_sem = max(self._safe_float(x.get("semantic_score"), 0.0) for x in merged_items) or 1.0
                else:
                    max_lex = max_sem = 1.0

                if query_type == "simple_entity":
                    w_lex, w_sem = 0.7, 0.3
                elif query_type == "long_query":
                    w_lex, w_sem = 0.3, 0.7
                else:
                    w_lex, w_sem = 0.5, 0.5

                for x in merged_items:
                    lex_n = self._safe_float(x.get("lexical_score"), 0.0) / max_lex
                    sem_n = self._safe_float(x.get("semantic_score"), 0.0) / max_sem
                    x["relevance_score"] = w_lex * lex_n + w_sem * sem_n

                merged_items.sort(key=lambda x: self._safe_float(x.get("relevance_score"), 0.0), reverse=True)

                total = len(merged_items)
                start = (page - 1) * limit
                end = page * limit
                page_items = merged_items[start:end]

                # 兜底：若第一页结果中没有任何真正包含查询串的文章，则将包含查询串的关键词命中提前插入
                if page == 1 and query:
                    def contains_query(it: Dict[str, Any]) -> bool:
                        text = ((it.get("title") or "") + " " + (it.get("content") or "") + " " + (it.get("author") or "")).strip()
                        return query in text

                    if not any(contains_query(it) for it in page_items):
                        keyword_hits = [it for it in merged_items if contains_query(it)]
                        if keyword_hits:
                            # 将前若干关键词命中放到最前面，再补满 limit
                            front = keyword_hits[: min(len(keyword_hits), limit)]
                            remaining = [it for it in merged_items if it not in front]
                            page_items = (front + remaining)[:limit]

                self._clamp_items_relevance(page_items, DEFAULT_THRESHOLD)
                results = {
                    "items": page_items,
                    "total": total,
                    "has_more": end < total,
                    "dynamic_threshold": DEFAULT_THRESHOLD,
                    "search_strategy": "hybrid_lexical_semantic_v2",
                }

            elif search_type == "comments":
                # 评论：保持现有向量搜索为主，向量无效时用关键词回退
                if vector_valid:
                    results = await self._search_comments(query_vector_json, sort_by, page, limit, query)
                    results["dynamic_threshold"] = DEFAULT_THRESHOLD
                else:
                    results = await self._keyword_search_comments(query, page, limit)

            else:
                # all：文章用新方案，评论按上面逻辑搜索，再合并后做分页
                lexical_n = self._candidate_pool_size(page, limit, factor=5, min_cap=50, max_cap=200)
                semantic_n = self._candidate_pool_size(page, limit, factor=5, min_cap=50, max_cap=200)
                comment_n = self._candidate_pool_size(page, limit, factor=3, min_cap=30, max_cap=200)
                # 先搜索文章
                kw_results = await self._keyword_search_articles(query, page=1, limit=lexical_n)
                if vector_valid:
                    sem_results = await self.hybrid_search_articles(
                        query_vector_json,
                        sort_by,
                        page=1,
                        limit=semantic_n,
                        query=query,
                        max_items=semantic_n,
                    )
                else:
                    sem_results = {"items": [], "total": 0, "has_more": False, "dynamic_threshold": DEFAULT_THRESHOLD}

                merged_items: List[Dict[str, Any]] = []
                by_id: Dict[Any, Dict[str, Any]] = {}
                for it in kw_results.get("items", []):
                    item = dict(it)
                    text = ((item.get("title") or "") + " " + (item.get("content") or "") + " " + (item.get("author") or "")).strip()
                    contains = 1.0 if query and query in text else 0.5
                    item["lexical_score"] = contains
                    item["semantic_score"] = 0.0
                    by_id[item["id"]] = item
                for it in sem_results.get("items", []):
                    existing = by_id.get(it["id"])
                    if existing:
                        existing["semantic_score"] = max(
                            existing.get("semantic_score", 0.0),
                            float(it.get("relevance_score") or 0.0),
                        )
                    else:
                        item = dict(it)
                        item["lexical_score"] = 0.0
                        item["semantic_score"] = float(item.get("relevance_score") or 0.0)
                        by_id[item["id"]] = item
                merged_items = list(by_id.values())
                if merged_items:
                    max_lex = max(self._safe_float(x.get("lexical_score"), 0.0) for x in merged_items) or 1.0
                    max_sem = max(self._safe_float(x.get("semantic_score"), 0.0) for x in merged_items) or 1.0
                else:
                    max_lex = max_sem = 1.0
                if query_type == "simple_entity":
                    w_lex, w_sem = 0.7, 0.3
                elif query_type == "long_query":
                    w_lex, w_sem = 0.3, 0.7
                else:
                    w_lex, w_sem = 0.5, 0.5
                for x in merged_items:
                    lex_n = self._safe_float(x.get("lexical_score"), 0.0) / max_lex
                    sem_n = self._safe_float(x.get("semantic_score"), 0.0) / max_sem
                    x["relevance_score"] = w_lex * lex_n + w_sem * sem_n
                merged_items.sort(key=lambda x: self._safe_float(x.get("relevance_score"), 0.0), reverse=True)

                # 评论结果：拉取前若干条作为候选池，再与文章结果一起分页
                if vector_valid:
                    comment_results = await self._search_comments(query_vector_json, sort_by, page=1, limit=comment_n, query=query)
                else:
                    comment_results = await self._keyword_search_comments(query, page=1, limit=comment_n)

                all_items = merged_items + comment_results.get("items", [])
                all_items.sort(key=lambda x: self._safe_float(x.get("relevance_score", 0.0)), reverse=True)

                total_count = len(all_items)
                start = (page - 1) * limit
                end = page * limit
                page_items = all_items[start:end]
                self._clamp_items_relevance(page_items, DEFAULT_THRESHOLD)
                results = {
                    "items": page_items,
                    "total": total_count,
                    "has_more": end < total_count,
                    "dynamic_threshold": DEFAULT_THRESHOLD,
                    "search_strategy": "hybrid_lexical_semantic_v2"
                }

            # 3. 计算搜索时间
            search_time = self._safe_float(round(time.time() - start_time, 3))
            return {
                "items": results.get("items", []),
                "total": results.get("total", 0),
                "has_more": results.get("has_more", False),
                "search_time": search_time,
                "dynamic_threshold": self._safe_float(results.get("dynamic_threshold", DEFAULT_THRESHOLD))
            }

        except Exception as e:
            logger.error(f"搜索服务错误: {e}")

            # 返回空结果而不是抛出异常
            return {
                "items": [],
                "total": 0,
                "has_more": False,
                "search_time": self._safe_float(round(time.time() - start_time, 3)),
                "error": str(e)
            }

    async def _search_articles(self, query_vector_json: str, sort_by: str, page: int, limit: int, query: str = "") -> Dict[str, Any]:
        """搜索文章"""
        offset = (page - 1) * limit

        # 计算动态阈值
        dynamic_threshold = self.calculate_dynamic_threshold(query, query_vector_json)

        # 使用纯语义搜索，动态阈值范围为10%-90%
        # 直接使用动态阈值，不再进一步调整
        adjusted_threshold = dynamic_threshold

        # 优化后的SQL：直接使用内容段相似度，避免UNION ALL和复杂GROUP BY
        # 使用DISTINCT ON去重，确保每篇文章只返回最高相似度的记录
        # 过滤掉过短的段落：长度小于3个字符或小于关键词长度的段落
        keyword_length = len(query.strip()) if query else 0
        min_segment_length = max(3, keyword_length)

        sql = f"""
            SELECT DISTINCT ON (av.projectitem_id)
                av.projectitem_id as id,
                pi.name as title,
                pi.comment as content,
                u.name as author,
                pi.createtime,
                (1 - (csv.segment_vector <=> '{query_vector_json}'::vector)) as relevance_score
            FROM article_vectors av
            LEFT JOIN projectitem pi ON av.projectitem_id = pi.id
            LEFT JOIN users u ON pi.userid = u.id
            LEFT JOIN content_segment_vectors csv ON av.id = csv.article_vector_id
            WHERE pi.status = 1
            AND pi.comment IS NOT NULL AND LENGTH(TRIM(pi.comment)) > 0
            AND (1 - (csv.segment_vector <=> '{query_vector_json}'::vector)) >= {adjusted_threshold}
            AND LENGTH(TRIM(csv.segment_text)) >= {min_segment_length}
            ORDER BY av.projectitem_id, (1 - (csv.segment_vector <=> '{query_vector_json}'::vector)) DESC
            LIMIT {limit} OFFSET {offset}
            """

        result = await self.session.exec(text(sql))
        items = result.fetchall()

        # 获取总数 - 简化查询，使用相同的过滤条件
        count_sql = f"""
        SELECT COUNT(DISTINCT av.projectitem_id)
        FROM article_vectors av
        LEFT JOIN projectitem pi ON av.projectitem_id = pi.id
        LEFT JOIN content_segment_vectors csv ON av.id = csv.article_vector_id
        WHERE pi.status = 1
        AND pi.comment IS NOT NULL AND LENGTH(TRIM(pi.comment)) > 0
        AND (1 - (csv.segment_vector <=> '{query_vector_json}'::vector)) >= {adjusted_threshold}
        AND LENGTH(TRIM(csv.segment_text)) >= {min_segment_length}
        """
        count_result = await self.session.exec(text(count_sql))
        total = count_result.fetchone()[0]

        formatted = [self._format_article_result(item) for item in items]
        self._clamp_items_relevance(formatted, dynamic_threshold)
        return {
            "items": formatted,
            "total": total,
            "has_more": (offset + len(items)) < total,
            "dynamic_threshold": self._safe_float(dynamic_threshold)
        }


    async def _search_comments(self, query_vector_json: str, sort_by: str, page: int, limit: int, query: str = "") -> Dict[str, Any]:
        """搜索评论"""
        offset = (page - 1) * limit

        # 使用向量搜索
        sql = f"""
            SELECT
                p.id,
                p.subject as title,
                p.content,
                u.name as author,
                p.posttime,
                (1 - (cv.content_vector <=> '{query_vector_json}'::vector)) as relevance_score,
                p.projectitemid as projectitem_id
            FROM comment_vectors cv
            LEFT JOIN post p ON cv.post_id = p.id
            LEFT JOIN users u ON p.userid = u.id
            WHERE p.status = 1
            ORDER BY relevance_score DESC
            LIMIT {limit} OFFSET {offset}
            """

        result = await self.session.exec(text(sql))
        items = result.fetchall()

        # 获取总数
        count_sql = """
        SELECT COUNT(*)
        FROM comment_vectors cv
        LEFT JOIN post p ON cv.post_id = p.id
        WHERE p.status = 1
        """
        count_result = await self.session.exec(text(count_sql))
        total = count_result.fetchone()[0]

        return {
            "items": [self._format_comment_result(item) for item in items],
            "total": total,
            "has_more": (offset + len(items)) < total
        }

    async def _keyword_search_articles(self, query: str, page: int, limit: int) -> Dict[str, Any]:
        """关键词搜索：标题/内容/作者名 ILIKE 匹配（向量无效时回退，或第一页与向量结果合并）。"""
        if not query or not query.strip():
            return {"items": [], "total": 0, "has_more": False, "dynamic_threshold": DEFAULT_THRESHOLD}
        offset = (page - 1) * limit
        pattern = f"%{self._escape_like_pattern(query.strip())}%"
        sql = text("""
            SELECT pi.id, pi.name as title, pi.comment as content, u.name as author, pi.createtime, 1.0 as relevance_score
            FROM projectitem pi
            LEFT JOIN users u ON pi.userid = u.id
            WHERE pi.status = 1 AND (pi.name ILIKE :pat ESCAPE '\\' OR pi.comment ILIKE :pat ESCAPE '\\' OR u.name ILIKE :pat ESCAPE '\\')
            ORDER BY pi.createtime DESC
            LIMIT :lim OFFSET :off
        """)
        result = await self.session.execute(sql, {"pat": pattern, "lim": limit, "off": offset})
        items = result.fetchall()
        count_sql = text("""
            SELECT COUNT(*) FROM projectitem pi
            LEFT JOIN users u ON pi.userid = u.id
            WHERE pi.status = 1 AND (pi.name ILIKE :pat ESCAPE '\\' OR pi.comment ILIKE :pat ESCAPE '\\' OR u.name ILIKE :pat ESCAPE '\\')
        """)
        count_result = await self.session.execute(count_sql, {"pat": pattern})
        total = count_result.fetchone()[0]
        return {
            "items": [self._format_article_result(item) for item in items],
            "total": total,
            "has_more": (offset + len(items)) < total,
            "dynamic_threshold": DEFAULT_THRESHOLD
        }

    async def _keyword_search_comments(self, query: str, page: int, limit: int) -> Dict[str, Any]:
        """关键词搜索：标题/内容/作者名 ILIKE 匹配（向量无效时回退）。"""
        if not query or not query.strip():
            return {"items": [], "total": 0, "has_more": False}
        offset = (page - 1) * limit
        pattern = f"%{self._escape_like_pattern(query.strip())}%"
        sql = text("""
            SELECT p.id, p.subject as title, p.content, u.name as author, p.posttime, 1.0 as relevance_score,
                   p.projectitemid as projectitem_id
            FROM post p
            LEFT JOIN users u ON p.userid = u.id
            WHERE p.status = 1 AND (p.subject ILIKE :pat ESCAPE '\\' OR p.content ILIKE :pat ESCAPE '\\' OR u.name ILIKE :pat ESCAPE '\\')
            ORDER BY p.posttime DESC
            LIMIT :lim OFFSET :off
        """)
        result = await self.session.execute(sql, {"pat": pattern, "lim": limit, "off": offset})
        items = result.fetchall()
        count_sql = text("""
            SELECT COUNT(*) FROM post p
            LEFT JOIN users u ON p.userid = u.id
            WHERE p.status = 1 AND (p.subject ILIKE :pat ESCAPE '\\' OR p.content ILIKE :pat ESCAPE '\\' OR u.name ILIKE :pat ESCAPE '\\')
        """)
        count_result = await self.session.execute(count_sql, {"pat": pattern})
        total = count_result.fetchone()[0]
        return {
            "items": [self._format_comment_result(item) for item in items],
            "total": total,
            "has_more": (offset + len(items)) < total
        }

    def _vector_to_json(self, vector: np.ndarray) -> str:
        """
        将向量转换为JSON字符串

        Args:
            vector: numpy向量数组

        Returns:
            str: JSON格式的向量字符串
        """
        return json.dumps(vector.tolist())

    def _json_to_vector(self, json_str: str) -> np.ndarray:
        """
        将JSON字符串转换为向量

        Args:
            json_str: JSON格式的向量字符串

        Returns:
            np.ndarray: 向量数组，失败时返回零向量
        """
        try:
            return np.array(json.loads(json_str))
        except Exception:
            return np.zeros(384)

    def _format_article_result(self, item: tuple) -> Dict[str, Any]:
        """
        格式化文章搜索结果

        Args:
            item: 数据库查询结果元组

        Returns:
            Dict[str, Any]: 格式化的文章搜索结果
        """
        return {
            "id": item[0],
            "title": item[1],
            "content": item[2],
            "author": item[3],
            "created_at": item[4].isoformat() if item[4] else None,
            "relevance_score": self._row_relevance(item),
            "type": "article"
        }

    def _format_hybrid_article_result(self, item: tuple) -> Dict[str, Any]:
        """
        格式化混合搜索文章结果

        Args:
            item: 数据库查询结果元组 (id, title, content, author, createtime, relevance_score, best_match_text, match_type)

        Returns:
            Dict[str, Any]: 格式化的混合搜索文章结果
        """
        return {
            "id": item[0],
            "title": item[1],
            "content": item[2],
            "author": item[3],
            "created_at": item[4].isoformat() if item[4] else None,
            "relevance_score": self._row_relevance(item),
            "best_match_text": item[6] if len(item) > 6 else None,
            "match_type": item[7] if len(item) > 7 else "content",
            "type": "article",
            "search_strategy": "hybrid_optimized"
        }

    def _format_comment_result(self, item: tuple) -> Dict[str, Any]:
        """
        格式化评论搜索结果

        Args:
            item: 数据库查询结果元组，前 6 列为
                id, title, content, author, createtime/posttime, relevance_score；
                可选第 7 列为所属博文 projectitem_id（留言本为 0）。

        Returns:
            Dict[str, Any]: 格式化的评论搜索结果
        """
        projectitem_id = item[6] if len(item) > 6 else None
        return {
            "id": item[0],
            "title": item[1],
            "content": item[2],
            "author": item[3],
            "created_at": item[4].isoformat() if item[4] else None,
            "relevance_score": self._row_relevance(item),
            "type": "comment",
            "projectitem_id": projectitem_id,
            "article_id": projectitem_id,
        }
