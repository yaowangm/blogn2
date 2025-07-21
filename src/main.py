import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径，确保模块导入正确
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

# 导入API控制器模块
from src.controllers import metadata, user, blog

# 创建FastAPI应用实例
app = FastAPI(
    title="BlogN2 API",
    description="一个基于FastAPI的博客系统",
    version="1.0.0"
)

# 配置CORS中间件，允许跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制具体域名以提高安全性
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 自定义upload文件路由 - 必须在静态文件挂载之前
@app.get("/static/upload/{path:path}")
async def serve_upload_file(path: str):
    """
    提供upload文件访问
    
    Args:
        path: 文件路径
        
    Returns:
        FileResponse: 文件
    """
    import os
    upload_path = f"/home/wy/pic/blogn_img/upload/{path}"
    if os.path.exists(upload_path):
        return FileResponse(upload_path)
    else:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="File not found")

# 添加HEAD方法支持
@app.head("/static/upload/{path:path}")
async def serve_upload_file_head(path: str):
    """
    提供upload文件HEAD请求支持
    
    Args:
        path: 文件路径
        
    Returns:
        FileResponse: 文件头信息
    """
    import os
    upload_path = f"/home/wy/pic/blogn_img/upload/{path}"
    if os.path.exists(upload_path):
        return FileResponse(upload_path)
    else:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="File not found")

# 挂载静态文件目录，提供前端资源访问
app.mount("/static", StaticFiles(directory="src/static"), name="static")

# 挂载用户头像目录，直接指向实际路径
# app.mount("/static/userlogo", StaticFiles(directory="/home/wy/pic/blogn_img/userlogo"), name="userlogo")

# 自定义头像文件路由
@app.get("/avatars/{prefix}/{filename}")
async def serve_avatar(prefix: str, filename: str):
    """
    提供用户头像文件访问
    
    Args:
        prefix: 用户ID前缀
        filename: 头像文件名
        
    Returns:
        FileResponse: 头像文件
    """
    import os
    avatar_path = f"../pic/blogn_img/userlogo/{prefix}/{filename}"
    if os.path.exists(avatar_path):
        return FileResponse(avatar_path, media_type="image/jpeg")
    else:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Avatar not found")

# 注册API路由，统一使用/api前缀
app.include_router(metadata.router, prefix="/api")
app.include_router(user.router, prefix="/api")
app.include_router(blog.router, prefix="/api")

# 根路径和首页路由 - 都返回首页
@app.get("/")
@app.get("/index.html")
async def root():
    """
    根路径和首页路由
    
    返回网站的首页HTML文件。
    
    Returns:
        FileResponse: 首页HTML文件
    """
    return FileResponse("src/static/index.html")

# 测试页面路由
@app.get("/test")
async def test_page():
    """
    测试页面路由
    
    用于测试动态组件的功能。
    
    Returns:
        FileResponse: 测试页面HTML文件
    """
    return FileResponse("src/static/test.html")

# 评论截断测试页面路由
@app.get("/test-truncate")
async def test_truncate_page():
    """
    评论截断测试页面路由
    
    用于测试评论截断功能。
    
    Returns:
        FileResponse: 评论截断测试页面HTML文件
    """
    return FileResponse("src/static/test-comment-truncate.html")

# 健康检查端点
@app.get("/health")
async def health_check():
    """
    健康检查端点
    
    用于监控系统状态和负载均衡器健康检查。
    
    Returns:
        Dict[str, str]: 包含服务状态的字典
    """
    return {"status": "healthy", "service": "BlogN2 API"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 