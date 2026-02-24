"""
BERT向量化服务

实现基于BERT模型的文本向量化功能，支持单文本和批量文本向量化。
使用sentence-transformers库提供多语言支持，主要针对中文文本优化。

主要功能：
- 异步模型加载和向量化
- 文本预处理和清洗
- 批量向量化处理
- 向量格式转换（JSON <-> numpy array）

技术特性：
- 单例模式确保模型只加载一次
- 异步处理避免阻塞主线程
- 自动降级处理（模型加载失败时返回零向量）
- 支持本地缓存和在线下载
"""

import asyncio
import json
import logging
import os
import re
import warnings
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any

import numpy as np
import torch
from sentence_transformers import SentenceTransformer

# 导入模型配置
from src.config.model import model_settings, get_model_device, get_model_path, get_model_name, get_model_cache_dir

# 设置日志记录器
logger = logging.getLogger(__name__)

# 禁用sentence-transformers的进度条
os.environ['SENTENCE_TRANSFORMERS_DISABLE_PROGRESS_BAR'] = '1'

# 抑制已知的警告
warnings.filterwarnings("ignore", message="torch.utils._pytree._register_pytree_node is deprecated")
warnings.filterwarnings("ignore", message="The `use_auth_token` argument is deprecated")

class BERTVectorizationService:
    """
    BERT向量化服务（单例模式）
    
    使用sentence-transformers库实现多语言文本向量化，主要针对中文文本优化。
    采用单例模式确保模型只加载一次，提高性能和资源利用率。
    """
    
    _instance = None
    _model_loaded = False
    _loading = False
    _model = None
    # 单线程 executor：模型加载与 encode 在同一线程执行，避免 CUDA 跨线程报错
    _executor: ThreadPoolExecutor = None

    @classmethod
    def _get_executor(cls) -> ThreadPoolExecutor:
        if cls._executor is None:
            cls._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="bert_vectorization")
        return cls._executor

    @classmethod
    def shutdown_executor(cls) -> None:
        """
        关闭线程池并释放资源。应在应用退出时调用（如 FastAPI lifespan 关闭阶段）。
        可重复调用，已关闭时无操作。
        """
        if cls._executor is not None:
            try:
                cls._executor.shutdown(wait=False)
            except Exception as e:
                logger.warning(f"关闭 BERT 向量化线程池时出错: {e}")
            finally:
                cls._executor = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BERTVectorizationService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        # 从配置文件加载模型配置
        self.model_name = get_model_name()
        self.device = get_model_device()
        self.max_length = model_settings.max_length
        self.vector_dimension = model_settings.vector_dimension
        self._initialized = True
    
    async def load_model(self):
        """
        异步加载BERT模型
        
        如果模型已经加载或正在加载中，则直接返回。
        使用后台线程加载模型，避免阻塞主线程。
        """
        if BERTVectorizationService._model_loaded:
            return
        
        if BERTVectorizationService._loading:
            # 等待其他线程完成加载
            while BERTVectorizationService._loading:
                await asyncio.sleep(0.1)
            return
        
        BERTVectorizationService._loading = True
        try:
            logger.info(f"正在加载BERT模型: {self.model_name}")
            
            # 在专用单线程中加载模型（与 encode 同线程，避免 CUDA 跨线程错误）
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(self._get_executor(), self._load_model_sync)
            
            BERTVectorizationService._model_loaded = True
            logger.info(f"BERT模型加载成功: {self.model_name}")
            
        except Exception as e:
            logger.error(f"BERT模型加载失败: {e}")
            BERTVectorizationService._model_loaded = False
            raise
        finally:
            BERTVectorizationService._loading = False
    
    def is_model_loaded(self):
        """检查模型是否已加载"""
        return BERTVectorizationService._model_loaded
    
    def _set_shared_model(self, model):
        """设置共享的模型实例"""
        BERTVectorizationService._model = model
        BERTVectorizationService._model_loaded = True
        logger.info(f"已设置共享模型 (进程: {os.getpid()})")

    def _load_model_sync(self):
        """
        同步加载sentence-transformers模型（在后台线程中执行）
        
        优先尝试从本地缓存加载，失败时从Hugging Face下载。
        """
        try:
            # 获取配置的模型路径
            model_path = get_model_path()
            
            # 如果配置了本地模型路径且优先使用本地模型
            if model_path and model_settings.prefer_local:
                try:
                    BERTVectorizationService._model = SentenceTransformer(model_path, device=self.device)
                    logger.info(f"已加载模型: {self.model_name} (设备: {self.device}) - 使用本地缓存: {model_path}")
                    BERTVectorizationService._model_loaded = True
                    return
                except Exception as e:
                    logger.warning(f"本地模型加载失败: {e}")
                    if not model_settings.fallback_to_huggingface:
                        raise
                    logger.info("回退到Hugging Face下载模型...")
            
            # 从Hugging Face下载或使用模型名称
            cache_dir = get_model_cache_dir()
            if cache_dir:
                BERTVectorizationService._model = SentenceTransformer(self.model_name, cache_folder=cache_dir, device=self.device)
                logger.info(f"已加载模型: {self.model_name} (设备: {self.device}) - 从Hugging Face下载到: {cache_dir}")
            else:
                BERTVectorizationService._model = SentenceTransformer(self.model_name, device=self.device)
                logger.info(f"已加载模型: {self.model_name} (设备: {self.device}) - 从Hugging Face下载")
            
            BERTVectorizationService._model_loaded = True
            
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            logger.error("提示: 请检查模型配置和网络连接")
            BERTVectorizationService._loading = False
            raise
    
    async def vectorize_text(self, text: str) -> np.ndarray:
        """
        将文本向量化
        
        Args:
            text: 输入文本
            
        Returns:
            np.ndarray: 384维向量，失败时返回零向量
        """
        if not BERTVectorizationService._model_loaded:
            await self.load_model()
        
        if not text or not text.strip():
            return np.zeros(self.vector_dimension)
        
        try:
            # 预处理文本
            processed_text = self._preprocess_text(text)
            
            # 在专用单线程中进行向量化（与 load 同线程，避免 CUDA 跨线程错误）
            loop = asyncio.get_event_loop()
            vector = await loop.run_in_executor(self._get_executor(), self._vectorize_sync, processed_text)
            
            return vector
            
        except Exception as e:
            logger.warning(f"文本向量化失败: {e}")
            return np.zeros(self.vector_dimension)
    
    def _vectorize_sync(self, text: str) -> np.ndarray:
        """
        同步向量化（在后台线程中执行）
        
        Args:
            text: 预处理后的文本
            
        Returns:
            np.ndarray: 384维向量
        """
        try:
            # 使用sentence-transformers进行向量化，禁用进度条
            vector = BERTVectorizationService._model.encode(text, show_progress_bar=False)
            
            # sentence-transformers已经返回numpy数组，无需额外处理
            return vector
            
        except Exception as e:
            logger.warning(f"同步向量化失败: {e}")
            return np.zeros(self.vector_dimension)
    
    async def vectorize_batch(self, texts: List[str]) -> List[np.ndarray]:
        """
        批量向量化文本
        
        Args:
            texts: 文本列表
            
        Returns:
            List[np.ndarray]: 向量列表，失败时返回零向量列表
        """
        if not BERTVectorizationService._model_loaded:
            await self.load_model()
        
        if not texts:
            return []
        
        try:
            # 预处理所有文本
            processed_texts = [self._preprocess_text(text) for text in texts]
            
            # 在专用单线程中进行批量向量化（与 load 同线程，避免 CUDA 跨线程错误）
            loop = asyncio.get_event_loop()
            vectors = await loop.run_in_executor(self._get_executor(), self._vectorize_batch_sync, processed_texts)
            
            return vectors
            
        except Exception as e:
            logger.warning(f"批量向量化失败: {e}")
            return [np.zeros(self.vector_dimension) for _ in texts]
    
    def _vectorize_batch_sync(self, texts: List[str]) -> List[np.ndarray]:
        """
        同步批量向量化（在后台线程中执行）
        
        Args:
            texts: 预处理后的文本列表
            
        Returns:
            List[np.ndarray]: 向量列表
        """
        try:
            # 使用sentence-transformers进行批量向量化，禁用进度条
            vectors = BERTVectorizationService._model.encode(texts, show_progress_bar=False)
            
            # sentence-transformers返回的是numpy数组，需要转换为列表
            if len(vectors.shape) == 1:
                # 单个文本的情况
                return [vectors]
            else:
                # 多个文本的情况
                return [vectors[i] for i in range(len(vectors))]
            
        except Exception as e:
            logger.warning(f"同步批量向量化失败: {e}")
            return [np.zeros(self.vector_dimension) for _ in texts]
    
    def _preprocess_text(self, text: str) -> str:
        """
        文本预处理
        
        清理和标准化输入文本，提高向量化质量。
        
        Args:
            text: 原始文本
            
        Returns:
            str: 预处理后的文本
        """
        if not text:
            return ""
        
        # 1. 清理HTML标签
        text = re.sub(r'<[^>]+>', '', text)
        
        # 2. 清理特殊字符，保留中文、英文、数字和基本标点
        text = re.sub(r'[^\w\s\u4e00-\u9fff，。！？；：""''（）【】]', ' ', text)
        
        # 3. 统一换行符
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # 4. 清理多余空白
        text = re.sub(r'\s+', ' ', text)
        
        # 5. 截断过长的文本（避免内存问题）
        if len(text) > 2000:
            text = text[:2000]
        
        return text.strip()
    
    def vector_to_json(self, vector: np.ndarray) -> str:
        """
        将向量转换为JSON字符串
        
        Args:
            vector: numpy向量数组
            
        Returns:
            str: JSON格式的向量字符串
        """
        return json.dumps(vector.tolist())
    
    def json_to_vector(self, json_str: str) -> np.ndarray:
        """
        将JSON字符串转换为向量
        
        Args:
            json_str: JSON格式的向量字符串
            
        Returns:
            np.ndarray: 向量数组，失败时返回零向量
        """
        try:
            return np.array(json.loads(json_str))
        except Exception as e:
            logger.warning(f"JSON向量转换失败: {e}")
            return np.zeros(self.vector_dimension)
    
    async def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        
        Returns:
            Dict[str, Any]: 模型配置信息
        """
        return {
            "model_name": self.model_name,
            "model_loaded": BERTVectorizationService._model_loaded,
            "max_length": self.max_length,
            "device": self.device,
            "vector_dimension": self.vector_dimension
        }

# 依赖注入函数（已废弃）
def get_vectorization_service() -> BERTVectorizationService:
    """
    获取向量化服务实例（已废弃）
    
    注意：此函数已废弃，应该使用 get_cached_model() 获取预加载的模型。
    此函数保留仅用于向后兼容，但会抛出错误提醒开发者使用正确的缓存模型。
    
    Returns:
        BERTVectorizationService: 向量化服务实例
        
    Raises:
        RuntimeError: 提醒使用 get_cached_model() 替代
    """
    raise RuntimeError(
        "get_vectorization_service() 已废弃，请使用 get_cached_model() 获取预加载的模型。"
        "模型应该在服务器启动时加载，不应该在运行时创建新实例。"
    )