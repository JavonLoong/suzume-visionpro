# -*- coding: utf-8 -*-
"""列出门的层级结构与门洞尺寸。"""
import bpy
import sys
import mathutils

sys.stdout.reconfigure(encoding="utf-8")


def obj_bounds(o):
    bpy.context.view_layer.update()
    cos = [o.matrix_world @ mathutils.Vector(c) for c in o.bound_box]
    xs = [c.x for c in cos]; ys = [c.y for c in cos]; zs = [c.z for c in cos]
    return (min(xs), max(xs)), (min(ys), max(ys)), (min(zs), max(zs))


def dump(o, depth=0):
    if depth > 3:
        return
    marker = ""
    if o.type == "MESH":
        (x0, x1), (y0, y1), (z0, z1) = obj_bounds(o)
        marker = (f" 尺寸=({x1-x0:.3f},{y1-y0:.3f},{z1-z0:.3f})"
                  f" z[{z0:.2f},{z1:.2f}]")
    print("  " * depth + f"- {o.name} [{o.type}]{marker}")
    for c in o.children:
        dump(c, depth + 1)


print("=" * 70)
print("门层级结构:")
for name in ["可开合门扇与铰链", "门扇框架内夜晚世界", "夜晚世界通向穿过门", "空间门延伸位于夜晚偏移"]:
    o = bpy.data.objects.get(name)
    print(f"\n### {name}")
    if o is None:
        print("   不存在")
        continue
    dump(o, 1)

# 白门/门框查找
print("\n" + "=" * 70)
print("白门 / 门框相关:")
for o in bpy.data.objects:
    n = o.name
    if any(k in n for k in ["白门", "门框", "门洞", "门槛", "门板", "门柱"]):
        loc = o.matrix_world.translation
        extra = ""
        if o.type == "MESH":
            (x0, x1), (y0, y1), (z0, z1) = obj_bounds(o)
            extra = f" 尺寸=({x1-x0:.3f},{y1-y0:.3f},{z1-z0:.3f})"
        print(f"   {n:42s} [{o.type:8s}] 位置=({loc.x:.3f},{loc.y:.3f},{loc.z:.3f}){extra}")

# 浅水
print("\n" + "=" * 70)
print("水面:")
o = bpy.data.objects.get("浅水与平面反射")
if o:
    (x0, x1), (y0, y1), (z0, z1) = obj_bounds(o)
    print(f"   浅水与平面反射 包围盒 x[{x0:.2f},{x1:.2f}] y[{y0:.2f},{y1:.2f}] z[{z0:.2f},{z1:.2f}]")
    print(f"   尺寸=({x1-x0:.2f},{y1-y0:.2f},{z1-z0:.2f})")

# 单位/朝向
print("\n" + "=" * 70)
print("单位设置:")
print(f"   scene.unit_settings.system = {bpy.context.scene.unit_settings.system}")
print(f"   scale_length = {bpy.context.scene.unit_settings.scale_length}")
