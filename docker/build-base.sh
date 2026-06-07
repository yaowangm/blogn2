#!/usr/bin/env bash
# 构建 blogn2-base 基础镜像（PyTorch + 依赖，约 1.2GB）
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VERSION="${1:-$(tr -d '\r\n' < "${ROOT}/docker/BASE_VERSION")}"

export DOCKER_BUILDKIT=0

echo "==> 构建 blogn2-base:${VERSION} （经典构建器，上下文: ${ROOT}）"
echo "    依赖未变时应显示 CACHED；日常发版请用 ./docker/build-app.sh"
docker build \
  -f "${ROOT}/docker/Dockerfile.base" \
  -t "blogn2-base:${VERSION}" \
  -t blogn2-base:latest \
  "${ROOT}"

echo ""
echo "完成: blogn2-base:${VERSION} / blogn2-base:latest"
docker images blogn2-base --format "  {{.Repository}}:{{.Tag}}  {{.Size}}"
