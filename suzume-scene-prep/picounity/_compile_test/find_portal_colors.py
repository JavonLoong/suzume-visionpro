# -*- coding: utf-8 -*-
"""在 Unity 窗口截图里找门户特征色，确认 Scene 视图渲染出了门与门后世界。"""
import sys
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")

img = Image.open(r"D:\虚拟C盘\JavonLoongSkill\suzume-scene-prep\picounity\preview\unity-editor-窗口.png").convert("RGB")
W, H = img.size
print(f"窗口截图: {W}x{H}")

px = img.load()

def close(c, t, tol=26):
    return all(abs(c[i] - t[i]) <= tol for i in range(3))

TARGETS = {
    "门框近白": (255, 250, 219),
    "门内夜空": (15, 20, 56),
    "门内水面": (89, 153, 178),
    "门外背景": (25, 33, 48),
}

counts = {k: [] for k in TARGETS}
for y in range(0, H, 2):
    for x in range(0, W, 2):
        c = px[x, y]
        for name, t in TARGETS.items():
            if close(c, t):
                counts[name].append((x, y))

for name, pts in counts.items():
    if pts:
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        print(f"  {name}: {len(pts)} 点, x∈[{min(xs)},{max(xs)}], y∈[{min(ys)},{max(ys)}]")
    else:
        print(f"  {name}: 0 点")

# 判断 Scene 视图区域（一般左上 2/3）
print()
print("结论：")
if counts["门框近白"]:
    print("  ✅ Scene 视图里有门框（近白色块）")
if counts["门内夜空"]:
    print("  ✅ Scene 视图里有门洞内的夜空（深蓝色块）")
if not counts["门框近白"] and not counts["门内夜空"]:
    print("  ❌ 未在窗口里找到门户特征色，可能 Scene 视图没显示或需要调整视角")
