#!/usr/bin/env bash
# 生成 STATIC_VERSION（UTC 时间戳 YYYYMMDDHHMMSS），用于静态资源 ?v= 缓存破除。
#
# 用法:
#   ./scripts/generate-static-version.sh              # 仅打印版本号
#   ./scripts/generate-static-version.sh --write      # 写入项目根 .static_version 并打印
#   ./scripts/generate-static-version.sh --write /path/to/project
set -euo pipefail

generate_static_version() {
  date -u +%Y%m%d%H%M%S
}

write_static_version_file() {
  local root="${1:-$(cd "$(dirname "$0")/.." && pwd)}"
  local version="${2:-$(generate_static_version)}"
  printf '%s\n' "$version" > "${root}/.static_version"
  echo "$version"
}

case "${1:-}" in
  --write)
    write_static_version_file "${2:-}"
    ;;
  "")
    generate_static_version
    ;;
  *)
    echo "未知参数: $1" >&2
    echo "用法: $0 [--write [项目根目录]]" >&2
    exit 1
    ;;
esac
