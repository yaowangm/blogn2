# 镜像包路径解析与校验（由 save-images.sh / load-images.sh source）
# base：完整 docker save 包；app-delta：save_app_delta.py 生成的增量包

# 判断参数是否为文件路径
_archive_is_path() {
  local arg="${1:-}"
  [[ -z "${arg}" ]] && return 1
  [[ "${arg}" == */* || "${arg}" == *.tar.gz || "${arg}" == *.tgz ]]
}

# 在多个目录中查找文件，找到则输出绝对路径
_archive_find_file() {
  local name="$1"
  shift
  local dir candidate
  for dir in "$@"; do
    [[ -z "${dir}" ]] && continue
    candidate="${dir%/}/${name}"
    if [[ -f "${candidate}" ]]; then
      printf '%s\n' "$(cd "$(dirname "${candidate}")" && pwd)/$(basename "${candidate}")"
      return 0
    fi
  done
  return 1
}

# 解析输入包路径：显式参数 > 当前目录 > DIST_DIR > 项目 docker/dist
archive_resolve_input() {
  local default_name="$1"
  local explicit="${2:-}"
  local script_root="${3:-}"
  local dist_dir="${DIST_DIR:-}"
  local found=""

  if [[ -n "${explicit}" ]]; then
    if [[ ! -f "${explicit}" ]]; then
      echo "错误: 找不到文件 ${explicit}" >&2
      return 1
    fi
    printf '%s\n' "${explicit}"
    return 0
  fi

  if found="$( _archive_find_file "${default_name}" "${PWD}" "${dist_dir}" "${script_root}/docker/dist" )"; then
    printf '%s\n' "${found}"
    return 0
  fi

  echo "错误: 找不到 ${default_name}" >&2
  echo "已搜索: ${PWD}  ${dist_dir:+(DIST_DIR=${dist_dir})}  ${script_root}/docker/dist" >&2
  echo "用法: 指定文件路径，例如: $0 ... /path/to/${default_name}" >&2
  return 1
}

# 解析输出路径：显式参数 > 当前目录下的默认文件名
archive_resolve_output() {
  local default_name="$1"
  local explicit="${2:-}"
  local out_dir="${OUT_DIR:-${PWD}}"

  if [[ -n "${explicit}" ]]; then
    mkdir -p "$(dirname "${explicit}")"
    printf '%s\n' "${explicit}"
    return 0
  fi

  mkdir -p "${out_dir}"
  printf '%s\n' "${out_dir%/}/${default_name}"
}

# 列出 tar 内路径（去掉 ./ 前缀）
_archive_list_tar_paths_from_file() {
  tar -tf "${1}" 2>/dev/null | sed 's|^\./||'
}

_archive_list_tar_paths() {
  gunzip -c "${1}" 2>/dev/null | tar -tf - 2>/dev/null | sed 's|^\./||'
}

# 判断 tar 列表是否为可 docker load 的镜像包
_archive_listing_is_loadable() {
  local listing="$1"
  local paths

  [[ -z "${listing}" ]] && return 1

  paths="$(printf '%s\n' "${listing}" | sed 's|/.*||' | sort -u)"
  if printf '%s\n' "${paths}" | grep -qxE 'manifest\.json|repositories|oci-layout|index\.json'; then
    return 0
  fi
  if printf '%s\n' "${listing}" | grep -qE '(^|/)manifest\.json$|(^|/)repositories$|(^|/)oci-layout$|(^|/)index\.json$'; then
    return 0
  fi
  # 旧版 docker save：repositories + <id>/layer.tar
  if printf '%s\n' "${listing}" | grep -qx 'repositories' && \
     printf '%s\n' "${listing}" | grep -qE '/layer\.tar$'; then
    return 0
  fi
  return 1
}

_archive_listing_error() {
  local file="$1"
  local listing="$2"
  local kind="${3:-}"

  if printf '%s\n' "${listing}" | grep -q 'blobs/sha256/' && \
     ! _archive_listing_is_loadable "${listing}"; then
    if [[ "${kind}" == "app-delta" ]]; then
      echo "错误: ${file} 不是有效的 app 增量包（仅有 blobs/，缺少 manifest.json）" >&2
      echo "原因: 可能是旧版导出、或镜像里误打包了 tar.gz 导致增量过大且结构异常" >&2
      echo "处理: 在构建机执行:" >&2
      echo "  ./docker/build-app.sh latest" >&2
      echo "  ./docker/save-images.sh app latest" >&2
      echo "远程须先: ./load-images.sh base" >&2
    else
      echo "错误: ${file} 仅有 blobs/，缺少 manifest.json / oci-layout / index.json" >&2
      echo "原因: docker save 不完整（常见于管道导出大镜像被截断）" >&2
      echo "处理: 在构建机用 save-images.sh base 重新导出" >&2
    fi
    _archive_print_listing_preview "${listing}"
    return 1
  fi

  if [[ "${kind}" == "app-delta" ]]; then
    echo "错误: ${file} 不是有效的 app 增量包" >&2
    echo "处理: 在构建机 ./docker/save-images.sh app latest 重新导出" >&2
    echo "远程须先加载 base: ./load-images.sh base" >&2
  else
    echo "错误: ${file} 不是有效的 docker load 包（缺少 manifest.json / repositories / oci-layout）" >&2
    echo "提示: 在构建机执行 save-images.sh base 重新导出后上传" >&2
  fi
  _archive_print_listing_preview "${listing}"
  return 1
}

# 校验未压缩的 docker save tar
archive_validate_tar() {
  local file="$1"
  local listing

  listing="$(_archive_list_tar_paths_from_file "${file}")" || listing=""
  if [[ -z "${listing}" ]]; then
    echo "错误: ${file} 无法读取 tar 内容" >&2
    return 1
  fi
  if _archive_listing_is_loadable "${listing}"; then
    return 0
  fi
  _archive_listing_error "${file}" "${listing}"
}

# 加载前校验 tar.gz 结构
archive_validate_loadable() {
  local file="$1"
  local kind="${2:-}"
  local listing

  if ! gunzip -t "${file}" 2>/dev/null; then
    echo "错误: ${file} 不是有效的 gzip 文件（可能上传不完整）" >&2
    return 1
  fi

  listing="$(_archive_list_tar_paths "${file}")" || listing=""
  if [[ -z "${listing}" ]]; then
    echo "错误: ${file} 无法读取 tar 内容（gzip 正常但内部不是 tar 归档）" >&2
    return 1
  fi
  if _archive_listing_is_loadable "${listing}"; then
    return 0
  fi
  _archive_listing_error "${file}" "${listing}" "${kind}"
}

# app 增量包校验（须已 load base）
archive_validate_app_delta() {
  local file="$1"
  archive_validate_loadable "${file}" "app-delta" || return 1

  local size
  size="$(stat -c%s "${file}" 2>/dev/null || stat -f%z "${file}" 2>/dev/null || echo 0)"
  if [[ "${size}" -gt 104857600 ]]; then
    echo "警告: ${file} 体积较大（>100MB），可能不是正确的增量包" >&2
    echo "正常增量约 5–20MB；若过大请在构建机重建 app 并重新 save-images.sh app" >&2
  fi
}

# base 包额外检查：体积过小多半是增量包或损坏
archive_validate_base_image() {
  local file="$1"
  archive_validate_loadable "${file}" || return 1

  local size blob_count
  size="$(stat -c%s "${file}" 2>/dev/null || stat -f%z "${file}" 2>/dev/null || echo 0)"
  blob_count="$( _archive_list_tar_paths "${file}" | grep -c 'blobs/sha256/' || true)"

  if [[ "${size}" -lt 52428800 ]]; then
    echo "错误: ${file} 仅 $(numfmt --to=iec-i --suffix=B "${size}" 2>/dev/null || echo "${size} bytes")，不像完整 base 包（通常 > 50MB）" >&2
    echo "提示: 若这是 app 增量包，请用 load-images.sh app；base 须 save-images.sh base 导出" >&2
    return 1
  fi
  if [[ "${blob_count}" -gt 0 && "${blob_count}" -lt 8 ]]; then
    echo "错误: ${file} 仅含 ${blob_count} 个 blob，像是 app 增量包而非 base" >&2
    return 1
  fi
}

_archive_print_listing_preview() {
  local listing="$1"
  echo "包内文件预览（前 15 项）:" >&2
  printf '%s\n' "${listing}" | head -15 | sed 's/^/  /' >&2
  local count
  count="$(printf '%s\n' "${listing}" | wc -l)"
  if [[ "${count}" -gt 15 ]]; then
    echo "  ... 共 ${count} 项" >&2
  fi
}
