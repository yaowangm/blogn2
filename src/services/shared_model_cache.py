"""
跨进程共享的模型缓存管理器

使用 multiprocessing.Manager + portalocker 实现跨进程协调，
确保只有一个进程执行模型初始化，其他进程等待并复用结果。
"""

import os
import time
import logging
import portalocker
from multiprocessing import Manager
from typing import Optional, Dict, Any
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class SharedModelCache:
    """跨进程共享的模型缓存管理器"""
    
    def __init__(self, lock_file: str = "/tmp/model_cache.lock"):
        self.lock_file = lock_file
        self.manager = Manager()
        self.shared_dict = self.manager.dict()
        self._model = None
        self._is_initialized = False
    
    def initialize_model(self, model_name: str, model_path: Optional[str] = None) -> bool:
        """
        初始化模型，使用文件锁确保只有一个进程执行初始化
        
        Args:
            model_name: 模型名称
            model_path: 本地模型路径（可选）
            
        Returns:
            bool: 是否成功初始化
        """
        if self._is_initialized:
            return True
        
        # 使用文件锁确保只有一个进程执行初始化
        with open(self.lock_file, 'w') as f:
            try:
                # 获取排他锁，非阻塞
                portalocker.lock(f, portalocker.LOCK_EX | portalocker.LOCK_NB)
                
                # 再次检查是否已被其他进程初始化
                if self.shared_dict.get('model_loaded', False):
                    logger.info(f"进程 {os.getpid()} 检测到模型已被其他进程初始化，开始加载...")
                    self._load_from_shared()
                    return True
                
                logger.info(f"进程 {os.getpid()} 开始初始化模型: {model_name}")
                
                # 初始化模型
                if model_path and os.path.exists(model_path):
                    model = SentenceTransformer(model_path)
                    logger.info(f"从本地路径加载模型: {model_path}")
                else:
                    model = SentenceTransformer(model_name)
                    logger.info(f"从Hugging Face下载模型: {model_name}")
                
                # 将模型信息存储到共享字典
                self.shared_dict.update({
                    'model_loaded': True,
                    'model_name': model_name,
                    'model_path': model_path,
                    'init_process_id': os.getpid(),
                    'init_timestamp': time.time()
                })
                
                # 存储模型对象到当前进程
                self._model = model
                self._is_initialized = True
                
                logger.info(f"✅ 模型初始化完成 (进程: {os.getpid()})")
                return True
                
            except portalocker.LockException:
                # 其他进程正在初始化，等待
                logger.info(f"进程 {os.getpid()} 检测到其他进程正在初始化模型，等待...")
                return self._wait_for_initialization()
            except Exception as e:
                logger.error(f"模型初始化失败: {e}")
                return False
    
    def _wait_for_initialization(self, timeout: int = 300) -> bool:
        """等待其他进程完成初始化"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.shared_dict.get('model_loaded', False):
                logger.info(f"进程 {os.getpid()} 检测到模型已初始化，开始加载...")
                return self._load_from_shared()
            
            time.sleep(1)
        
        logger.error(f"进程 {os.getpid()} 等待模型初始化超时")
        return False
    
    def _load_from_shared(self) -> bool:
        """从共享信息加载模型"""
        try:
            model_name = self.shared_dict.get('model_name')
            model_path = self.shared_dict.get('model_path')
            
            if not model_name:
                logger.error("共享字典中缺少模型名称")
                return False
            
            # 重新加载模型（每个进程都需要加载到自己的内存）
            if model_path and os.path.exists(model_path):
                self._model = SentenceTransformer(model_path)
                logger.info(f"进程 {os.getpid()} 从本地路径加载模型: {model_path}")
            else:
                self._model = SentenceTransformer(model_name)
                logger.info(f"进程 {os.getpid()} 从Hugging Face加载模型: {model_name}")
            
            self._is_initialized = True
            logger.info(f"✅ 模型加载完成 (进程: {os.getpid()})")
            return True
            
        except Exception as e:
            logger.error(f"从共享信息加载模型失败: {e}")
            return False
    
    def get_model(self) -> Optional[SentenceTransformer]:
        """获取模型实例"""
        if not self._is_initialized:
            logger.warning("模型未初始化")
            return None
        return self._model
    
    def get_shared_info(self) -> Dict[str, Any]:
        """获取共享信息"""
        return dict(self.shared_dict)
    
    def cleanup(self):
        """清理资源"""
        if hasattr(self, 'manager'):
            self.manager.shutdown()

# 全局共享缓存实例
_shared_cache = None

def get_shared_model_cache() -> SharedModelCache:
    """获取全局共享模型缓存实例"""
    global _shared_cache
    if _shared_cache is None:
        _shared_cache = SharedModelCache()
    return _shared_cache
