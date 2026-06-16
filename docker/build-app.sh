#!/usr/bin/env bash
# 构建 blogn2-app 应用镜像（需已存在 blogn2-base）
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TAG="${1:-latest}"
BASE_VERSION="${BASE_VERSION:-$(cat "${ROOT}/docker/BASE_VERSION")}"
BASE_IMAGE="${BASE_IMAGE:-blogn2-base:${BASE_VERSION}}"

if ! docker image inspect "${BASE_IMAGE}" >/dev/null 2>&1; then
  echo "错误: 未找到基础镜像 ${BASE_IMAGE}" >&2
  echo "请先执行: ./docker/build-base.sh" >&2
  exit 1
fi

export DOCKER_BUILDKIT=0

if [ -z "${STATIC_VERSION:-}" ]; then
  STATIC_VERSION="$("${ROOT}/scripts/generate-static-version.sh" --write "${ROOT}")"
else
  printf '%s\n' "$STATIC_VERSION" > "${ROOT}/.static_version"
fi

echo "==> 构建 blogn2-app:${TAG} （BASE_IMAGE=${BASE_IMAGE}）"
echo "    仅复制代码层，不会重新 pip 下载依赖"
echo "    STATIC_VERSION=${STATIC_VERSION}"
docker build \
  -f "${ROOT}/docker/Dockerfile.app" \
  --build-arg "BASE_IMAGE=${BASE_IMAGE}" \
  --build-arg "STATIC_VERSION=${STATIC_VERSION}" \
  -t "blogn2-app:${TAG}" \
  "${ROOT}"

echo ""
echo "完成: blogn2-app:${TAG}"
docker images blogn2-app --format "  {{.Repository}}:{{.Tag}}  {{.Size}}"
