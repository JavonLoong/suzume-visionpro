# -*- coding: utf-8 -*-
"""检查铃芽 v56 场景的对象结构，找出「门后梦幻世界」相关的对象。
用法: blender -b <file>.blend -P inspect_scene.py
"""
import bpy
import sys
import json

print("=" * 70)
print("SCENE INSPECT START")
print("=" * 70)

scene = bpy.context.scene
print(f"Scene: {scene.name}")
print(f"Total objects: {len(bpy.data.objects)}")

# 按集合分组
print("\n=== Collections ===")
def walk_collection(col, depth=0):
    objs = [o.name for o in col.objects]
    print("  " * depth + f"[{col.name}] objects={len(objs)}")
    if objs and depth <= 2:
        preview = objs[:8]
        print("  " * (depth + 1) + " 例: " + ", ".join(preview) + (" ..." if len(objs) > 8 else ""))
    for c in col.children:
        walk_collection(c, depth + 1)
walk_collection(scene.collection)

# 顶层对象
print("\n=== 顶层对象（无父级）===")
roots = [o for o in bpy.data.objects if o.parent is None]
for o in sorted(roots, key=lambda x: x.name):
    nchild = len(o.children_recursive)
    print(f"  {o.name:45s} type={o.type:10s} children={nchild}")

# 关键词分类
print("\n=== 关键词命中 ===")
KWS = {
    "门/Door": ["door", "gate", "门"],
    "水面/Water": ["water", "pool", "水面", "池", "sea", "lake"],
    "花/Flower": ["flower", "花", "grass", "草", "plant", "植"],
    "星空/Sky": ["star", "sky", "night", "cloud", "云", "星", "夜"],
    "建筑/Building": ["wall", "build", "roof", "arch", "window", "廊", "墙", "楼"],
    "人物/Character": ["suzume", "铃芽", "char", "body", "head", "hair"],
    "常世/OtherWorld": ["常世", "other", "dream", "world", "afterlife", "异"],
    "钢架/Steel": ["steel", "beam", "frame", "钢", "架"],
}
for label, kws in KWS.items():
    hits = [o.name for o in bpy.data.objects
            if any(k.lower() in o.name.lower() for k in kws)]
    print(f"  {label}: {len(hits)}")
    for h in hits[:6]:
        print(f"      - {h}")

# 材质列表（找名字带关键词的）
print("\n=== 材质数量 ===")
print(f"  materials: {len(bpy.data.materials)}")
print("\n=== 前 30 个材质名 ===")
for i, m in enumerate(sorted([m.name for m in bpy.data.materials])[:30]):
    print(f"  {m}")

print("\n=== 渲染/世界设置 ===")
print(f"  engine: {scene.render.engine}")
print(f"  frame: {scene.frame_current} / {scene.frame_start}-{scene.frame_end}")
if scene.world:
    print(f"  world: {scene.world.name}")

print("=" * 70)
print("SCENE INSPECT END")
print("=" * 70)
