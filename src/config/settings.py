import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Settings:
    # 应用配置
    APP_NAME: str = "BlogN2"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # 服务器配置
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # 安全配置
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALLOWED_ORIGINS: list = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8080").split(",")
    
    # 网站配置
    SITE_NAME: str = "BlogN"
    SITE_VERSION: str = "V1"
    LOGO_URL: str = "/static/images/logo-light.svg"

# 创建全局配置实例
settings = Settings() 