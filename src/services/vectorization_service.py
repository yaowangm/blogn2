"""
BERT向量化服务
实现基于BERT模型的文本向量化功能
"""

import asyncio
import json
import numpy as np
from typing import List, Dict, Any
import torch
from transformers import AutoTokenizer, AutoModel
import re
import warnings

# 抑制已知的警告
warnings.filterwarnings("ignore", message="torch.utils._pytree._register_pytree_node is deprecated")
warnings.filterwarnings("ignore", message="The `use_auth_token` argument is deprecated")

class BERTVectorizationService:
    """BERT向量化服务（单例模式）"""
    
    _instance = None
    _model_loaded = False
    _loading = False
    _model = None
    _tokenizer = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BERTVectorizationService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self.model_name = "bert-base-chinese"
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.max_length = 512
        self._initialized = True
    
    async def load_model(self):
        """异步加载BERT模型"""
        if BERTVectorizationService._model_loaded:
            return
        
        # 调试代码：如果模型已经加载过，不应该再次加载
        if hasattr(BERTVectorizationService, '_loading_attempted') and BERTVectorizationService._loading_attempted:
            print("❌ 模型重复加载检测：模型已经被加载过，不应该再次加载！")
            assert False, "模型重复加载：模型已经被加载过，不应该再次加载！"
        
        if BERTVectorizationService._loading:
            # 等待加载完成
            while BERTVectorizationService._loading:
                await asyncio.sleep(0.1)
            return
        
        BERTVectorizationService._loading = True
        BERTVectorizationService._loading_attempted = True  # 标记已尝试加载
        try:
            print(f"🔄 正在加载BERT模型: {self.model_name}")
            
            # 在后台线程中加载模型
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._load_model_sync)
            
            BERTVectorizationService._model_loaded = True
            print(f"✅ BERT模型加载成功: {self.model_name}")
            
        except Exception as e:
            print(f"❌ BERT模型加载失败: {e}")
            BERTVectorizationService._model_loaded = False
            raise
        finally:
            BERTVectorizationService._loading = False
    
    def is_model_loaded(self):
        """检查模型是否已加载"""
        return BERTVectorizationService._model_loaded
    
    def _load_model_sync(self):
        """同步加载模型（在后台线程中执行）"""
        try:
            # 强制使用本地缓存，不检查网络
            # 设置环境变量强制使用 PyTorch
            import os
            os.environ['TRANSFORMERS_OFFLINE'] = '1'
            
            # 直接指定本地模型路径
            model_path = "/home/wy/.cache/huggingface/hub/models--bert-base-chinese/snapshots/8f23c25b06e129b6c986331a13d8d025a92cf0ea"
            
            BERTVectorizationService._tokenizer = AutoTokenizer.from_pretrained(
                model_path,
                local_files_only=True,
                token=False,
                use_fast=True
            )
            BERTVectorizationService._model = AutoModel.from_pretrained(
                model_path,
                local_files_only=True,
                token=False,
                torch_dtype=torch.float32
            )
            BERTVectorizationService._model.eval()
            BERTVectorizationService._model.to(self.device)
            print(f"📦 已加载模型: {self.model_name} (设备: {self.device}) - 使用本地缓存")
        except Exception as e:
            print(f"❌ 模型加载失败: {e}")
            print(f"💡 提示: 请确保模型已下载到本地缓存")
            raise
    
    async def vectorize_text(self, text: str) -> np.ndarray:
        """
        将文本向量化
        
        Args:
            text: 输入文本
            
        Returns:
            768维向量
        """
        if not BERTVectorizationService._model_loaded:
            await self.load_model()
        
        if not text or not text.strip():
            return np.zeros(768)
        
        try:
            # 预处理文本
            processed_text = self._preprocess_text(text)
            
            # 在后台线程中进行向量化
            loop = asyncio.get_event_loop()
            vector = await loop.run_in_executor(None, self._vectorize_sync, processed_text)
            
            return vector
            
        except Exception as e:
            return np.zeros(768)
    
    def _vectorize_sync(self, text: str) -> np.ndarray:
        """同步向量化（在后台线程中执行）"""
        try:
            # 分词和编码
            inputs = BERTVectorizationService._tokenizer(
                text,
                return_tensors="pt",
                max_length=self.max_length,
                truncation=True,
                padding=True
            )
            
            # 移动到设备
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # 生成向量
            with torch.no_grad():
                outputs = BERTVectorizationService._model(**inputs)
                # 使用[CLS] token的向量作为句子向量
                vector = outputs.last_hidden_state[:, 0, :].cpu().numpy()
            
            # 归一化向量以提高相似度计算准确性
            vector = vector[0]  # 获取768维向量
            vector_norm = np.linalg.norm(vector)
            if vector_norm > 0:
                vector = vector / vector_norm
            
            return vector
            
        except Exception as e:
            return np.zeros(768)
    
    async def vectorize_batch(self, texts: List[str]) -> List[np.ndarray]:
        """
        批量向量化文本
        
        Args:
            texts: 文本列表
            
        Returns:
            向量列表
        """
        if not BERTVectorizationService._model_loaded:
            await self.load_model()
        
        if not texts:
            return []
        
        try:
            # 预处理所有文本
            processed_texts = [self._preprocess_text(text) for text in texts]
            
            # 在后台线程中进行批量向量化
            loop = asyncio.get_event_loop()
            vectors = await loop.run_in_executor(None, self._vectorize_batch_sync, processed_texts)
            
            return vectors
            
        except Exception as e:
            return [np.zeros(768) for _ in texts]
    
    def _vectorize_batch_sync(self, texts: List[str]) -> List[np.ndarray]:
        """同步批量向量化（在后台线程中执行）"""
        try:
            vectors = []
            
            # 分批处理，避免内存溢出
            batch_size = 8
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                
                # 分词和编码
                inputs = BERTVectorizationService._tokenizer(
                    batch_texts,
                    return_tensors="pt",
                    max_length=self.max_length,
                    truncation=True,
                    padding=True
                )
                
                # 移动到设备
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
                
                # 生成向量
                with torch.no_grad():
                    outputs = BERTVectorizationService._model(**inputs)
                    # 使用[CLS] token的向量
                    batch_vectors = outputs.last_hidden_state[:, 0, :].cpu().numpy()
                    vectors.extend(batch_vectors)
            
            return vectors
            
        except Exception as e:
            return [np.zeros(768) for _ in texts]
    
    def _preprocess_text(self, text: str) -> str:
        """
        文本预处理
        
        Args:
            text: 原始文本
            
        Returns:
            预处理后的文本
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
        
        # 5. 对于短文本，添加一些上下文信息
        if len(text.strip()) < 10:
            # 短文本可能缺乏足够的语义信息，保持原样
            pass
        
        # 6. 截断过长的文本
        if len(text) > 2000:  # 限制文本长度
            text = text[:2000]
        
        return text.strip()
    
    def vector_to_json(self, vector: np.ndarray) -> str:
        """将向量转换为JSON字符串"""
        return json.dumps(vector.tolist())
    
    def json_to_vector(self, json_str: str) -> np.ndarray:
        """将JSON字符串转换为向量"""
        try:
            return np.array(json.loads(json_str))
        except:
            return np.zeros(768)
    
    async def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "model_name": self.model_name,
            "model_loaded": BERTVectorizationService._model_loaded,
            "max_length": self.max_length,
            "device": self.device,
            "vector_dimension": 768
        }

# 依赖注入函数
def get_vectorization_service() -> BERTVectorizationService:
    """获取向量化服务实例"""
    return BERTVectorizationService()