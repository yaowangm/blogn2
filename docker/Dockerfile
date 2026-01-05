# 多阶段构建 Dockerfile for BlogN2
# 第一阶段：构建依赖
FROM python:3.12-slim as builder

# 设置工作目录
WORKDIR /build

# 安装构建依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 创建虚拟环境并安装依赖
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 第二阶段：运行环境
FROM python:3.12-slim

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    APP_ENV=production

# 安装运行时依赖
# 注意：只安装 postgresql-client 用于连接外部PostgreSQL数据库，不包含PostgreSQL服务器
# Redis 和 BERT 模型通过环境变量配置，不在此处安装
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# 创建非root用户
# 注意：模型缓存目录由 docker-entrypoint.sh 根据 MODEL_CACHE_DIR 环境变量创建
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/data /app/uploads /app/avatars /app/.cache/models && \
    chown -R appuser:appuser /app

# 从构建阶段复制虚拟环境
COPY --from=builder /opt/venv /opt/venv

# 设置工作目录
WORKDIR /app

# 复制应用代码
COPY --chown=appuser:appuser . .

# 复制 docker-entrypoint.sh 到正确位置并设置权限（在切换用户之前）
COPY --chown=appuser:appuser docker/docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

# 确保必要的目录存在并设置正确的权限（在切换用户之前，使用 root 权限）
RUN mkdir -p /app/.cache/models /app/uploads /app/avatars && \
    chown -R appuser:appuser /app/.cache /app/uploads /app/avatars

# 切换到非root用户
USER appuser

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# 启动命令
ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

