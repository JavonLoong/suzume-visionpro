# -*- coding: utf-8 -*-
"""详细列出「可编辑夜晚世界」集合内容 + 门的坐标，用于导出对齐。"""
import bpy
import sys
import mathutils

sys.stdout.reconfigure(encoding="utf-8")


def bounds(objs):
    mn = mathutils.Vector((1e9, 1e9, 1e9))
    mx = mathutils.Vector((-1e9, -1e9, -1e9))
    n = 0
    for o in objs:
        if o.type != "MESH":
            continue
        try:
            for c in o.bound_box:
                w = o.matrix_world @ mathutils.Vector(c)
                mn.x = min(mn.x, w.x); mn.y = min(mn.y, w.y); mn.z = min(mn.z, w.z)
                mx.x = max(mx.x, w.x); mx.y = max(mx.y, w.y); mx.z = max(mx.z, w.z)
            n += 1
        except Exception:
            pass
    return mn, mx, n


for colname in ["可编辑夜晚世界", "可编辑夜晚世界.001"]:
    col = bpy.data.collections.get(colname)
    print(f"\n{'='*70}")
    print(f"集合: {colname}  存在={col is not None}")
    if col is None:
        continue
    print(f"对象数: {len(col.objects)}")
    for o in sorted(col.objects, key=lambda x: x.name):
        loc = o.matrix_world.translation
        print(f"    {o.name:40s} type={o.type:9s} 世界位置=({loc.x:8.3f},{loc.y:8.3f},{loc.z:8.3f})")
    mn, mx, n = bounds(col.objects)
    if n:
        print(f"  包围盒: min=({mn.x:.2f},{mn.y:.2f},{mn.z:.2f}) max=({mx.x:.2f},{mx.y:.2f},{mx.z:.2f})")
        print(f"  尺寸: ({mx.x-mn.x:.2f}, {mx.y-mn.y:.2f}, {mx.z-mn.z:.2f})  网格数={n}")

# 门
print(f"\n{'='*70}")
print("门相关对象:")
for name in ["可开合门扇与铰链", "可开合门扇与铰链.001", "门扇框架内夜晚世界", "门扇框架内夜晚世界.001",
             "夜晚世界通向穿过门", "夜晚世界通向穿过门.001",
             "空间门延伸位于夜晚偏移", "空间门延伸位于夜晚偏移.001"]:
    o = bpy.data.objects.get(name)
    if o is None:
        print(f"    {name}: 不存在")
        continue
    loc = o.matrix_world.translation
    print(f"    {name}: type={o.type} 位置=({loc.x:.3f},{loc.y:.3f},{loc.z:.3f})")
    if o.type == "MESH":
        try:
            bpy.context.view_layer.update()
            coords = [o.matrix_world @ mathutils.Vector(c) for c in o.bound_box]
            xs = [c.x for c in coords]; ys = [c.y for c in coords]; zs = [c.z for c in coords]
            print(f"        包围盒 x[{min(xs):.2f},{max(xs):.2f}] "
                  f"y[{min(ys):.2f},{max(ys):.2f}] z[{min(zs):.2f},{max(zs):.2f}]")
            print(f"        尺寸 ({max(xs)-min(xs):.3f}, {max(ys)-min(ys):.3f}, {max(zs)-min(zs):.3f})")
        except Exception as e:
            print("        包围盒失败:", e)

# 关键标记对象（星空/草原）
print(f"\n{'='*70}")
print("梦幻世界元素的位置:")
for name in ["起伏草原地面", "连续远景草原第31版", "环绕夜空", "立体发光星辰",
             "浅水与平面反射", "草原独立花朵", "低矮草原薄雾第31版0"]:
    o = bpy.data.objects.get(name)
    if o is None:
        print(f"    {name}: 不存在")
        continue
    loc = o.matrix_world.translation
    print(f"    {name:28s} 位置=({loc.x:8.3f},{loc.y:8.3f},{loc.z:8.3f}) scale={tuple(round(s,3) for s in o.scale)}")
