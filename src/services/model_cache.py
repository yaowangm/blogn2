"""
模型缓存服务
在应用启动时预加载BERT模型，避免重复加载
"""

import asyncio
from src.services.vectorization_service import BERTVectorizationService

# 全局模型缓存
_model_cache = None

async def initialize_model_cache():
    """初始化模型缓存"""
    global _model_cache
    if _model_cache is None:
        try:
            print("🔄 正在初始化BERT模型缓存...")
            _model_cache = BERTVectorizationService()
            await _model_cache.load_model()
            print("✅ BERT模型缓存初始化完成")
        except Exception as e:
            print(f"⚠️  BERT模型缓存初始化失败: {e}")
            print("💡 搜索功能将使用传统文本搜索")
            _model_cache = None
    return _model_cache

def get_cached_model():
    """获取缓存的模型"""
    global _model_cache
    if _model_cache is None:
        raise RuntimeError("模型缓存未初始化，请先调用 initialize_model_cache()")
    return _model_cache
