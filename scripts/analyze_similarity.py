#!/usr/bin/env python3
"""
文章相似度分析脚本

用法:
    python analyze_similarity.py "关键词" "{1,2,3,4,5}"

功能:
    - 计算关键词与文章标题的相似度
    - 计算关键词与文章每个内容段的相似度
    - 计算关键词与文章的整体相似度
    - 使用sentence-transformers模型进行向量化
"""

import asyncio
import sys
import argparse
import json
from typing import List, Dict, Any, Tuple
import numpy as np
from sqlmodel import create_engine, text
from dotenv import load_dotenv
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.vectorization_service import BERTVectorizationService

# 加载环境变量
load_dotenv()

class SimilarityAnalyzer:
    def __init__(self, database_url: str):
        """初始化相似度分析器"""
        self.engine = create_engine(database_url)
        self.vectorization_service = None
        
    async def load_model(self):
        """加载向量化服务"""
        print("🔄 正在加载BERT模型...")
        self.vectorization_service = BERTVectorizationService()
        print("✅ BERT模型加载成功")
        
    async def vectorize_text(self, text: str) -> np.ndarray:
        """向量化文本"""
        if self.vectorization_service is None:
            raise ValueError("向量化服务未加载，请先调用load_model()")
        return await self.vectorization_service.vectorize_text(text)
    
    def calculate_similarity(self, vector1: np.ndarray, vector2: np.ndarray) -> float:
        """计算两个向量的余弦相似度"""
        # 计算余弦相似度
        dot_product = np.dot(vector1, vector2)
        norm1 = np.linalg.norm(vector1)
        norm2 = np.linalg.norm(vector2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        similarity = dot_product / (norm1 * norm2)
        return float(similarity)
    
    def get_article_data(self, article_ids: List[int]) -> List[Dict[str, Any]]:
        """获取文章数据"""
        with self.engine.connect() as conn:
            # 获取文章基本信息
            articles_sql = f"""
                SELECT 
                    pi.id,
                    pi.name as title,
                    pi.comment as content,
                    u.name as author,
                    pi.createtime
                FROM projectitem pi
                LEFT JOIN users u ON pi.userid = u.id
                WHERE pi.id = ANY(ARRAY{article_ids})
                AND pi.status = 1
                ORDER BY pi.id
            """
            
            result = conn.execute(text(articles_sql))
            articles = []
            for row in result:
                articles.append({
                    'id': row[0],
                    'title': row[1] or '',
                    'content': row[2] or '',
                    'author': row[3] or '',
                    'createtime': row[4]
                })
            
            # 获取文章的内容段
            for article in articles:
                segments_sql = f"""
                    SELECT csv.segment_text, csv.segment_vector
                    FROM article_vectors av
                    LEFT JOIN content_segment_vectors csv ON av.id = csv.article_vector_id
                    WHERE av.projectitem_id = {article['id']}
                    ORDER BY csv.id
                """
                
                result = conn.execute(text(segments_sql))
                segments = []
                for row in result:
                    segments.append({
                        'text': row[0] or '',
                        'vector': row[1]  # 这是存储的向量
                    })
                
                article['segments'] = segments
            
            return articles
    
    async def analyze_article_similarity(self, keyword: str, article: Dict[str, Any]) -> Dict[str, Any]:
        """分析单篇文章与关键词的相似度"""
        print(f"📄 分析文章 {article['id']}: {article['title'][:50]}...")
        
        # 向量化关键词
        keyword_vector = await self.vectorize_text(keyword)
        
        results = {
            'article_id': article['id'],
            'title': article['title'],
            'author': article['author'],
            'keyword': keyword,
            'similarities': {}
        }
        
        # 1. 计算与标题的相似度
        if article['title']:
            title_vector = await self.vectorize_text(article['title'])
            title_similarity = self.calculate_similarity(keyword_vector, title_vector)
            results['similarities']['title'] = {
                'similarity': title_similarity,
                'text': article['title']
            }
            print(f"  📝 标题相似度: {title_similarity:.4f}")
        
        # 2. 计算与每个内容段的相似度
        segment_similarities = []
        segment_results = []
        
        for i, segment in enumerate(article['segments']):
            if segment['text']:
                segment_vector = await self.vectorize_text(segment['text'])
                segment_similarity = self.calculate_similarity(keyword_vector, segment_vector)
                
                # 检查段落是否包含关键词
                contains_keyword = keyword.lower() in segment['text'].lower()
                
                segment_info = {
                    'index': i,
                    'similarity': segment_similarity,
                    'text': segment['text'][:100] + '...' if len(segment['text']) > 100 else segment['text'],
                    'contains_keyword': contains_keyword
                }
                
                segment_similarities.append(segment_similarity)
                segment_results.append(segment_info)
                
                # 标记包含关键词的段落
                keyword_mark = " 🔍" if contains_keyword else ""
                print(f"  📄 段落{i+1}相似度: {segment_similarity:.4f}{keyword_mark}")
        
        # 按相似度从大到小排序段落
        segment_results.sort(key=lambda x: x['similarity'], reverse=True)
        
        # 更新结果中的段落信息（按相似度排序）
        for i, segment_info in enumerate(segment_results):
            results['similarities'][f'segment_{i}'] = {
                'original_index': segment_info['index'],
                'similarity': segment_info['similarity'],
                'text': segment_info['text'],
                'contains_keyword': segment_info['contains_keyword']
            }
        
        # 3. 计算整体相似度（所有段落相似度的最大值）
        if segment_similarities:
            overall_similarity = max(segment_similarities)
            results['similarities']['overall'] = {
                'similarity': overall_similarity,
                'method': 'max_segment_similarity'
            }
            print(f"  🎯 整体相似度: {overall_similarity:.4f}")
        else:
            results['similarities']['overall'] = {
                'similarity': 0.0,
                'method': 'no_segments'
            }
            print(f"  ⚠️  无内容段落")
        
        return results
    
    async def analyze_all_articles(self, keyword: str, article_ids: List[int]) -> Dict[str, Any]:
        """分析所有文章与关键词的相似度"""
        print(f"🔍 开始分析关键词: '{keyword}'")
        print(f"📚 文章ID列表: {article_ids}")
        print("=" * 60)
        
        # 加载模型
        await self.load_model()
        
        # 获取文章数据
        print("📖 获取文章数据...")
        articles = self.get_article_data(article_ids)
        print(f"✅ 找到 {len(articles)} 篇文章")
        
        if not articles:
            print("❌ 没有找到指定的文章")
            return {'error': 'No articles found'}
        
        # 分析每篇文章
        results = {
            'keyword': keyword,
            'article_ids': article_ids,
            'total_articles': len(articles),
            'articles': []
        }
        
        for article in articles:
            article_result = await self.analyze_article_similarity(keyword, article)
            results['articles'].append(article_result)
            print("-" * 40)
        
        # 计算统计信息
        overall_similarities = [
            article['similarities']['overall']['similarity'] 
            for article in results['articles']
        ]
        
        results['statistics'] = {
            'max_similarity': max(overall_similarities) if overall_similarities else 0,
            'min_similarity': min(overall_similarities) if overall_similarities else 0,
            'avg_similarity': sum(overall_similarities) / len(overall_similarities) if overall_similarities else 0,
            'articles_above_0.5': sum(1 for s in overall_similarities if s > 0.5),
            'articles_above_0.3': sum(1 for s in overall_similarities if s > 0.3)
        }
        
        return results

def parse_article_ids(article_ids_str: str) -> List[int]:
    """解析文章ID字符串"""
    try:
        # 移除大括号和空格
        clean_str = article_ids_str.strip('{}').replace(' ', '')
        # 分割并转换为整数
        ids = [int(id_str) for id_str in clean_str.split(',') if id_str]
        return ids
    except ValueError as e:
        raise ValueError(f"无法解析文章ID列表: {article_ids_str}. 请使用格式: {{1,2,3,4,5}}")

async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='分析关键词与文章的相似度')
    parser.add_argument('keyword', help='搜索关键词')
    parser.add_argument('article_ids', help='文章ID列表，格式: {1,2,3,4,5}')
    parser.add_argument('--output', '-o', help='输出文件路径（JSON格式）')
    parser.add_argument('--database-url', help='数据库连接URL')
    
    args = parser.parse_args()
    
    # 解析文章ID
    try:
        article_ids = parse_article_ids(args.article_ids)
    except ValueError as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)
    
    # 获取数据库连接（使用同步连接）
    env_database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/blogn')
    # 将异步URL转换为同步URL
    if '+asyncpg' in env_database_url:
        database_url = env_database_url.replace('+asyncpg', '')
    else:
        database_url = env_database_url
    
    database_url = args.database_url or database_url
    
    # 创建分析器并执行分析
    analyzer = SimilarityAnalyzer(database_url)
    
    try:
        results = await analyzer.analyze_all_articles(args.keyword, article_ids)
        
        # 打印结果摘要
        print("\n" + "=" * 60)
        print("📊 分析结果摘要")
        print("=" * 60)
        print(f"关键词: {results['keyword']}")
        print(f"分析文章数: {results['total_articles']}")
        
        if 'statistics' in results:
            stats = results['statistics']
            print(f"最高相似度: {stats['max_similarity']:.4f}")
            print(f"最低相似度: {stats['min_similarity']:.4f}")
            print(f"平均相似度: {stats['avg_similarity']:.4f}")
            print(f"相似度>0.5的文章: {stats['articles_above_0.5']}")
            print(f"相似度>0.3的文章: {stats['articles_above_0.3']}")
        
        # 按相似度排序显示文章
        print("\n📋 文章相似度排名:")
        articles_with_similarity = [
            (article['article_id'], article['title'], article['similarities']['overall']['similarity'])
            for article in results['articles']
        ]
        articles_with_similarity.sort(key=lambda x: x[2], reverse=True)
        
        for i, (article_id, title, similarity) in enumerate(articles_with_similarity, 1):
            print(f"{i:2d}. ID:{article_id:4d} 相似度:{similarity:.4f} 标题:{title[:50]}...")
        
        # 显示每篇文章的段落相似度排名
        print("\n📄 段落相似度详情:")
        for article in results['articles']:
            print(f"\n文章 {article['article_id']}: {article['title'][:30]}...")
            
            # 获取段落信息并按相似度排序
            segments = []
            for key, value in article['similarities'].items():
                if key.startswith('segment_'):
                    segments.append((int(key.split('_')[1]), value))
            
            segments.sort(key=lambda x: x[1]['similarity'], reverse=True)
            
            print("  段落相似度排名（前10名）:")
            for i, (orig_idx, segment_info) in enumerate(segments[:10], 1):
                keyword_mark = " 🔍" if segment_info.get('contains_keyword', False) else ""
                print(f"    {i:2d}. 原段落{orig_idx+1:2d} 相似度:{segment_info['similarity']:.4f}{keyword_mark} {segment_info['text'][:40]}...")
        
        # 保存结果到文件
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"\n💾 详细结果已保存到: {args.output}")
        
    except Exception as e:
        print(f"❌ 分析过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
