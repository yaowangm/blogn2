#!/usr/bin/env bash
# 在远程主机加载手动上传的镜像包（须同步 lib/archive_paths.sh）
# 文档: docker/README-DOCKER.md
#
# 用法:
#   ./load-images.sh base [tar.gz路径]
#   ./load-images.sh app [tag] [tar.gz路径]    # 须先 load base
#   ./load-images.sh app-full [tag] [tar.gz路径]
#   ./load-images.sh all [tag] [base路径] [app路径]
#
# 未指定路径时查找: 当前目录 -> DIST_DIR -> 项目 docker/dist

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
# shellcheck source=lib/archive_paths.sh
source "${SCRIPT_DIR}/lib/archive_paths.sh"

MODE="${1:-all}"
ARG2="${2:-}"
ARG3="${3:-}"
ARG4="${4:-}"
APP_TAG="latest"
BASE_VERSION="${BASE_VERSION:-$(cat "${ROOT}/docker/BASE_VERSION" 2>/dev/null || echo 1.0)}"

load_archive() {
  local file="$1"
  local kind="${2:-}"
  if [[ "${kind}" == "base" ]]; then
    archive_validate_base_image "${file}"
  elif [[ "${kind}" == "app-delta" ]]; then
    archive_validate_app_delta "${file}"
  else
    archive_validate_loadable "${file}"
  fi
  echo "==> 加载 ${file}"
  gunzip -c "${file}" | docker load
}

resolve_base_file() {
  local explicit="${1:-}"
  archive_resolve_input "blogn2-base-${BASE_VERSION}.tar.gz" "${explicit}" "${ROOT}"
}

# 根据文件名判断 base / app 增量包（all 模式仅传一个路径时使用）
_archive_guess_kind() {
  local file="$1"
  local base
  base="$(basename "${file}")"
  if [[ "${base}" =~ ^blogn2-base-.+\.tar\.gz$ ]]; then
    echo "base"
  elif [[ "${base}" =~ ^blogn2-app-.+-delta\.tar\.gz$ ]] || [[ "${base}" =~ ^blogn2-app-.+\.tar\.gz$ ]]; then
    echo "app-delta"
  else
    echo "unknown"
  fi
}

resolve_app_file() {
  local tag="$1"
  local explicit="${2:-}"
  local delta_name="blogn2-app-${tag}-delta.tar.gz"
  local full_name="blogn2-app-${tag}.tar.gz"

  if [[ -n "${explicit}" ]]; then
    archive_resolve_input "$(basename "${explicit}")" "${explicit}" "${ROOT}"
    return
  fi

  local found=""
  if found="$( _archive_find_file "${delta_name}" "${PWD}" "${DIST_DIR:-}" "${ROOT}/docker/dist" )"; then
    printf '%s\n' "${found}"
    return 0
  fi
  if found="$( _archive_find_file "${full_name}" "${PWD}" "${DIST_DIR:-}" "${ROOT}/docker/dist" )"; then
    echo "提示: 使用完整 app 包（非增量）" >&2
    printf '%s\n' "${found}"
    return 0
  fi

  echo "错误: 找不到 ${delta_name} 或 ${full_name}" >&2
  echo "已搜索: ${PWD}  ${DIST_DIR:+(DIST_DIR=${DIST_DIR})}  ${ROOT}/docker/dist" >&2
  return 1
}

case "${MODE}" in
  base)
    load_archive "$(resolve_base_file "$( _archive_is_path "${ARG2}" && echo "${ARG2}" || echo "" )")" base
    ;;
  app)
    if _archive_is_path "${ARG2}"; then
      APP_TAG="latest"
      load_archive "$(resolve_app_file "${APP_TAG}" "${ARG2}")" app-delta
    else
      APP_TAG="${ARG2:-latest}"
      load_archive "$(resolve_app_file "${APP_TAG}" "$( _archive_is_path "${ARG3}" && echo "${ARG3}" || echo "" )")" app-delta
    fi
    ;;
  app-full)
    if _archive_is_path "${ARG2}"; then
      APP_TAG="latest"
      load_archive "$(archive_resolve_input "$(basename "${ARG2}")" "${ARG2}" "${ROOT}")"
    else
      APP_TAG="${ARG2:-latest}"
      load_archive "$(archive_resolve_input "blogn2-app-${APP_TAG}.tar.gz" "$( _archive_is_path "${ARG3}" && echo "${ARG3}" || echo "" )" "${ROOT}")"
    fi
    ;;
  all)
    if _archive_is_path "${ARG2}" && _archive_is_path "${ARG3}"; then
      APP_TAG="latest"
      load_archive "${ARG2}" base
      load_archive "${ARG3}" app-delta
    elif _archive_is_path "${ARG3}"; then
      APP_TAG="${ARG2:-latest}"
      load_archive "$(resolve_base_file "")" base
      load_archive "${ARG3}" app-delta
    elif _archive_is_path "${ARG2}"; then
      APP_TAG="latest"
      case "$( _archive_guess_kind "${ARG2}" )" in
        base)
          load_archive "${ARG2}" base
          load_archive "$(resolve_app_file "${APP_TAG}" "")" app-delta
          ;;
        app-delta)
          load_archive "$(resolve_base_file "")" base
          load_archive "${ARG2}" app-delta
          ;;
        *)
          echo "错误: 无法识别镜像包类型（须为 blogn2-base-*.tar.gz 或 blogn2-app-*.tar.gz）: ${ARG2}" >&2
          exit 1
          ;;
      esac
    else
      APP_TAG="${ARG2:-latest}"
      load_archive "$(resolve_base_file "")" base
      load_archive "$(resolve_app_file "${APP_TAG}" "")" app-delta
    fi
    ;;
  *)
    echo "用法: $0 {base|app|app-full|all} [tag] [tar.gz路径...]" >&2
    exit 1
    ;;
esac

echo ""
docker images blogn2-base blogn2-app --format "  {{.Repository}}:{{.Tag}}  {{.Size}}" 2>/dev/null || true
