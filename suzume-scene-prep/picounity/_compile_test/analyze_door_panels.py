# -*- coding: utf-8 -*-
"""几何分析：判断门的每个网格是否「覆盖门洞开口」。
原理：门洞开口是一个矩形区域（在门的平面内）。若某网格有面片的重心落在开口内部，
      说明它是盖住门洞的面板（门框的面片只会在开口四周，重心不会落在开口内部）。
用法: blender -b <file>.blend -P analyze_door_panels.py
"""
import bpy
import sys
import mathutils

sys.stdout.reconfigure(encoding="utf-8")

# 门洞开口（来自 空间门洞传送门开口.001：中心 (0, 0.072, 1.920)，尺寸 1.423 x 3.400）
OPEN_CX = 0.0
OPEN_CZ = 1.920
OPEN_HW = 1.423 / 2.0      # 半宽
OPEN_HH = 3.400 / 2.0      # 半高
OPEN_Y = 0.072
# 判定用的内缩边界（避免把开口边缘的面片误判）
MARGIN_X = 0.10
MARGIN_Z = 0.20


def in_opening(p):
    if abs(p.y - OPEN_Y) > 0.8:
        return False
    if abs(p.x - OPEN_CX) > (OPEN_HW - MARGIN_X):
        return False
    if abs(p.z - OPEN_CZ) > (OPEN_HH - MARGIN_Z):
        return False
    return True


# 收集门相关对象
names = set()
r = bpy.data.objects.get("完整六格白门与门框")
if r:
    stack = [r]
    while stack:
        o = stack.pop()
        names.add(o.name)
        stack.extend(o.children)
for pn in ["空间门洞传送门开口", "空间门洞传送门开口.001", "可开合门扇与铰链"]:
    o = bpy.data.objects.get(pn)
    if o:
        names.add(o.name)
        for c in o.children_recursive:
            names.add(c.name)

print("=" * 78)
print("门网格覆盖分析（面片重心落在门洞开口内 = 挡住门洞）")
print("=" * 78)
print(f"开口区域: x∈[{-OPEN_HW:.3f},{OPEN_HW:.3f}] z∈[{OPEN_CZ-OPEN_HH:.3f},{OPEN_CZ+OPEN_HH:.3f}] y≈{OPEN_Y}")
print(f"判定内缩: x±{OPEN_HW-MARGIN_X:.3f} z±{OPEN_HH-MARGIN_Z:.3f}")
print()

results = []
for name in sorted(names):
    o = bpy.data.objects.get(name)
    if o is None or o.type != "MESH":
        continue
    me = o.data
    mw = o.matrix_world
    total = len(me.polygons)
    inside = 0
    for poly in me.polygons:
        c = mw @ poly.center
        if in_opening(c):
            inside += 1
    ratio = inside / total if total else 0
    results.append((name, total, inside, ratio))

results.sort(key=lambda x: -x[3])
for name, total, inside, ratio in results:
    flag = "  <<< 挡住门洞" if ratio > 0.15 else ("  (部分)" if ratio > 0.02 else "")
    print(f"  {name:36s} 面片={total:6d} 落在开口内={inside:6d} 占比={ratio*100:5.1f}%{flag}")

print()
print("=" * 78)
print("建议：删除/隐藏「挡住门洞」的网格，保留门框")
print("=" * 78)
blockers = [n for n, t, i, r_ in results if r_ > 0.15]
keepers = [n for n, t, i, r_ in results if r_ <= 0.02]
print(f"挡住门洞（应隐藏）: {len(blockers)}")
for b in blockers:
    print("   -", b)
print(f"保留（门框等）: {len(keepers)}")
for k in keepers:
    print("   +", k)
