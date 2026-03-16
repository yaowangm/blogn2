#!/usr/bin/env python3
"""
博客文章列表加载性能测速脚本

用于衡量博客列表 API 的加载速度，对比首页与末页（大 offset）的响应时间，
帮助定位性能瓶颈（如数据库 OFFSET 查询过慢）。

使用前请确保服务已启动：uvicorn 或 python -m src.main
使用示例：
    python scripts/benchmark_blog_list.py
    python scripts/benchmark_blog_list.py --base-url http://localhost:8000 --blog-id 12 --last-page 24
    python scripts/benchmark_blog_list.py --iterations 5 --no-cache  # 每次请求带缓存绕过参数
"""

import argparse
import statistics
import sys
import time
from pathlib import Path

import requests

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def measure_api(
    base_url: str,
    blog_id: int,
    page: int,
    limit: int = 10,
    folderid: str | None = None,
    no_cache: bool = False,
) -> tuple[float, int, dict | None]:
    """请求 GET /api/projects/{blog_id}/posts，返回 (耗时秒, 状态码, 响应 JSON)。"""
    params = {"page": page, "limit": limit, "type": "original"}
    if folderid is not None:
        params["folderid"] = folderid
    if no_cache:
        params["_t"] = str(time.time())
    url = f"{base_url.rstrip('/')}/api/projects/{blog_id}/posts"
    start = time.perf_counter()
    try:
        r = requests.get(url, params=params, timeout=30)
        elapsed = time.perf_counter() - start
        return elapsed, r.status_code, r.json() if r.status_code == 200 else None
    except Exception:
        return time.perf_counter() - start, -1, None


def measure_page_times(
    base_url: str,
    blog_id: int,
    page: int,
    limit: int = 10,
    iterations: int = 3,
    no_cache: bool = False,
) -> list[float]:
    """多次请求同一页，返回每次耗时（秒）列表。"""
    times: list[float] = []
    for _ in range(iterations):
        elapsed, status, _ = measure_api(base_url, blog_id, page, limit, no_cache=no_cache)
        if status == 200:
            times.append(elapsed)
    return times


def main():
    parser = argparse.ArgumentParser(description="博客文章列表 API 性能测速")
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="服务根地址 (默认: http://localhost:8000)",
    )
    parser.add_argument(
        "--blog-id",
        type=int,
        default=12,
        help="博客项目 ID (默认: 12)",
    )
    parser.add_argument(
        "--last-page",
        type=int,
        default=24,
        help="用于测速的“末页”页码 (默认: 24)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="每页条数 (默认: 10)",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=3,
        help="每页重复请求次数 (默认: 3)",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="每次请求带随机参数以尽量绕过缓存，观察冷请求耗时",
    )
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    blog_id = args.blog_id
    last_page = args.last_page
    limit = args.limit
    iterations = args.iterations
    no_cache = args.no_cache

    print("=" * 60)
    print("博客文章列表 API 性能测速")
    print("=" * 60)
    print(f"  接口: GET {base_url}/api/projects/{{id}}/posts")
    print(f"  博客 ID: {blog_id}")
    print(f"  每页条数: {limit}")
    print(f"  对比页码: 第 1 页 vs 第 {last_page} 页")
    print(f"  每页请求次数: {iterations}")
    print(f"  绕过缓存: {'是' if no_cache else '否'}")
    print()

    elapsed_probe, status, data = measure_api(base_url, blog_id, 1, limit)
    if status != 200 or not data:
        print(f"❌ 探测请求失败: status={status}, 请确认服务已启动且 blog_id={blog_id} 有效")
        sys.exit(1)
    total = data.get("total", 0)
    total_pages = (total + limit - 1) // limit if total else 0
    print(f"  当前总文章数: {total}")
    print(f"  实际总页数: {total_pages}")
    if last_page > total_pages and total_pages > 0:
        print(f"  ⚠ 将使用实际末页 {total_pages} 代替 --last-page {last_page}")
        last_page = total_pages
    print()

    print("  正在测速 第 1 页 ...")
    times_first = measure_page_times(base_url, blog_id, 1, limit, iterations, no_cache)
    if not times_first:
        print("❌ 第 1 页所有请求均失败")
        sys.exit(1)
    avg_first = statistics.mean(times_first)
    print(f"  第 1 页: 平均 {avg_first*1000:.1f} ms  (min={min(times_first)*1000:.1f}, max={max(times_first)*1000:.1f})")

    print(f"  正在测速 第 {last_page} 页 ...")
    times_last = measure_page_times(base_url, blog_id, last_page, limit, iterations, no_cache)
    if not times_last:
        print(f"❌ 第 {last_page} 页所有请求均失败")
        sys.exit(1)
    avg_last = statistics.mean(times_last)
    print(f"  第 {last_page} 页: 平均 {avg_last*1000:.1f} ms  (min={min(times_last)*1000:.1f}, max={max(times_last)*1000:.1f})")

    # 对比
    print()
    print("  结论:")
    ratio = avg_last / avg_first if avg_first > 0 else 0
    print(f"    末页平均耗时 / 首页平均耗时 ≈ {ratio:.2f}x")
    if ratio > 2:
        print("    ⚠ 末页明显更慢，建议检查：")
        print("      1. 数据库分页是否使用大 OFFSET（ORDER BY createtime DESC OFFSET n LIMIT 10）")
        print("      2. projectitem 表是否有 (projectid, status, createtime) 复合索引")
        print("      3. 是否可改为游标/keyset 分页（基于 createtime 或 id）")
    else:
        print("    首页与末页耗时接近，或差异在正常范围内。")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
