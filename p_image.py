#!/usr/bin/env python3
"""
P图工具 - 简单的图片处理脚本
支持亮度/对比度/饱和度调整、滤镜、缩放、裁剪、旋转和添加水印
"""

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageDraw, ImageFont


# ─────────────────────── 基础调整 ───────────────────────

def adjust_brightness(img: Image.Image, factor: float) -> Image.Image:
    """调整亮度，factor=1.0 为原始亮度"""
    return ImageEnhance.Brightness(img).enhance(factor)


def adjust_contrast(img: Image.Image, factor: float) -> Image.Image:
    """调整对比度，factor=1.0 为原始对比度"""
    return ImageEnhance.Contrast(img).enhance(factor)


def adjust_saturation(img: Image.Image, factor: float) -> Image.Image:
    """调整饱和度，factor=1.0 为原始饱和度，factor=0 为灰度"""
    return ImageEnhance.Color(img).enhance(factor)


def adjust_sharpness(img: Image.Image, factor: float) -> Image.Image:
    """调整锐度，factor=1.0 为原始锐度"""
    return ImageEnhance.Sharpness(img).enhance(factor)


# ─────────────────────── 滤镜 ───────────────────────

FILTERS = {
    "blur":       ImageFilter.BLUR,
    "contour":    ImageFilter.CONTOUR,
    "detail":     ImageFilter.DETAIL,
    "edge":       ImageFilter.FIND_EDGES,
    "emboss":     ImageFilter.EMBOSS,
    "sharpen":    ImageFilter.SHARPEN,
    "smooth":     ImageFilter.SMOOTH,
    "grayscale":  None,   # 特殊处理
}


def apply_filter(img: Image.Image, name: str) -> Image.Image:
    """应用滤镜"""
    if name not in FILTERS:
        raise ValueError(f"未知滤镜 '{name}'，可选: {', '.join(FILTERS)}")
    if name == "grayscale":
        return img.convert("L").convert("RGB")
    return img.filter(FILTERS[name])


# ─────────────────────── 几何变换 ───────────────────────

def resize_image(img: Image.Image, width: int, height: int, keep_ratio: bool = True) -> Image.Image:
    """缩放图片"""
    if keep_ratio:
        img.thumbnail((width, height), Image.LANCZOS)
        return img
    return img.resize((width, height), Image.LANCZOS)


def crop_image(img: Image.Image, left: int, top: int, right: int, bottom: int) -> Image.Image:
    """裁剪图片（像素坐标）"""
    return img.crop((left, top, right, bottom))


def rotate_image(img: Image.Image, angle: float, expand: bool = True) -> Image.Image:
    """旋转图片，expand=True 自动扩展画布以显示完整图片"""
    return img.rotate(angle, expand=expand, resample=Image.BICUBIC)


def flip_image(img: Image.Image, direction: str) -> Image.Image:
    """翻转图片，direction='horizontal' 或 'vertical'"""
    if direction == "horizontal":
        return img.transpose(Image.FLIP_LEFT_RIGHT)
    if direction == "vertical":
        return img.transpose(Image.FLIP_TOP_BOTTOM)
    raise ValueError("direction 必须是 'horizontal' 或 'vertical'")


# ─────────────────────── 水印 ───────────────────────

def add_text_watermark(
    img: Image.Image,
    text: str,
    position: str = "bottom-right",
    color: tuple = (255, 255, 255, 160),
    font_size: int = 36,
) -> Image.Image:
    """在图片上添加文字水印"""
    rgba = img.convert("RGBA")
    overlay = Image.new("RGBA", rgba.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except OSError:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    w, h = rgba.size
    padding = 10

    positions = {
        "top-left":     (padding, padding),
        "top-right":    (w - text_w - padding, padding),
        "bottom-left":  (padding, h - text_h - padding),
        "bottom-right": (w - text_w - padding, h - text_h - padding),
        "center":       ((w - text_w) // 2, (h - text_h) // 2),
    }
    if position not in positions:
        raise ValueError(f"未知位置 '{position}'，可选: {', '.join(positions)}")

    draw.text(positions[position], text, font=font, fill=color)
    result = Image.alpha_composite(rgba, overlay)
    return result.convert("RGB")


# ─────────────────────── CLI ───────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="p_image",
        description="P图工具 – 图片处理命令行工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""示例:
  # 调整亮度和对比度
  python p_image.py input.jpg -o out.jpg --brightness 1.3 --contrast 1.2

  # 转为灰度 + 添加水印
  python p_image.py input.jpg -o out.jpg --filter grayscale --watermark "© 2024"

  # 缩放到 800x600 并旋转 15 度
  python p_image.py input.jpg -o out.jpg --resize 800 600 --rotate 15

  # 裁剪区域 (left top right bottom)
  python p_image.py input.jpg -o out.jpg --crop 100 50 800 600
""",
    )

    parser.add_argument("input", help="输入图片路径")
    parser.add_argument("-o", "--output", required=True, help="输出图片路径")

    # 基础调整
    adj = parser.add_argument_group("基础调整 (1.0 为原始值)")
    adj.add_argument("--brightness", type=float, metavar="F", help="亮度系数")
    adj.add_argument("--contrast",   type=float, metavar="F", help="对比度系数")
    adj.add_argument("--saturation", type=float, metavar="F", help="饱和度系数")
    adj.add_argument("--sharpness",  type=float, metavar="F", help="锐度系数")

    # 滤镜
    flt = parser.add_argument_group("滤镜")
    flt.add_argument("--filter", choices=list(FILTERS), metavar="NAME",
                     help=f"滤镜名称: {', '.join(FILTERS)}")

    # 几何变换
    geo = parser.add_argument_group("几何变换")
    geo.add_argument("--resize",   nargs=2, type=int, metavar=("W", "H"), help="缩放到指定宽高（保持比例）")
    geo.add_argument("--no-ratio", action="store_true", help="缩放时不保持宽高比（与 --resize 配合）")
    geo.add_argument("--crop",     nargs=4, type=int, metavar=("L", "T", "R", "B"), help="裁剪区域")
    geo.add_argument("--rotate",   type=float, metavar="DEG", help="旋转角度（逆时针）")
    geo.add_argument("--flip",     choices=["horizontal", "vertical"], help="翻转方向")

    # 水印
    wm = parser.add_argument_group("水印")
    wm.add_argument("--watermark",          metavar="TEXT", help="水印文字")
    wm.add_argument("--watermark-position", metavar="POS",
                    default="bottom-right",
                    help="水印位置: top-left / top-right / bottom-left / bottom-right / center")
    wm.add_argument("--watermark-size",     type=int, default=36, metavar="PX", help="水印字号")

    return parser


def process(args: argparse.Namespace) -> None:
    src = Path(args.input)
    if not src.exists():
        print(f"错误: 文件不存在 '{src}'", file=sys.stderr)
        sys.exit(1)

    img = Image.open(src)
    print(f"已打开: {src}  尺寸={img.size}  模式={img.mode}")

    # 基础调整
    if args.brightness is not None:
        img = adjust_brightness(img, args.brightness)
        print(f"  亮度调整: {args.brightness}")
    if args.contrast is not None:
        img = adjust_contrast(img, args.contrast)
        print(f"  对比度调整: {args.contrast}")
    if args.saturation is not None:
        img = adjust_saturation(img, args.saturation)
        print(f"  饱和度调整: {args.saturation}")
    if args.sharpness is not None:
        img = adjust_sharpness(img, args.sharpness)
        print(f"  锐度调整: {args.sharpness}")

    # 滤镜
    if args.filter:
        img = apply_filter(img, args.filter)
        print(f"  滤镜: {args.filter}")

    # 几何变换
    if args.resize:
        w, h = args.resize
        img = resize_image(img, w, h, keep_ratio=not args.no_ratio)
        print(f"  缩放 → {img.size}")
    if args.crop:
        img = crop_image(img, *args.crop)
        print(f"  裁剪 → {img.size}")
    if args.rotate is not None:
        img = rotate_image(img, args.rotate)
        print(f"  旋转: {args.rotate}°  新尺寸={img.size}")
    if args.flip:
        img = flip_image(img, args.flip)
        print(f"  翻转: {args.flip}")

    # 水印
    if args.watermark:
        img = add_text_watermark(
            img,
            args.watermark,
            position=args.watermark_position,
            font_size=args.watermark_size,
        )
        print(f"  水印: '{args.watermark}'  位置={args.watermark_position}")

    # 保存
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    print(f"已保存: {out}")


def main() -> None:
    parser = build_parser()
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)
    args = parser.parse_args()
    process(args)


if __name__ == "__main__":
    main()
