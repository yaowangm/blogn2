from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
import os

# 导入路由模块
from routes import test, user

# 创建FastAPI应用实例
app = FastAPI(
    title="BlogN2 API",
    description="一个基于FastAPI的博客系统",
    version="1.0.0"
)

# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="src/static"), name="static")

# 注册路由
app.include_router(test.router, prefix="/api")
app.include_router(user.router, prefix="/api")

# 根路径 - 返回首页
@app.get("/")
async def root():
    return FileResponse("src/static/index.html")

# 首页路由
@app.get("/index.html")
async def index():
    return FileResponse("src/static/index.html")

# 健康检查端点
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "BlogN2 API"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 