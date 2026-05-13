#!/usr/bin/env python3
"""从 SVG 栅格化生成站点分享图与 PNG favicon（与源 SVG 像素级一致）。

优先使用系统自带的 SVG 渲染器（与浏览器 / 微信预览更接近），按顺序尝试：
  1. rsvg-convert（librsvg，推荐，体量小）
  2. Inkscape
  3. ImageMagick（magick / convert）

若均不可用，回退到 Pillow 手绘（与 SVG 不完全一致）。

安装（Ubuntu / Debian / WSL）::

    # 推荐：仅命令行栅格化
    sudo apt update
    sudo apt install -y librsvg2-bin

    # 或：完整矢量工具（较大）
    sudo apt install -y inkscape

    # 或：ImageMagick（部分发行版需额外包才能读 SVG，不如前两者省心）
    sudo apt install -y imagemagick

用法::

    source ~/blogn2-env/bin/activate   # 回退分支需要 Pillow
    python3 scripts/generate_site_share_icon.py
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SVG_SHARE = ROOT / "src/static/images/logo-light.svg"
SVG_FAVICON = ROOT / "src/static/favicon.svg"
OUT_SHARE = ROOT / "src/static/images/site-share-icon.png"
OUT_FAVICON = ROOT / "src/static/favicon.png"

BG = "#0A66C2"
REG_FONTS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
]
BOLD_FONTS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
]


def _export_rsvg(svg: Path, png: Path, width: int, height: int) -> bool:
    exe = shutil.which("rsvg-convert")
    if not exe:
        return False
    png.parent.mkdir(parents=True, exist_ok=True)
    cmd = [exe, "-w", str(width), "-h", str(height), str(svg), "-o", str(png)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stderr or r.stdout or "rsvg-convert failed\n")
        return False
    return png.is_file()


def _export_inkscape(svg: Path, png: Path, width: int, height: int) -> bool:
    exe = shutil.which("inkscape")
    if not exe:
        return False
    png.parent.mkdir(parents=True, exist_ok=True)
    # Inkscape 1.x+
    cmd1 = [
        exe,
        "--export-type=png",
        f"--export-filename={png}",
        "-w",
        str(width),
        "-h",
        str(height),
        str(svg),
    ]
    r = subprocess.run(cmd1, capture_output=True, text=True)
    if r.returncode == 0 and png.is_file():
        return True
    # Inkscape 0.92
    cmd0 = [exe, "-z", "-e", str(png), "-w", str(width), "-h", str(height), str(svg)]
    r = subprocess.run(cmd0, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stderr or r.stdout or "inkscape failed\n")
        return False
    return png.is_file()


def _export_imagemagick(svg: Path, png: Path, width: int, height: int) -> bool:
    for name in ("magick", "convert"):
        exe = shutil.which(name)
        if not exe:
            continue
        png.parent.mkdir(parents=True, exist_ok=True)
        cmd = [exe, "-background", "none", str(svg), "-resize", f"{width}x{height}", str(png)]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0 and png.is_file():
            return True
        sys.stderr.write(r.stderr or r.stdout or f"{name} failed\n")
    return False


def export_svg_to_png(svg: Path, png: Path, width: int, height: int) -> bool:
    if not svg.is_file():
        print(f"Missing SVG: {svg}", file=sys.stderr)
        return False
    if _export_rsvg(svg, png, width, height):
        print(f"rsvg-convert -> {png} ({width}x{height})")
        return True
    if _export_inkscape(svg, png, width, height):
        print(f"inkscape -> {png} ({width}x{height})")
        return True
    if _export_imagemagick(svg, png, width, height):
        print(f"ImageMagick -> {png} ({width}x{height})")
        return True
    return False


def _load_font(paths: list[str], size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for p in paths:
        try:
            return ImageFont.truetype(p, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def render_logo_png_fallback(size: int, dest: Path) -> None:
    W = H = size
    rx = max(2, int(4 * W // 32))
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((0, 0, W - 1, H - 1), radius=rx, fill=BG)

    font_size = max(6, int(10 * W // 32))
    font_blog = _load_font(REG_FONTS, font_size)
    font_n = _load_font(BOLD_FONTS, font_size)

    text_blog, text_n = "Blog", "N"
    y_center = int(20 * H // 32)

    def text_w(font: ImageFont.ImageFont, t: str) -> float:
        if hasattr(draw, "textlength"):
            return float(draw.textlength(t, font=font))
        if hasattr(font, "getlength"):
            return float(font.getlength(t))
        return float(draw.textsize(t, font=font)[0])

    tw = text_w(font_blog, text_blog) + text_w(font_n, text_n)
    x0 = (W - tw) / 2
    _, top, _, bottom = draw.textbbox((0, 0), "Ay", font=font_blog)
    cap_h = bottom - top
    y = y_center - cap_h * 0.55

    draw.text((x0, y), text_blog, fill="white", font=font_blog)
    draw.text((x0 + text_w(font_blog, text_blog), y), text_n, fill="white", font=font_n)

    dest.parent.mkdir(parents=True, exist_ok=True)
    img.save(dest, format="PNG", optimize=True)
    print(f"Pillow fallback -> {dest} ({W}x{H})")


def main() -> None:
    ok_share = export_svg_to_png(SVG_SHARE, OUT_SHARE, 512, 512)
    if not ok_share:
        print("No SVG rasterizer found; install: sudo apt install -y librsvg2-bin", file=sys.stderr)
        render_logo_png_fallback(512, OUT_SHARE)

    ok_fav = export_svg_to_png(SVG_FAVICON, OUT_FAVICON, 32, 32)
    if not ok_fav:
        render_logo_png_fallback(32, OUT_FAVICON)


if __name__ == "__main__":
    main()
