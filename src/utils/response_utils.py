"""
API响应工具类

提供统一的API响应格式，减少重复代码。
"""

from typing import Any, Dict, Optional
from fastapi import HTTPException
from fastapi.responses import JSONResponse

class ResponseUtils:
    """API响应工具类"""
    
    @staticmethod
    def success_response(
        data: Any = None,
        message: str = "操作成功",
        status_code: int = 200
    ) -> JSONResponse:
        """
        创建成功响应
        
        Args:
            data: 响应数据
            message: 成功消息
            status_code: HTTP状态码
            
        Returns:
            JSONResponse: 成功响应
        """
        response_data = {
            "success": True,
            "message": message
        }
        
        if data is not None:
            response_data["data"] = data
            
        return JSONResponse(
            content=response_data,
            status_code=status_code
        )
    
    @staticmethod
    def error_response(
        message: str = "操作失败",
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None
    ) -> HTTPException:
        """
        创建错误响应
        
        Args:
            message: 错误消息
            status_code: HTTP状态码
            details: 错误详情
            
        Returns:
            HTTPException: 错误异常
        """
        error_detail = {"message": message}
        if details:
            error_detail.update(details)
            
        return HTTPException(
            status_code=status_code,
            detail=error_detail
        )
    
    @staticmethod
    def validation_error_response(
        field: str,
        message: str
    ) -> HTTPException:
        """
        创建验证错误响应
        
        Args:
            field: 字段名
            message: 错误消息
            
        Returns:
            HTTPException: 验证错误异常
        """
        return ResponseUtils.error_response(
            message=f"字段 '{field}' 验证失败: {message}",
            status_code=422,
            details={"field": field}
        )
    
    @staticmethod
    def not_found_response(
        resource: str = "资源"
    ) -> HTTPException:
        """
        创建未找到响应
        
        Args:
            resource: 资源名称
            
        Returns:
            HTTPException: 未找到异常
        """
        return ResponseUtils.error_response(
            message=f"{resource}不存在",
            status_code=404
        )
    
    @staticmethod
    def forbidden_response(
        message: str = "无权限访问"
    ) -> HTTPException:
        """
        创建禁止访问响应
        
        Args:
            message: 错误消息
            
        Returns:
            HTTPException: 禁止访问异常
        """
        return ResponseUtils.error_response(
            message=message,
            status_code=403
        )
    
    @staticmethod
    def paginated_response(
        items: list,
        total: int,
        page: int,
        page_size: int,
        message: str = "获取成功"
    ) -> Dict[str, Any]:
        """
        创建分页响应
        
        Args:
            items: 数据项列表
            total: 总数量
            page: 当前页码
            page_size: 每页大小
            message: 成功消息
            
        Returns:
            Dict[str, Any]: 分页响应数据
        """
        total_pages = (total + page_size - 1) // page_size
        
        return {
            "success": True,
            "message": message,
            "data": {
                "items": items,
                "pagination": {
                    "current_page": page,
                    "page_size": page_size,
                    "total_count": total,
                    "total_pages": total_pages,
                    "has_next": page < total_pages,
                    "has_prev": page > 1
                }
            }
        }
