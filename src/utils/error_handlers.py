from functools import wraps
from fastapi import HTTPException
from typing import Callable, Any
import logging

logger = logging.getLogger(__name__)

def handle_api_errors(error_message: str = "操作失败"):
    """
    通用API错误处理装饰器
    
    Args:
        error_message: 错误消息模板
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                # 重新抛出HTTP异常，保持原有的状态码和详情
                raise
            except Exception as e:
                # 记录错误日志
                logger.error(f"{error_message}: {str(e)}", exc_info=True)
                # 抛出500内部服务器错误
                raise HTTPException(
                    status_code=500, 
                    detail=f"{error_message}: {str(e)}"
                )
        return wrapper
    return decorator 