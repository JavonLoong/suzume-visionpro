# -*- coding: utf-8 -*-
import sys
from PIL import Image
sys.stdout.reconfigure(encoding="utf-8")

img = Image.open(r"d:\Users\15410\AppData\Local\Temp\cursor\screenshots\portal-preview-check.png").convert("RGB")
w, h = img.size
print(f"image size: {w}x{h}")

def px(x, y):
    return img.getpixel((int(x), int(y)))

# 采样几个点：中心（门洞）、上方（门框上梁）、左外侧（门外地面）、门洞中心偏下（花海/水面）
samples = {
    "中心(门洞中)": (0.50, 0.45),
    "门洞上沿外(门框)": (0.50, 0.16),
    "左外侧(门外地面)": (0.15, 0.80),
    "右外侧(门外地面)": (0.85, 0.80),
    "门洞下(水面区)": (0.50, 0.75),
}
for name, (fx, fy) in samples.items():
    r, g, b = px(w*fx, h*fy)
    print(f"  {name:22s} ({fx:.2f},{fy:.2f}) -> RGB({r},{g},{b})")

# 统计：门洞中心区域 vs 门外区域的色彩饱和程度
def region_stats(cx, cy, r=0.08):
    x0, x1 = int(w*(cx-r)), int(w*(cx+r))
    y0, y1 = int(h*(cy-r)), int(h*(cy+r))
    tot = 0; sat = 0
    for x in range(x0, x1, 4):
        for y in range(y0, y1, 4):
            rr, gg, bb = px(x, y)
            mx, mn = max(rr,gg,bb), min(rr,gg,bb)
            if mx > 0:
                sat += (mx - mn) / mx
            tot += 1
    return round(sat/tot, 3) if tot else 0

print("\n饱和度和(0=纯灰, 越大越彩色):")
print("  门洞内中心:", region_stats(0.50, 0.45))
print("  门外左下 :", region_stats(0.18, 0.78))
print("  门外右下 :", region_stats(0.82, 0.78))
