# P图工具

自己写的测试代码 —— 一个基于 [Pillow](https://pillow.readthedocs.io/) 的命令行图片处理脚本。

## 功能

| 类别 | 功能 |
|------|------|
| 基础调整 | 亮度、对比度、饱和度、锐度 |
| 滤镜 | 模糊、描边、细节增强、边缘检测、浮雕、锐化、平滑、灰度 |
| 几何变换 | 缩放（保持/不保持比例）、裁剪、旋转、翻转 |
| 水印 | 文字水印（位置、字号可配置） |

## 依赖

```bash
pip install Pillow
```

## 用法

```
python p_image.py <输入图片> -o <输出图片> [选项]
```

### 示例

```bash
# 提升亮度和对比度，添加水印
python p_image.py input.jpg -o out.jpg --brightness 1.3 --contrast 1.2 --watermark "© 2024"

# 转为灰度，缩放到 800×600
python p_image.py input.jpg -o out.jpg --filter grayscale --resize 800 600

# 裁剪区域后旋转 15 度
python p_image.py input.jpg -o out.jpg --crop 100 50 800 600 --rotate 15

# 水平翻转
python p_image.py input.jpg -o out.jpg --flip horizontal

# 居中水印（字号 48）
python p_image.py input.jpg -o out.jpg --watermark "仅供内部使用" --watermark-position center --watermark-size 48
```

### 所有选项

```
基础调整 (1.0 为原始值):
  --brightness F    亮度系数
  --contrast F      对比度系数
  --saturation F    饱和度系数
  --sharpness F     锐度系数

滤镜:
  --filter NAME     blur | contour | detail | edge | emboss | sharpen | smooth | grayscale

几何变换:
  --resize W H      缩放到指定宽高（默认保持比例）
  --no-ratio        缩放时不保持宽高比
  --crop L T R B    裁剪区域（像素坐标）
  --rotate DEG      逆时针旋转角度
  --flip DIR        horizontal 或 vertical

水印:
  --watermark TEXT          水印文字
  --watermark-position POS  top-left / top-right / bottom-left / bottom-right / center
  --watermark-size PX       字号（默认 36）
```
