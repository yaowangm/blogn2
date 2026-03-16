#!/usr/bin/env python3
"""
全文检索评估脚本

思路：
- 从项目数据库中采样一定数量的文章
- 从每篇文章的标题/正文中随机抽取若干子串作为查询
- 调用搜索服务（直接使用 HierarchicalSearchService）执行搜索
- 计算简单的 Recall@K / MRR@K 指标，用于比较不同参数或实现版本

使用示例：

    python scripts/eval_fulltext_search.py --limit-articles 200 --queries-per-article 3 --top-k 10
"""

import argparse
import asyncio
import random
import re
from typing import Any, Dict, List, Tuple

from sqlalchemy import text

from src.database import get_async_session
from src.services.model_cache import get_cached_model, initialize_model_cache
from src.services.search_service import HierarchicalSearchService


def strip_html(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"<[^>]+>", " ", text)


def extract_candidate_terms(text: str, max_terms: int = 20) -> List[str]:
    """
    从文本中抽取更贴近“真实搜索”的候选查询：
    - 先按标点/换行切成句子级片段
    - 对中文：使用长度适中的句子或句中子串（4-20 字）
    - 对英文：按空格切词，过滤掉很短的 token
    """
    if not text:
        return []
    text = strip_html(text)
    candidates: List[str] = []

    # 1. 句子级切分（中文标点 + 英文标点）
    sentence_seps = r"[。！？!?;\n]+"
    raw_sentences = re.split(sentence_seps, text)
    sentences = [s.strip() for s in raw_sentences if s and s.strip()]

    # 2. 从句子中抽中文短句 / 子串
    for sent in sentences:
        # 提取该句中的连续中文
        chinese_chars = [ch for ch in sent if "\u4e00" <= ch <= "\u9fff"]
        chinese_text = "".join(chinese_chars)
        if 4 <= len(chinese_text) <= 20:
            # 句子级短句
            candidates.append(chinese_text)
        elif len(chinese_text) > 20:
            # 过长则在其中抽几个 4-12 字的子串
            n = len(chinese_text)
            for _ in range(3):
                if n < 4:
                    break
                l = random.randint(4, min(12, n))
                start = random.randint(0, max(0, n - l))
                sub = chinese_text[start : start + l]
                candidates.append(sub)

    # 3. 英文单词/短语（简单处理）
    words = re.split(r"\s+", text)
    english_tokens = [w.strip() for w in words if len(w.strip()) >= 3 and re.search(r"[A-Za-z]", w)]
    # 单词本身
    candidates.extend(english_tokens[: max_terms])

    # 短语：相邻 2-3 个英文单词
    for i in range(len(english_tokens) - 1):
        phrase = " ".join(english_tokens[i : i + 2])
        candidates.append(phrase)
        if i + 2 < len(english_tokens):
            phrase3 = " ".join(english_tokens[i : i + 3])
            candidates.append(phrase3)

    # 去重并打乱
    uniq = list(dict.fromkeys(candidates))
    random.shuffle(uniq)
    return uniq[:max_terms]


async def sample_articles(session, limit: int) -> List[Tuple[int, str, str]]:
    """
    从 projectitem 中采样文章：只选 status=1 且有正文的条目。
    返回 (id, title, content)
    """
    sql = text(
        """
        SELECT id, name, comment
        FROM projectitem
        WHERE status = 1 AND comment IS NOT NULL AND LENGTH(TRIM(comment)) > 0
        ORDER BY id DESC
        LIMIT :lim
        """
    )
    result = await session.execute(sql, {"lim": limit})
    rows = result.fetchall()
    return [(r[0], r[1] or "", r[2] or "") for r in rows]


async def build_queries_from_articles(
    session, limit_articles: int, queries_per_article: int
) -> List[Tuple[str, int]]:
    """
    从文章中构造 (query, article_id) 列表。
    """
    articles = await sample_articles(session, limit_articles)
    queries: List[Tuple[str, int]] = []
    for aid, title, content in articles:
        text = f"{title} {content}"
        terms = extract_candidate_terms(text, max_terms=queries_per_article * 3)
        if not terms:
            continue
        picked = terms[:queries_per_article]
        for q in picked:
            queries.append((q, aid))
    return queries


def update_metrics(
    metrics: Dict[str, Any],
    query: str,
    target_id: int,
    results: List[Dict[str, Any]],
    k: int,
) -> None:
    """
    更新 Recall@K / MRR@K 指标。
    """
    metrics["total"] += 1
    found_rank = None
    for idx, item in enumerate(results[:k]):
        if int(item.get("id", -1)) == int(target_id):
            found_rank = idx
            break
    if found_rank is not None:
        metrics["hit"] += 1
        metrics["mrr_sum"] += 1.0 / (found_rank + 1)
    else:
        metrics["miss_examples"].append(
            {
                "query": query,
                "target_id": target_id,
                "top_ids": [int(x.get("id", -1)) for x in results[:k]],
            }
        )


async def run_eval(
    limit_articles: int,
    queries_per_article: int,
    top_k: int,
) -> None:
    async for session in get_async_session():
        print(f"采样文章数量: {limit_articles}")
        queries = await build_queries_from_articles(
            session, limit_articles=limit_articles, queries_per_article=queries_per_article
        )
        if not queries:
            print("未能构造任何查询，退出。")
            return
        print(f"构造查询数量: {len(queries)}")
        # 初始化或获取模型缓存
        try:
            vectorization_service = get_cached_model()
        except RuntimeError:
            print("模型未初始化，正在调用 initialize_model_cache() ...")
            vec = await initialize_model_cache()
            if vec is None:
                print("initialize_model_cache() 失败，无法评估全文检索（缺少向量化模型）")
                return
            vectorization_service = vec
        search_service = HierarchicalSearchService(vectorization_service, session)

        metrics: Dict[str, Any] = {
            "total": 0,
            "hit": 0,
            "mrr_sum": 0.0,
            "miss_examples": [],
        }

        for idx, (q, aid) in enumerate(queries, 1):
            result = await search_service.search(
                query=q,
                search_type="articles",
                sort_by="relevance",
                page=1,
                limit=top_k,
            )
            update_metrics(metrics, q, aid, result.get("items", []), top_k)
            if idx % 50 == 0:
                print(f"已评估 {idx}/{len(queries)} 个查询...")

        total = metrics["total"]
        hit = metrics["hit"]
        recall = hit / total if total else 0.0
        mrr = metrics["mrr_sum"] / total if total else 0.0

        print("==== 评估结果 ====")
        print(f"总查询数: {total}")
        print(f"命中数: {hit}")
        print(f"Recall@{top_k}: {recall:.4f}")
        print(f"MRR@{top_k}:    {mrr:.4f}")
        print(f"未命中的示例（最多 5 条）:")
        for miss in metrics["miss_examples"][:5]:
            print(
                f"  query='{miss['query']}' target_id={miss['target_id']} top_ids={miss['top_ids']}"
            )
        break


def main() -> None:
    parser = argparse.ArgumentParser(description="评估全文检索效果（文章搜索）")
    parser.add_argument("--limit-articles", type=int, default=200, help="参与评估的文章数量上限")
    parser.add_argument("--queries-per-article", type=int, default=3, help="每篇文章抽取的查询个数")
    parser.add_argument("--top-k", type=int, default=10, help="计算 Recall / MRR 的 K 值")
    args = parser.parse_args()
    asyncio.run(
        run_eval(
            limit_articles=args.limit_articles,
            queries_per_article=args.queries_per_article,
            top_k=args.top_k,
        )
    )


if __name__ == "__main__":
    main()

