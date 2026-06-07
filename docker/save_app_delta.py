#!/usr/bin/env python3
"""导出 blogn2-app 相对 blogn2-base 的增量层（供 docker load，远程须已 load base）。"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile


def inspect_layers(image_ref: str) -> list[str]:
    out = subprocess.check_output(
        ["docker", "image", "inspect", image_ref, "--format", "{{json .RootFS.Layers}}"],
    )
    return json.loads(out.decode())


def save_delta(app_ref: str, base_ref: str, output_gz: str) -> None:
    base_layers = inspect_layers(base_ref)
    app_layers = inspect_layers(app_ref)

    if len(app_layers) < len(base_layers):
        raise SystemExit(f"错误: {app_ref} 层数({len(app_layers)}) 少于 {base_ref}({len(base_layers)})")

    if app_layers[: len(base_layers)] != base_layers:
        print(
            f"错误: {app_ref} 不是由 {base_ref} 构建，无法生成小体积增量包。",
            file=sys.stderr,
        )
        print("请先执行: ./docker/build-app.sh", file=sys.stderr)
        raise SystemExit(1)

    extra_count = len(app_layers) - len(base_layers)

    with tempfile.TemporaryDirectory() as tmp:
        full_tar = os.path.join(tmp, "full.tar")
        subprocess.check_call(["docker", "save", app_ref, "-o", full_tar])

        extract = os.path.join(tmp, "extract")
        os.makedirs(extract)
        with tarfile.open(full_tar) as archive:
            archive.extractall(extract)

        manifest_path = os.path.join(extract, "manifest.json")
        with open(manifest_path, encoding="utf-8") as handle:
            manifest = json.load(handle)

        if not manifest:
            raise SystemExit("manifest.json 为空")

        entry = manifest[0]
        layer_paths = entry["Layers"]
        if len(layer_paths) != len(app_layers):
            raise SystemExit(
                f"manifest 层数({len(layer_paths)}) 与镜像层数({len(app_layers)}) 不一致"
            )

        needed_blobs: set[str] = set()
        needed_blobs.add(entry["Config"].split("/")[-1])
        for layer_path in layer_paths[-extra_count:]:
            needed_blobs.add(layer_path.split("/")[-1])

        out_dir = os.path.join(tmp, "delta")
        blob_dir = os.path.join(out_dir, "blobs", "sha256")
        os.makedirs(blob_dir, exist_ok=True)

        total_bytes = 0
        for digest in sorted(needed_blobs):
            src = os.path.join(extract, "blobs", "sha256", digest)
            if not os.path.isfile(src):
                raise SystemExit(f"缺少 blob: {digest}")
            dst = os.path.join(blob_dir, digest)
            shutil.copy2(src, dst)
            total_bytes += os.path.getsize(src)

        for meta in ("manifest.json", "index.json", "oci-layout"):
            src = os.path.join(extract, meta)
            if os.path.isfile(src):
                shutil.copy2(src, os.path.join(out_dir, meta))

        delta_tar = os.path.join(tmp, "delta.tar")
        with tarfile.open(delta_tar, "w") as archive:
            for name in sorted(os.listdir(out_dir)):
                path = os.path.join(out_dir, name)
                archive.add(path, arcname=name)

        os.makedirs(os.path.dirname(os.path.abspath(output_gz)), exist_ok=True)
        with open(delta_tar, "rb") as src_handle, gzip.open(output_gz, "wb", compresslevel=1) as dst_handle:
            shutil.copyfileobj(src_handle, dst_handle)

    compressed_mb = os.path.getsize(output_gz) / 1024 / 1024
    raw_mb = total_bytes / 1024 / 1024
    print(f"增量层数: {extra_count}，blob 合计: {raw_mb:.1f} MB -> {output_gz} ({compressed_mb:.1f} MB 压缩)")
    if raw_mb > 50:
        print(
            "警告: 增量包偏大，常见原因是镜像里 COPY 进了 tar.gz 等大文件。",
            file=sys.stderr,
        )
        print(
            "请检查 .dockerignore，并重建: ./docker/build-app.sh",
            file=sys.stderr,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="导出 app 相对 base 的增量 docker load 包")
    parser.add_argument("--app", required=True, help="应用镜像，如 blogn2-app:latest")
    parser.add_argument("--base", required=True, help="基础镜像，如 blogn2-base:1.0")
    parser.add_argument("-o", "--output", required=True, help="输出 .tar.gz 路径")
    args = parser.parse_args()
    save_delta(args.app, args.base, args.output)


if __name__ == "__main__":
    main()
