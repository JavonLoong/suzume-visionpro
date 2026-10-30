# -*- coding: utf-8 -*-
"""导出 FBX 版本（Unity 原生支持），与 GLB 并存。
用法: blender -b <file>.blend -P export_fbx.py
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
    try:
        if o.name in bpy.context.view_layer.objects:
            o.select_set(True)
            return True
    except Exception:
        pass
    return False


def objects_of_collection(col):
    result = list(col.objects)
    for c in col.children:
        result.extend(objects_of_collection(c))
    return result


def select_hierarchy(root):
    stack = [root]
    while stack:
        o = stack.pop()
        select_safe(o)
        stack.extend(o.children)


def export_fbx(path, label):
    bpy.ops.export_scene.fbx(
        filepath=path,
        use_selection=True,
        apply_unit_scale=True,
        global_scale=1.0,
        object_types={"MESH", "EMPTY"},
        use_mesh_modifiers=True,
        mesh_smooth_type="FACE",
        path_mode="COPY",
        embed_textures=True,
        axis_forward="-Z",
        axis_up="Y",
    )
    size = os.path.getsize(path) if os.path.exists(path) else 0
    print(f"[FBX] {label} -> {os.path.basename(path)}  {size/1e6:.2f} MB")


print("=" * 70)
print("导出 FBX")

# 1) 门后梦幻世界
deselect_all()
col = bpy.data.collections.get("可编辑夜晚世界")
if col:
    for o in objects_of_collection(col):
        select_safe(o)
    export_fbx(os.path.join(OUT, "DreamWorld.fbx"), "门后梦幻世界")

# 2) 白门与门框
deselect_all()
r = bpy.data.objects.get("完整六格白门与门框")
if r:
    select_hierarchy(r)
for pn in ["空间门洞传送门开口", "空间门洞传送门开口.001"]:
    o = bpy.data.objects.get(pn)
    if o:
        select_safe(o)
export_fbx(os.path.join(OUT, "SuzumeDoor.fbx"), "白门与门框")

# 3) 水面
deselect_all()
w = bpy.data.objects.get("浅水与平面反射")
if w:
    select_safe(w)
export_fbx(os.path.join(OUT, "Water.fbx"), "水面")

print("\n输出目录:", OUT)
for f in sorted(os.listdir(OUT)):
    print(f"  {f}  {os.path.getsize(os.path.join(OUT, f))/1e6:.2f} MB")
