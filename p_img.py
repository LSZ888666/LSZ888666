"""
P图 - 简单的图片编辑工具
支持功能：
  - 缩放 (resize)
  - 裁剪 (crop)
  - 旋转 (rotate)
  - 翻转 (flip)
  - 亮度 / 对比度 / 饱和度 调整
  - 模糊 (blur)
  - 锐化 (sharpen)
  - 灰度 (grayscale)
  - 添加文字水印 (watermark)
"""

import argparse
import sys
from pathlib import Path

try:
    from PIL import Image, ImageEnhance, ImageFilter, ImageDraw, ImageFont
except ImportError:
    sys.exit("请先安装 Pillow：pip install Pillow")


# ---------------------------------------------------------------------------
# 核心操作
# ---------------------------------------------------------------------------

def resize(img: Image.Image, width: int, height: int) -> Image.Image:
    """按指定宽高缩放图片（保持比例时传 0 给其中一个维度）。"""
    orig_w, orig_h = img.size
    if width == 0 and height == 0:
        raise ValueError("width 和 height 不能同时为 0")
    if width == 0:
        width = int(orig_w * height / orig_h)
    elif height == 0:
        height = int(orig_h * width / orig_w)
    return img.resize((width, height), Image.LANCZOS)


def crop(img: Image.Image, left: int, top: int, right: int, bottom: int) -> Image.Image:
    """裁剪图片。坐标为像素值，原点在左上角。"""
    return img.crop((left, top, right, bottom))


def rotate(img: Image.Image, angle: float, expand: bool = True) -> Image.Image:
    """旋转图片（逆时针，角度）。"""
    return img.rotate(angle, expand=expand)


def flip(img: Image.Image, direction: str) -> Image.Image:
    """翻转图片。direction: 'horizontal' | 'vertical'"""
    if direction == "horizontal":
        return img.transpose(Image.FLIP_LEFT_RIGHT)
    elif direction == "vertical":
        return img.transpose(Image.FLIP_TOP_BOTTOM)
    else:
        raise ValueError(f"未知翻转方向：{direction}")


def adjust_brightness(img: Image.Image, factor: float) -> Image.Image:
    """调整亮度。factor=1.0 为原始值，>1 变亮，<1 变暗。"""
    return ImageEnhance.Brightness(img).enhance(factor)


def adjust_contrast(img: Image.Image, factor: float) -> Image.Image:
    """调整对比度。factor=1.0 为原始值。"""
    return ImageEnhance.Contrast(img).enhance(factor)


def adjust_saturation(img: Image.Image, factor: float) -> Image.Image:
    """调整饱和度。factor=0 为灰度，1.0 为原始，>1 更鲜艳。"""
    return ImageEnhance.Color(img).enhance(factor)


def blur(img: Image.Image, radius: float = 2.0) -> Image.Image:
    """高斯模糊。"""
    return img.filter(ImageFilter.GaussianBlur(radius=radius))


def sharpen(img: Image.Image) -> Image.Image:
    """锐化图片。"""
    return img.filter(ImageFilter.SHARPEN)


def grayscale(img: Image.Image) -> Image.Image:
    """转为灰度图。"""
    return img.convert("L").convert("RGB")


def watermark(img: Image.Image, text: str, position: str = "bottom-right",
              opacity: int = 128, font_size: int = 36) -> Image.Image:
    """在图片上添加半透明文字水印。"""
    img = img.convert("RGBA")
    overlay = Image.new("RGBA", img.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)

    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except (IOError, OSError):
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    margin = 10
    img_w, img_h = img.size
    positions = {
        "top-left":     (margin, margin),
        "top-right":    (img_w - text_w - margin, margin),
        "bottom-left":  (margin, img_h - text_h - margin),
        "bottom-right": (img_w - text_w - margin, img_h - text_h - margin),
        "center":       ((img_w - text_w) // 2, (img_h - text_h) // 2),
    }
    xy = positions.get(position, positions["bottom-right"])
    draw.text(xy, text, font=font, fill=(255, 255, 255, opacity))
    result = Image.alpha_composite(img, overlay)
    return result.convert("RGB")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="p_img",
        description="P图 — 命令行图片编辑工具",
    )
    parser.add_argument("input", help="输入图片路径")
    parser.add_argument("output", help="输出图片路径")

    ops = parser.add_argument_group("操作（可叠加，按参数顺序依次执行）")
    ops.add_argument("--resize", metavar=("W", "H"), nargs=2, type=int,
                     help="缩放到指定尺寸（某一边传 0 表示按比例计算）")
    ops.add_argument("--crop", metavar=("LEFT", "TOP", "RIGHT", "BOTTOM"),
                     nargs=4, type=int, help="裁剪图片")
    ops.add_argument("--rotate", metavar="ANGLE", type=float,
                     help="逆时针旋转角度（度）")
    ops.add_argument("--flip", choices=["horizontal", "vertical"],
                     help="翻转方向")
    ops.add_argument("--brightness", metavar="FACTOR", type=float,
                     help="亮度因子（1.0=原始）")
    ops.add_argument("--contrast", metavar="FACTOR", type=float,
                     help="对比度因子（1.0=原始）")
    ops.add_argument("--saturation", metavar="FACTOR", type=float,
                     help="饱和度因子（1.0=原始）")
    ops.add_argument("--blur", metavar="RADIUS", type=float,
                     help="高斯模糊半径（像素）")
    ops.add_argument("--sharpen", action="store_true", help="锐化")
    ops.add_argument("--grayscale", action="store_true", help="转为灰度")
    ops.add_argument("--watermark", metavar="TEXT", help="添加文字水印")
    ops.add_argument("--watermark-position",
                     choices=["top-left", "top-right", "bottom-left",
                              "bottom-right", "center"],
                     default="bottom-right",
                     help="水印位置（默认 bottom-right）")
    ops.add_argument("--watermark-opacity", metavar="0-255", type=int,
                     default=128, help="水印不透明度（默认 128）")
    ops.add_argument("--watermark-font-size", metavar="SIZE", type=int,
                     default=36, help="水印字体大小（默认 36）")
    ops.add_argument("--quality", metavar="1-95", type=int, default=90,
                     help="JPEG 保存质量（默认 90）")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    input_path = Path(args.input)
    if not input_path.exists():
        parser.error(f"输入文件不存在：{args.input}")

    img = Image.open(input_path)

    # 执行各操作
    if args.resize:
        img = resize(img, args.resize[0], args.resize[1])
        print(f"[resize] → {img.size}")

    if args.crop:
        img = crop(img, *args.crop)
        print(f"[crop] → {img.size}")

    if args.rotate is not None:
        img = rotate(img, args.rotate)
        print(f"[rotate] {args.rotate}° → {img.size}")

    if args.flip:
        img = flip(img, args.flip)
        print(f"[flip] {args.flip}")

    if args.brightness is not None:
        img = adjust_brightness(img, args.brightness)
        print(f"[brightness] factor={args.brightness}")

    if args.contrast is not None:
        img = adjust_contrast(img, args.contrast)
        print(f"[contrast] factor={args.contrast}")

    if args.saturation is not None:
        img = adjust_saturation(img, args.saturation)
        print(f"[saturation] factor={args.saturation}")

    if args.blur is not None:
        img = blur(img, args.blur)
        print(f"[blur] radius={args.blur}")

    if args.sharpen:
        img = sharpen(img)
        print("[sharpen]")

    if args.grayscale:
        img = grayscale(img)
        print("[grayscale]")

    if args.watermark:
        img = watermark(img, args.watermark,
                        position=args.watermark_position,
                        opacity=args.watermark_opacity,
                        font_size=args.watermark_font_size)
        print(f"[watermark] '{args.watermark}' @ {args.watermark_position}")

    # 保存
    output_path = Path(args.output)
    save_kwargs = {}
    if output_path.suffix.lower() in (".jpg", ".jpeg"):
        save_kwargs["quality"] = args.quality
    img.save(output_path, **save_kwargs)
    print(f"已保存：{output_path}")


if __name__ == "__main__":
    main()
