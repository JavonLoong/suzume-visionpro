# -*- coding: utf-8 -*-
"""分析 Unity 桌面截图，判断 Scene 视图是否渲染出了门户几何体。"""
import sys
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")

img = Image.open(r"D:\虚拟C盘\JavonLoongSkill\suzume-scene-prep\picounity\preview\unity-editor-桌面.png").convert("RGB")
W, H = img.size
print(f"桌面截图: {W}x{H}")

# Unity 主窗口：找非桌面背景的大块区域。先按网格切分统计亮度分布
def region_stats(x0, y0, x1, y1, step=8):
    """返回该区域的：平均亮度、亮度标准差、亮像素占比(亮度>90)"""
    tot = 0; s = 0; s2 = 0; bright = 0
    for x in range(x0, x1, step):
        for y in range(y0, y1, step):
            r, g, b = img.getpixel((x, y))
            lum = 0.299 * r + 0.587 * g + 0.114 * b
            tot += 1; s += lum; s2 += lum * lum
            if lum > 90: bright += 1
    mean = s / tot
    var = s2 / tot - mean * mean
    return mean, (var ** 0.5), bright / tot

# 打印 6x4 网格，定位 Unity 窗口
print("\n亮度网格（行=上→下，列=左→右）: mean / std / bright%")
cols, rows = 6, 4
for r in range(rows):
    line = []
    for c in range(cols):
        x0 = W * c // cols; x1 = W * (c + 1) // cols
        y0 = H * r // rows; y1 = H * (r + 1) // rows
        m, sd, br = region_stats(x0, y0, x1, y1, step=16)
        line.append(f"{m:5.0f}/{sd:4.0f}/{br*100:3.0f}%")
    print("  ".join(line))

# 重点：找出最亮（几何体多为浅灰/白）的区域
print("\n最亮的几个区域（可能是门框等浅色几何）:")
best = []
for r in range(rows):
    for c in range(cols):
        x0 = W * c // cols; x1 = W * (c + 1) // cols
        y0 = H * r // rows; y1 = H * (r + 1) // rows
        m, sd, br = region_stats(x0, y0, x1, y1, step=8)
        best.append((m, sd, br, r, c, x0, y0, x1, y1))
best.sort(reverse=True)
for m, sd, br, r, c, x0, y0, x1, y1 in best[:5]:
    print(f"  行{r}列{c} 区域({x0},{y0})-({x1},{y1}): 亮度{m:.0f} 标准差{sd:.0f} 亮像素{br*100:.0f}%")
