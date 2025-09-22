"""
图片处理工具模块

提供图片resize、格式转换等功能的统一处理逻辑。
"""

import os
from typing import Tuple
from PIL import Image
import asyncio
from concurrent.futures import ThreadPoolExecutor


class ImageProcessor:
    """图片处理器类"""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=2)
    
    async def resize_and_save_image(
        self, 
        source_path: str, 
        target_path: str, 
        max_size: Tuple[int, int] = (200, 200),
        quality: int = 85
    ) -> None:
        """
        调整图片大小并保存
        
        Args:
            source_path: 源图片路径
            target_path: 目标图片路径
            max_size: 最大尺寸 (width, height)
            quality: JPEG质量 (1-100)
        """
        def _process_image():
            # 打开源图片
            with Image.open(source_path) as img:
                # 转换为RGB模式（如果是RGBA或其他模式）
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # 计算新的尺寸，保持宽高比
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # 确保目标目录存在
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                
                # 保存图片
                img.save(target_path, 'JPEG', quality=quality, optimize=True)
        
        # 在线程池中执行图片处理
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self.executor, _process_image)
    
    async def get_image_info(self, image_path: str) -> dict:
        """
        获取图片信息
        
        Args:
            image_path: 图片路径
            
        Returns:
            dict: 包含图片信息的字典
        """
        def _get_info():
            with Image.open(image_path) as img:
                return {
                    'width': img.width,
                    'height': img.height,
                    'mode': img.mode,
                    'format': img.format,
                    'size_bytes': os.path.getsize(image_path)
                }
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, _get_info)
    
    def __del__(self):
        """清理资源"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)
