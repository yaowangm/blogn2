"""
应用配置模块

提供应用级别的配置读取功能，支持环境变量配置。
"""

import os
from dotenv import load_dotenv

def get_blog_posts_page_size() -> int:
    """
    获取博客文章列表每页显示数量
    
    Returns:
        int: 每页显示的文章数量，默认为10
    """
    load_dotenv()
    try:
        page_size = os.getenv('BLOG_POSTS_PAGE_SIZE', '10')
        return int(page_size)
    except (ValueError, TypeError):
        return 10
