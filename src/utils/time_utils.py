"""
时间处理工具模块

提供时间格式化和处理的统一工具函数。
"""

from datetime import datetime


class TimeUtils:
    """时间处理工具类"""
    
    @staticmethod
    def format_relative_time(post_time: datetime) -> str:
        """
        格式化时间显示为相对时间
        
        Args:
            post_time: 要格式化的时间
            
        Returns:
            str: 格式化后的相对时间字符串
        """
        now = datetime.now()
        diff = now - post_time
        
        # 如果是今天，显示相对时间
        if diff.days == 0:
            if diff.seconds >= 3600:
                hours = diff.seconds // 3600
                return f"{hours}小时前"
            elif diff.seconds >= 60:
                minutes = diff.seconds // 60
                return f"{minutes}分钟前"
            else:
                return "刚刚"
        # 如果是昨天，显示"昨天"
        elif diff.days == 1:
            return "昨天"
        # 如果是前天，显示"前天"
        elif diff.days == 2:
            return "前天"
        # 其他情况显示具体日期
        else:
            return post_time.strftime("%Y-%m-%d")
    
    @staticmethod
    def format_datetime_for_api(dt: datetime) -> str:
        """
        格式化时间为API响应格式
        
        Args:
            dt: 要格式化的时间
            
        Returns:
            str: ISO格式的时间字符串
        """
        return dt.isoformat() if dt else None
    
    @staticmethod
    def format_access_count(access_count: int) -> str:
        """
        格式化访问量显示
        
        Args:
            access_count: 访问量
            
        Returns:
            str: 格式化后的访问量字符串
        """
        if access_count >= 1000:
            return f"{access_count/1000:.1f}k"
        else:
            return str(access_count)

