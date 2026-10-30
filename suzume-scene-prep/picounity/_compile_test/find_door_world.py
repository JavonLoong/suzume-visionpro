# -*- coding: utf-8 -*-
"""聚焦搜索：找门、门后世界（常世/星空/花海）相关对象。"""
import bpy
import sys
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")

KWS = {
    "门": ["门", "door", "門"],
    "常世/异世界": ["常世", "异世界", "異世界", "彼岸", "死后", "afterlife", "otherworld", "other_world"],
    "星空/夜空": ["星空", "夜空", "星", "star", "night"],
    "花海/草原": ["花海", "花丛", "草地", "草原", "flower", "meadow"],
    "水面/水": ["水面", "浅水", "海", "water", "sea", "pool"],
    "云": ["云", "雲", "cloud"],
    "光/发光": ["光", "发光", "light", "glow", "emission"],
    "白天/白天世界": ["白天", "日光", "daylight"],
    "夜晚": ["夜晚", "夜间", "月", "moon"],
    "铃芽/人物": ["铃芽", "suzume", "人物", "角色", "少女"],
    "相机": ["相机", "camera", "机位"],
}

matches = defaultdict(list)
for o in bpy.data.objects:
    n = o.name
    for label, kws in KWS.items():
        for k in kws:
            if k.lower() in n.lower():
                matches[label].append(n)
                break

for label in KWS:
    hits = matches.get(label, [])
    print(f"\n### {label}: {len(hits)} 个")
    for h in sorted(hits)[:25]:
        print(f"    {h}")

# 关键：找「相机」和「场景坐标」这类锚点，以及灯光对象
print("\n\n=== 所有 CAMERA 对象 ===")
for o in bpy.data.objects:
    if o.type == "CAMERA":
        loc = o.matrix_world.translation
        print(f"    {o.name}  位置=({loc.x:.2f},{loc.y:.2f},{loc.z:.2f})")

print("\n=== 所有 LIGHT 对象 ===")
for o in bpy.data.objects:
    if o.type == "LIGHT":
        loc = o.matrix_world.translation
        print(f"    {o.name}  type={o.data.type}  位置=({loc.x:.2f},{loc.y:.2f},{loc.z:.2f})")

print("\n=== 对象数按集合 ===")
for col in bpy.data.collections:
    print(f"    [{col.name}] {len(col.objects)}")

print("\n=== 所有集合名（完整）===")
for col in sorted([c.name for c in bpy.data.collections]):
    print(f"    {col}")

# 世界环境设置（门后世界可能是 world 或大 mesh）
print("\n=== 场景边界（全部 mesh 的包围盒）===")
import mathutils
mn = mathutils.Vector((1e9, 1e9, 1e9))
mx = mathutils.Vector((-1e9, -1e9, -1e9))
cnt = 0
for o in bpy.data.objects:
    if o.type == "MESH" and o.parent is None:
        try:
            for corner in o.bound_box:
                w = o.matrix_world @ mathutils.Vector(corner)
                mn.x = min(mn.x, w.x); mn.y = min(mn.y, w.y); mn.z = min(mn.z, w.z)
                mx.x = max(mx.x, w.x); mx.y = max(mx.y, w.y); mx.z = max(mx.z, w.z)
            cnt += 1
        except Exception:
            pass
print(f"  统计对象数={cnt}")
print(f"  min=({mn.x:.2f},{mn.y:.2f},{mn.z:.2f})")
print(f"  max=({mx.x:.2f},{mx.y:.2f},{mx.z:.2f})")
