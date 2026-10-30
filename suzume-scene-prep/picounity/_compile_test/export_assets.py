# -*- coding: utf-8 -*-
"""导出铃芽场景的真实资产为 GLB：
1) 门后梦幻世界（可编辑夜晚世界集合）
2) 白门与门框（完整六格白门与门框 + 传送门开口）
3) 水面（浅水与平面反射）
同时输出各部分的包围盒，便于 Unity 里定位。
用法: blender -b <file>.blend -P export_assets.py
"""
import bpy
import sys
import os
import mathutils

sys.stdout.reconfigure(encoding="utf-8")

OUT = r"D:\虚拟C盘\JavonLoongSkill\suzume-scene-prep\picounity\Assets\Models"
os.makedirs(OUT, exist_ok=True)


def deselect_all():
    for o in bpy.context.view_layer.objects:
        try:
            o.select_set(False)
        except Exception:
            pass


def select_safe(o):
    """只有位于当前视图层的对象才能被选中并导出。"""
    try:
        if o.name in bpy.context.view_layer.objects:
            o.select_set(True)
            return True
    except Exception:
        pass
    return False


def objects_of_collection(col):
    """递归取集合内所有对象（含子集合）。"""
    result = list(col.objects)
    for c in col.children:
        result.extend(objects_of_collection(c))
    return result


def select_hierarchy(root):
    """选中 root 及其全部子级。"""
    stack = [root]
    while stack:
        o = stack.pop()
        select_safe(o)
        stack.extend(o.children)


def world_bounds(objs):
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


def export_selection(path, label):
    bpy.ops.export_scene.gltf(
        filepath=path,
        export_format="GLB",
        use_selection=True,
        export_apply=True,             # 应用修改器
        export_yup=True,               # glTF Y-up（Unity 期望）
        export_materials="EXPORT",
        export_image_format="AUTO",
        export_texcoords=True,
        export_normals=True,
    )
    size = os.path.getsize(path) if os.path.exists(path) else 0
    print(f"[EXPORT] {label} -> {os.path.basename(path)}  {size/1e6:.2f} MB")


print("=" * 70)
print("导出真实资产")
print("=" * 70)

# ---------- 1) 门后梦幻世界 ----------
print("\n--- 1) 门后梦幻世界（可编辑夜晚世界）---")
night_col = bpy.data.collections.get("可编辑夜晚世界")
if night_col:
    objs = objects_of_collection(night_col)
    mn, mx, n = world_bounds(objs)
    print(f"  对象数={len(objs)} 网格数={n}")
    print(f"  包围盒 min=({mn.x:.2f},{mn.y:.2f},{mn.z:.2f}) max=({mx.x:.2f},{mx.y:.2f},{mx.z:.2f})")
    # 逐对象尺寸，帮助定位
    print("  各元素世界包围盒:")
    for o in sorted(objs, key=lambda x: x.name):
        if o.type != "MESH":
            continue
        a, b, m = world_bounds([o])
        if m:
            print(f"    {o.name:26s} x[{a.x:8.2f},{b.x:8.2f}] y[{a.y:8.2f},{b.y:8.2f}] z[{a.z:8.2f},{b.z:8.2f}]")
    deselect_all()
    for o in objs:
        select_safe(o)
    export_selection(os.path.join(OUT, "DreamWorld.glb"), "门后梦幻世界")
else:
    print("  !! 找不到 可编辑夜晚世界")

# ---------- 2) 白门与门框 ----------
print("\n--- 2) 白门与门框 ---")
deselect_all()
door_roots = ["完整六格白门与门框"]
for rn in door_roots:
    r = bpy.data.objects.get(rn)
    if r:
        select_hierarchy(r)
        print(f"  选中层级: {rn}")
# 传送门开口
for pn in ["空间门洞传送门开口", "空间门洞传送门开口.001"]:
    o = bpy.data.objects.get(pn)
    if o:
        select_safe(o)
        print(f"  选中: {pn}")

sel = [o for o in bpy.context.view_layer.objects if o.select_get() and o.type == "MESH"]
mn, mx, n = world_bounds(sel)
if n:
    print(f"  门网格数={n} 包围盒 min=({mn.x:.2f},{mn.y:.2f},{mn.z:.2f}) max=({mx.x:.2f},{mx.y:.2f},{mx.z:.2f})")
    print(f"  尺寸=({mx.x-mn.x:.3f},{mx.y-mn.y:.3f},{mx.z-mn.z:.3f})")
export_selection(os.path.join(OUT, "SuzumeDoor.glb"), "白门与门框")

# ---------- 3) 水面 ----------
print("\n--- 3) 水面（浅水与平面反射）---")
deselect_all()
w = bpy.data.objects.get("浅水与平面反射")
if w:
    select_safe(w)
    a, b, m = world_bounds([w])
    print(f"  包围盒 min=({a.x:.2f},{a.y:.2f},{a.z:.2f}) max=({b.x:.2f},{b.y:.2f},{b.z:.2f})")
    export_selection(os.path.join(OUT, "Water.glb"), "水面")
else:
    print("  !! 找不到 浅水与平面反射")

print("\n" + "=" * 70)
print("完成。输出目录:", OUT)
for f in sorted(os.listdir(OUT)):
    print(f"  {f}  {os.path.getsize(os.path.join(OUT, f))/1e6:.2f} MB")
print("=" * 70)
