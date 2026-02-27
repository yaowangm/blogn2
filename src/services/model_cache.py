"""
模型缓存服务
使用跨进程共享缓存，确保只有一个进程执行模型初始化
"""

import asyncio
import os
import logging
from typing import Optional
from src.services.vectorization_service import BERTVectorizationService
from src.services.shared_model_cache import get_shared_model_cache

logger = logging.getLogger(__name__)

async def initialize_model_cache() -> Optional[BERTVectorizationService]:
    """初始化模型缓存并返回模型实例。
    在 BERT 的专用 executor 线程中加载模型，使后续 vectorize_text 的 encode 与加载在同一线程执行，
    避免「主线程加载、子线程 encode」的跨线程使用导致本地返回零向量、与 Docker 行为不一致。"""
    try:
        logger.info(f"进程 {os.getpid()} 正在初始化BERT模型缓存...")
        
        shared_cache = get_shared_model_cache()
        
        from src.config.model import get_model_name, get_model_path
        model_name = get_model_name()
        model_path = get_model_path()
        
        # 在 BERT 专用 executor 线程中初始化，与后续 vectorize_text 的 encode 同线程，保证本地/Docker 一致
        loop = asyncio.get_event_loop()
        executor = BERTVectorizationService._get_executor()
        success = await loop.run_in_executor(
            executor,
            lambda: shared_cache.initialize_model(model_name, model_path),
        )
        
        if success:
            # 创建BERTVectorizationService实例，使用共享模型
            model_cache = BERTVectorizationService()
            # 直接设置共享的模型，跳过加载过程
            model_cache._set_shared_model(shared_cache.get_model())
            logger.info(f"进程 {os.getpid()} BERT模型缓存初始化完成")
            return model_cache
        else:
            logger.warning(f"进程 {os.getpid()} BERT模型缓存初始化失败")
            return None
            
    except Exception as e:
        logger.error(f"进程 {os.getpid()} BERT模型缓存初始化失败: {e}")
        logger.info("搜索功能将使用传统文本搜索")
        return None

def get_cached_model() -> BERTVectorizationService:
    """
    获取缓存的模型（从共享缓存获取）
    
    Returns:
        BERTVectorizationService: 缓存的模型实例
    """
    shared_cache = get_shared_model_cache()
    model = shared_cache.get_model()
    
    if model is None:
        raise RuntimeError("模型缓存未初始化，请先调用 initialize_model_cache()")
    
    # 创建BERTVectorizationService实例并设置共享模型
    model_cache = BERTVectorizationService()
    model_cache._set_shared_model(model)
    return model_cache