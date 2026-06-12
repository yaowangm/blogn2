# BlogN2 应用镜像：在 blogn2-base 上叠加业务代码（约 +16MB 层）
# 构建: ./docker/build-app.sh [tag]  文档: docker/README-DOCKER.md

ARG BASE_IMAGE=blogn2-base:latest
FROM ${BASE_IMAGE}

LABEL org.opencontainers.image.title="blogn2-app" \
      org.opencontainers.image.description="BlogN2 application (code on top of blogn2-base)"

WORKDIR /app

COPY --chown=appuser:appuser . .
COPY --chown=appuser:appuser docker/docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

# 构建时写入静态资源版本（build-app.sh 传入；未传则用 UTC 时间戳）
ARG STATIC_VERSION=
RUN STATIC_VERSION="${STATIC_VERSION:-$(date -u +%Y%m%d%H%M%S)}" && \
    printf '%s\n' "$STATIC_VERSION" > /app/.static_version && \
    chown appuser:appuser /app/.static_version

RUN mkdir -p /app/.cache/models /app/.cache/models/bert-model /app/uploads /app/avatars && \
    chown -R appuser:appuser /app/.cache /app/uploads /app/avatars

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=10)" || exit 1

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
