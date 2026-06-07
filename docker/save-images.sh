#!/usr/bin/env bash
# 导出镜像 tar.gz，用于手动上传到远程主机后 load-images.sh 加载
# 文档: docker/README-DOCKER.md
#
# 用法:
#   ./save-images.sh base [输出路径]       # blogn2-base-1.0.tar.gz（约 380MB）
#   ./save-images.sh app [tag] [输出路径]  # blogn2-app-{tag}-delta.tar.gz（约 5–20MB）
#   ./save-images.sh app-full [tag] [输出路径]
#   ./save-images.sh all [tag]
#
# 导出包请放在项目外（如 ~/docker），勿放在 docker/docker/ 以免打进 app 镜像。
# 环境变量 OUT_DIR：未指定输出路径时的默认目录（默认当前目录）。

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
# shellcheck source=lib/archive_paths.sh
source "${SCRIPT_DIR}/lib/archive_paths.sh"

MODE="${1:-all}"
ARG2="${2:-}"
ARG3="${3:-}"
APP_TAG="latest"
BASE_VERSION="${BASE_VERSION:-$(cat "${ROOT}/docker/BASE_VERSION")}"
BASE_IMAGE="blogn2-base:${BASE_VERSION}"
APP_IMAGE="blogn2-app:${APP_TAG}"

save_image() {
  local name="$1"
  local tag="$2"
  local outfile="$3"
  local ref="${name}:${tag}"
  if ! docker image inspect "${ref}" >/dev/null 2>&1; then
    echo "错误: 未找到镜像 ${ref}" >&2
    if [[ "${name}" == "blogn2-base" ]]; then
      echo "请先执行: ./docker/build-base.sh" >&2
      echo "或确认 BASE_VERSION（当前 ${BASE_VERSION}）与 docker images 中的 tag 一致" >&2
    fi
    docker images "${name}" --format '  已有: {{.Repository}}:{{.Tag}}' 2>/dev/null || true
    exit 1
  fi
  local tmp_tar
  tmp_tar="$(mktemp "${outfile%.tar.gz}.XXXXXX.tar")"

  echo "==> docker save ${ref}"
  docker save "${ref}" -o "${tmp_tar}"
  if ! archive_validate_tar "${tmp_tar}"; then
    rm -f "${tmp_tar}"
    exit 1
  fi

  echo "==> 压缩 -> ${outfile}"
  gzip -1 -c "${tmp_tar}" > "${outfile}"
  rm -f "${tmp_tar}"
  ls -lh "${outfile}"

  if [[ "${name}" == "blogn2-base" ]]; then
    archive_validate_base_image "${outfile}"
  else
    archive_validate_loadable "${outfile}"
  fi
  echo "    校验通过"
}

save_app_delta() {
  local outfile="$1"
  if ! docker image inspect "${BASE_IMAGE}" >/dev/null 2>&1; then
    echo "错误: 未找到 ${BASE_IMAGE}，请先 ./docker/build-base.sh" >&2
    exit 1
  fi
  if ! docker image inspect "${APP_IMAGE}" >/dev/null 2>&1; then
    echo "错误: 未找到 ${APP_IMAGE}，请先 ./docker/build-app.sh ${APP_TAG}" >&2
    exit 1
  fi
  echo "==> 导出应用增量包 ${APP_IMAGE}（相对 ${BASE_IMAGE}）"
  echo "    输出: ${outfile}"
  echo "    提示: 导出包请放在项目外或 docker/dist/，勿放在 docker/docker/ 以免被打进镜像"
  python3 "${ROOT}/docker/save_app_delta.py" \
    --app "${APP_IMAGE}" \
    --base "${BASE_IMAGE}" \
    -o "${outfile}"
  ls -lh "${outfile}"
}

parse_app_args() {
  if _archive_is_path "${ARG2}"; then
    APP_TAG="latest"
    APP_OUT="$(archive_resolve_output "blogn2-app-${APP_TAG}-delta.tar.gz" "${ARG2}")"
  else
    APP_TAG="${ARG2:-latest}"
    APP_IMAGE="blogn2-app:${APP_TAG}"
    APP_OUT="$(archive_resolve_output "blogn2-app-${APP_TAG}-delta.tar.gz" "$( _archive_is_path "${ARG3}" && echo "${ARG3}" || echo "" )")"
  fi
}

case "${MODE}" in
  base)
    BASE_OUT="$(archive_resolve_output "blogn2-base-${BASE_VERSION}.tar.gz" "$( _archive_is_path "${ARG2}" && echo "${ARG2}" || echo "" )")"
    save_image blogn2-base "${BASE_VERSION}" "${BASE_OUT}"
    ;;
  app)
    parse_app_args
    save_app_delta "${APP_OUT}"
    ;;
  app-full)
    if _archive_is_path "${ARG2}"; then
      APP_TAG="latest"
      APP_IMAGE="blogn2-app:${APP_TAG}"
      FULL_OUT="$(archive_resolve_output "blogn2-app-${APP_TAG}.tar.gz" "${ARG2}")"
    else
      APP_TAG="${ARG2:-latest}"
      APP_IMAGE="blogn2-app:${APP_TAG}"
      FULL_OUT="$(archive_resolve_output "blogn2-app-${APP_TAG}.tar.gz" "$( _archive_is_path "${ARG3}" && echo "${ARG3}" || echo "" )")"
    fi
    save_image blogn2-app "${APP_TAG}" "${FULL_OUT}"
    ;;
  all)
    BASE_OUT="$(archive_resolve_output "blogn2-base-${BASE_VERSION}.tar.gz" "")"
    parse_app_args
    save_image blogn2-base "${BASE_VERSION}" "${BASE_OUT}"
    save_app_delta "${APP_OUT}"
    ;;
  *)
    echo "用法: $0 {base|app|app-full|all} [tag] [输出路径]" >&2
    exit 1
    ;;
esac

echo ""
echo "导出完成"
