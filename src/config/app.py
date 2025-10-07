"""
应用配置模块

提供应用级别的配置读取功能，支持环境变量配置。
"""

import os
import logging
from dotenv import load_dotenv

# 确保加载.env文件
load_dotenv()

logger = logging.getLogger(__name__)


def get_base_url() -> str:
    """
    获取应用基础URL
    
    Returns:
        str: 应用基础URL，从环境变量BASE_URL读取，默认为http://localhost:8000
    """
    return os.getenv('BASE_URL', 'http://localhost:8000')


def get_app_environment() -> str:
    """
    获取应用环境
    
    Returns:
        str: 应用环境，从环境变量APP_ENV读取，默认为development
    """
    return os.getenv('APP_ENV', 'development')


def is_production() -> bool:
    """
    检查是否为生产环境
    
    Returns:
        bool: 如果是生产环境返回True，否则返回False
    """
    return get_app_environment().lower() == "production"


def is_development() -> bool:
    """
    检查是否为开发环境
    
    Returns:
        bool: 如果是开发环境返回True，否则返回False
    """
    return get_app_environment().lower() == "development"


def is_testing() -> bool:
    """
    检查是否为测试环境
    
    Returns:
        bool: 如果是测试环境返回True，否则返回False
    """
    return get_app_environment().lower() == "testing"


def get_blog_posts_page_size() -> int:
    """
    获取博客文章列表每页显示数量
    
    Returns:
        int: 每页显示的文章数量，从环境变量BLOG_POSTS_PAGE_SIZE读取，默认为10
    """
    try:
        return int(os.getenv('BLOG_POSTS_PAGE_SIZE', '10'))
    except (ValueError, TypeError):
        return 10


def get_max_attachments_per_article() -> int:
    """
    获取每篇文章最大附件数量
    
    Returns:
        int: 每篇文章最大附件数量，从环境变量MAX_ATTACHMENTS_PER_ARTICLE读取，默认为10
    """
    try:
        return int(os.getenv('MAX_ATTACHMENTS_PER_ARTICLE', '10'))
    except (ValueError, TypeError):
        return 10


def get_upload_dir() -> str:
    """
    获取文件上传目录
    
    Returns:
        str: 文件上传目录路径，从环境变量UPLOAD_DIR读取，默认为../pic/blogn_img/upload
    """
    return os.getenv('UPLOAD_DIR', '../pic/blogn_img/upload')





def validate_app_config() -> dict:
    """
    验证应用配置并返回配置信息
    
    Returns:
        Dict: 包含完整应用配置信息的字典
    """
    config_info = {
        "app_env": get_app_environment(),
        "debug": os.getenv('DEBUG', 'true').lower() == 'true',
        "log_level": os.getenv('LOG_LEVEL', 'INFO'),
        "base_url": get_base_url(),
        "blog_posts_page_size": get_blog_posts_page_size(),
        "max_attachments_per_article": get_max_attachments_per_article(),
        "max_file_size": int(os.getenv('MAX_FILE_SIZE', '10485760')),
        "allowed_file_types": os.getenv('ALLOWED_FILE_TYPES', 'image/jpeg,image/png,image/gif'),
        "upload_dir": get_upload_dir(),
        "avatar_dir": os.getenv('AVATAR_DIR', '../pic/blogn_img/userlogo'),
        "config_source": "environment" if os.path.exists(".env") else "defaults"
    }
    
    if config_info["debug"]:
        logger.debug(f"App configuration loaded: {config_info}")
    
    return config_info
