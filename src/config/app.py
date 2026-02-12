"""
应用配置模块

提供应用级别的配置读取功能，支持环境变量配置。
"""

import os
import logging
from typing import Optional

from .utils import load_config_file, get_config_file_path

# 加载配置文件（如果存在）
load_config_file()

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


def get_mail_from() -> str:
    """
    获取密码重置邮件发件人地址
    
    Returns:
        str: 发件人邮箱，从环境变量 MAIL_FROM 读取
    """
    return os.getenv('MAIL_FROM', 'noreply@localhost')


def get_reset_link_expire_minutes() -> int:
    """
    获取密码重置链接有效期（分钟）
    
    Returns:
        int: 有效期分钟数，从环境变量 RESET_LINK_EXPIRE_MINUTES 读取，默认 60
    """
    try:
        return int(os.getenv('RESET_LINK_EXPIRE_MINUTES', '60'))
    except (ValueError, TypeError):
        return 60


def get_smtp_host() -> Optional[str]:
    """
    获取 SMTP 主机（用于连接宿主机 sendmail）。
    - 若设置则通过 SMTP 发信；未设置或空则使用本机 sendmail 命令。
    - Docker 内未设置时默认为 localhost，通过 SMTP 连宿主机 25 端口发信（不依赖容器内安装 sendmail）。
    """
    v = os.getenv('SMTP_HOST', '').strip()
    if v:
        return v
    try:
        from .utils import is_docker_container
        if is_docker_container():
            return 'localhost'
    except Exception:
        pass
    return None


def get_smtp_port() -> int:
    """获取 SMTP 端口，默认 25"""
    try:
        return int(os.getenv('SMTP_PORT', '25'))
    except (ValueError, TypeError):
        return 25





def validate_app_config() -> dict:
    """
    验证应用配置并返回配置信息
    
    Returns:
        Dict: 包含完整应用配置信息的字典
    """
    config_file = get_config_file_path()
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
        "config_source": str(config_file) if config_file else "defaults"
    }
    
    if config_info["debug"]:
        logger.debug(f"App configuration loaded: {config_info}")
    
    return config_info
