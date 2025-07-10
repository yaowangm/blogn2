from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from datetime import datetime

# 创建路由器
router = APIRouter()

@router.get("/test", response_class=HTMLResponse)
async def test_page():
    """
    测试页面端点
    访问地址: http://localhost:8000/api/test
    """
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>BlogN2 - 测试页面</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }}
            .container {{
                background: white;
                padding: 40px;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                text-align: center;
                max-width: 600px;
                width: 100%;
            }}
            h1 {{
                color: #333;
                margin-bottom: 20px;
                font-size: 2.5em;
            }}
            .status {{
                background: #4CAF50;
                color: white;
                padding: 10px 20px;
                border-radius: 25px;
                display: inline-block;
                margin: 20px 0;
                font-weight: bold;
            }}
            .info {{
                background: #f8f9fa;
                padding: 20px;
                border-radius: 10px;
                margin: 20px 0;
                border-left: 4px solid #667eea;
            }}
            .time {{
                color: #666;
                font-size: 0.9em;
                margin-top: 20px;
            }}
            .links {{
                margin-top: 30px;
            }}
            .links a {{
                display: inline-block;
                margin: 0 10px;
                padding: 10px 20px;
                background: #667eea;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                transition: background 0.3s;
            }}
            .links a:hover {{
                background: #5a6fd8;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 BlogN2 API</h1>
            <div class="status">✅ 运行正常</div>
            
            <div class="info">
                <h3>测试页面信息</h3>
                <p>恭喜！你的FastAPI应用已经成功运行。</p>
                <p>这是一个测试页面，用于验证网站的基本功能。</p>
            </div>
            
            <div class="time">
                <strong>当前时间:</strong> {current_time}
            </div>
            
            <div class="links">
                <a href="/">首页</a>
                <a href="/health">健康检查</a>
                <a href="/docs">API文档</a>
            </div>
        </div>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)

@router.get("/test/json")
async def test_json():
    """
    返回JSON格式的测试数据
    访问地址: http://localhost:8000/api/test/json
    """
    return {
        "message": "测试成功",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@router.get("/test/error")
async def test_error():
    """
    测试错误处理
    访问地址: http://localhost:8000/api/test/error
    """
    raise HTTPException(status_code=500, detail="这是一个测试错误") 