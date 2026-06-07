#!/usr/bin/env bash
# 一体镜像构建（docker/Dockerfile，兼容旧 README 命令）
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TAG="${1:-latest}"
IMAGE="${IMAGE:-blogn2-app:${TAG}}"

export DOCKER_BUILDKIT=0

echo "==> 构建 ${IMAGE} （经典构建器）"
echo "    推荐日常发版: ./docker/build-base.sh && ./docker/build-app.sh"
docker build \
  -f "${ROOT}/docker/Dockerfile" \
  -t "${IMAGE}" \
  "${ROOT}"

echo ""
docker images "${IMAGE%%:*}" --format "  {{.Repository}}:{{.Tag}}  {{.Size}}" 2>/dev/null | head -5 || true
