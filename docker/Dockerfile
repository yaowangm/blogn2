# Dockerfile for BlogN2
# 使用 CPU-only PyTorch 和排除测试依赖，减小镜像大小
# 预期大小：约 1.1–1.3GB（随 PyTorch/transformers 版本变化）
#
# 特性：
# - 多阶段构建，减小最终镜像大小
# - 使用 CPU-only PyTorch（torch==2.2.0+cpu）
# - pip --no-cache-dir + 精简 venv（去掉 pycache、tests、pip）进一步减体积
# - 优化构建缓存，PyTorch 安装层独立，提高构建速度
# - 使用清华大学镜像源加速构建

# 第一阶段：构建依赖
FROM python:3.12-slim AS builder

# 设置工作目录
WORKDIR /build

# 配置 Debian apt 使用清华大学镜像源（基础镜像使用 Debian）
RUN sed -i 's|http://deb.debian.org|https://mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list.d/debian.sources && \
    sed -i 's|http://security.debian.org|https://mirrors.tuna.tsinghua.edu.cn/debian-security|g' /etc/apt/sources.list.d/debian.sources

# 配置 pip 使用清华大学镜像源（加速 Python 包下载）
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn

# 安装构建依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# 创建虚拟环境并安装依赖
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 升级 pip（使用清华镜像源，不保留缓存）
RUN pip install --no-cache-dir --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple

# 先安装 PyTorch CPU 版本（独立层，不依赖 requirements 文件，便于缓存）
# 尝试多个源：先尝试官方 CPU 索引，失败则使用清华镜像
RUN pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu torch==2.2.0+cpu || \
    pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple torch==2.2.0+cpu

# 复制生产环境依赖文件（放在 PyTorch 安装之后，避免 requirements 变化导致 PyTorch 层缓存失效）
COPY requirements-prod.txt .

# 安装其他依赖（使用清华镜像源，不保留缓存）
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements-prod.txt

# 精简 venv：删除 __pycache__、.pyc、以及各包内的 tests 目录（运行时不需要，可显著减小体积）
RUN find /opt/venv -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true && \
    find /opt/venv -name "*.pyc" -delete 2>/dev/null || true && \
    find /opt/venv -type d -name "tests" -path "*/site-packages/*" -exec rm -rf {} + 2>/dev/null || true

# 运行时不需 pip，卸载以减小体积
RUN /opt/venv/bin/python -m pip uninstall -y pip

# 第二阶段：运行环境
FROM python:3.12-slim

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    APP_ENV=production

# 配置 Debian apt 使用清华大学镜像源（第二阶段也需要配置）
RUN sed -i 's|http://deb.debian.org|https://mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list.d/debian.sources && \
    sed -i 's|http://security.debian.org|https://mirrors.tuna.tsinghua.edu.cn/debian-security|g' /etc/apt/sources.list.d/debian.sources

# 安装运行时依赖（含 sendmail，供密码重置邮件使用本机 sendmail 命令；可选后续改为 SMTP 连宿主机）
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    sendmail \
    gosu \
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

# 确保缓存与上传目录存在（bert-model 为默认模型路径，可被 volume 挂载覆盖）
RUN mkdir -p /app/.cache/models /app/.cache/models/bert-model /app/uploads /app/avatars && \
    chown -R appuser:appuser /app/.cache /app/uploads /app/avatars

# 容器以 root 启动，entrypoint 中先启动 sendmail 再以 appuser 运行 uvicorn
# 暴露端口
EXPOSE 8000

# 健康检查：start-period 留足时间给 BERT/Redis 等初始化，避免误判导致重启
HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=10)" || exit 1

# 启动命令
ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

