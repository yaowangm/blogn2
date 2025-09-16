"""
文件处理工具模块

提供文件上传、服务、删除等操作的统一处理逻辑。
"""

import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import HTTPException, UploadFile, File
from fastapi.responses import FileResponse

from src.utils.file_utils import get_temp_dir, validate_and_sanitize_path
from src.config.app import get_upload_dir


class FileHandler:
    """文件处理器类"""
    
    # 允许的文件类型
    ALLOWED_TYPES = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif']
    
    # 允许的文件扩展名
    ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif']
    
    # 最大文件大小（1MB）
    MAX_FILE_SIZE = 1048576
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        清理文件名，防止路径遍历攻击
        
        Args:
            filename: 原始文件名
            
        Returns:
            str: 清理后的安全文件名
            
        Raises:
            HTTPException: 如果文件名包含危险字符
        """
        if not filename:
            raise HTTPException(status_code=400, detail="文件名不能为空")
        
        # 移除路径分隔符和危险字符
        dangerous_chars = ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in dangerous_chars:
            if char in filename:
                raise HTTPException(status_code=400, detail=f"文件名包含非法字符: {char}")
        
        # 移除前后空格
        filename = filename.strip()
        
        # 检查文件名长度
        if len(filename) > 255:
            raise HTTPException(status_code=400, detail="文件名过长")
        
        # 检查是否为空或只包含空格
        if not filename:
            raise HTTPException(status_code=400, detail="文件名不能为空")
        
        return filename
    
    @staticmethod
    def validate_file(file: UploadFile) -> None:
        """
        验证上传文件
        
        Args:
            file: 上传的文件
            
        Raises:
            HTTPException: 当文件验证失败时
        """
        if not file.filename:
            raise HTTPException(status_code=400, detail="文件名不能为空")
        
        # 检查文件类型
        if file.content_type not in FileHandler.ALLOWED_TYPES:
            raise HTTPException(status_code=400, detail="只支持jpg、png、gif格式的图片")
    
    @staticmethod
    async def process_upload_file(file: UploadFile, temp: bool = False) -> Dict[str, Any]:
        """
        处理文件上传
        
        Args:
            file: 上传的文件
            temp: 是否为临时文件
            
        Returns:
            Dict[str, Any]: 上传结果
        """
        # 验证文件
        FileHandler.validate_file(file)
        
        # 清理文件名
        safe_filename = FileHandler.sanitize_filename(file.filename)
        
        # 读取文件内容
        file_content = await file.read()
        
        # 检查文件大小
        if len(file_content) > FileHandler.MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="图片大小不能超过1MB")
        
        # 检查文件扩展名
        file_extension = os.path.splitext(safe_filename)[1].lower()
        if file_extension not in FileHandler.ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail="不支持的文件扩展名")
        
        # 生成唯一文件名
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        
        if temp:
            # 临时文件处理
            return await FileHandler._save_temp_file(file_content, unique_filename)
        else:
            # 正式文件处理
            return await FileHandler._save_regular_file(file_content, unique_filename)
    
    @staticmethod
    async def _save_temp_file(file_content: bytes, unique_filename: str) -> Dict[str, Any]:
        """保存临时文件"""
        temp_dir = get_temp_dir()
        os.makedirs(temp_dir, exist_ok=True)
        file_path = os.path.join(temp_dir, unique_filename)
        
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)
        
        # 验证文件是否保存成功
        if not os.path.exists(file_path):
            raise HTTPException(status_code=500, detail="文件保存失败")
        
        return {
            "success": True,
            "filename": unique_filename,
            "size": len(file_content),
            "url": f"/api/temp-upload/{unique_filename}",
            "relative_path": f"temp/{unique_filename}",
            "is_temp": True
        }
    
    @staticmethod
    async def _save_regular_file(file_content: bytes, unique_filename: str) -> Dict[str, Any]:
        """保存正式文件"""
        upload_dir = get_upload_dir()
        current_time = datetime.now()
        month_dir = current_time.strftime("%Y%m")
        monthly_upload_path = os.path.join(upload_dir, month_dir)
        os.makedirs(monthly_upload_path, exist_ok=True)
        
        file_path = os.path.join(monthly_upload_path, unique_filename)
        relative_path = f"{month_dir}/{unique_filename}"
        
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)
        
        # 验证文件是否保存成功
        if not os.path.exists(file_path):
            raise HTTPException(status_code=500, detail="文件保存失败")
        
        return {
            "success": True,
            "filename": unique_filename,
            "size": len(file_content),
            "url": f"/upload/{relative_path}",
            "relative_path": relative_path,
            "is_temp": False
        }
    
    @staticmethod
    def serve_file(file_path: str, media_type: str = None) -> FileResponse:
        """
        通用文件服务函数
        
        Args:
            file_path: 文件路径
            media_type: 媒体类型
            
        Returns:
            FileResponse: 文件响应
            
        Raises:
            HTTPException: 当文件不存在时抛出404错误
        """
        if os.path.exists(file_path):
            return FileResponse(file_path, media_type=media_type)
        else:
            raise HTTPException(status_code=404, detail="File not found")
    
    @staticmethod
    async def delete_temp_file(filename: str) -> Dict[str, str]:
        """
        删除临时文件
        
        Args:
            filename: 文件名
            
        Returns:
            Dict[str, str]: 删除结果
        """
        # 验证文件名，防止路径遍历攻击
        safe_filename = FileHandler.sanitize_filename(filename)
        
        temp_dir = get_temp_dir()
        file_path = os.path.join(temp_dir, safe_filename)
        
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return {"success": True, "message": "文件删除成功"}
            else:
                return {"success": True, "message": "文件不存在"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"文件删除失败: {str(e)}")

