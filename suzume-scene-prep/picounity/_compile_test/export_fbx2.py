# -*- coding: utf-8 -*-
"""导出 FBX（Unity 原生支持，无需联网装包）。
关键：先把目标对象链接进活动场景根集合，使其位于视图层、可被选中。
用法: blender -b <file>.blend -P export_fbx2.py
"""
import bpy
import sys
import os

sys.stdout.reconfigure(encoding="utf-8")
OUT = r"D:\虚拟C盘\JavonLoongSkill\suzume-scene-prep\picounity\Assets\Models"
os.makedirs(OUT, exist_ok=True)
root_col = bpy.context.scene.collection


def ensure_linked(objs):
    added = []
    for o in objs:
        chain = []
        p = o.parent
        while p is not None:
            chain.append(p)
            p = p.parent
        for node in list(reversed(chain)) + [o]:
            try:
                if node.name not in root_col.objects:
                    root_col.objects.link(node)
                    added.append(node.name)
            except Exception as e:
                print(f"    链接失败 {node.name}: {e}")
    return added


def hard_deselect():
    try:
        bpy.ops.object.select_all(action="DESELECT")
    except Exception:
        pass
    for o in bpy.data.objects:
        try:
            o.select_set(False)
        except Exception:
            pass


def objects_of_collection(col, seen=None):
    if seen is None:
        seen = set()
    res = []
    for o in col.objects:
        if o.name not in seen:
            seen.add(o.name)
            res.append(o)
    for c in col.children:
        res.extend(objects_of_collection(c, seen))
    return res


def hierarchy(root):
    out = []
    stack = [root]
    while stack:
        o = stack.pop()
        out.append(o)
        stack.extend(o.children)
    return out


def do_export(targets, filename, label):
    print(f"\n{'='*70}")
    print(f"FBX 导出 {label} -> {filename}")
    added = ensure_linked(targets)
    print(f"  链接进根集合: {len(added)}")
    hard_deselect()
    ok = 0
    for o in targets:
        try:
            o.select_set(True)
            ok += 1
        except Exception as e:
            print(f"    失败 {o.name}: {e}")
    sel = [o.name for o in bpy.context.view_layer.objects if o.select_get()]
    print(f"  选中 {ok}/{len(targets)}；实际 {len(sel)}")

    path = os.path.join(OUT, filename)
    bpy.ops.export_scene.fbx(
        filepath=path,
        use_selection=True,
        use_active_collection=False,
        apply_unit_scale=True,
        global_scale=1.0,
        object_types={"MESH", "EMPTY"},
        use_mesh_modifiers=True,
        mesh_smooth_type="FACE",
        use_tspace=True,
        path_mode="COPY",
        embed_textures=True,
        axis_forward="-Z",
        axis_up="Y",
        bake_space_transform=False,
        add_leaf_bones=False,
    )
    size = os.path.getsize(path) if os.path.exists(path) else 0
    print(f"  写出 {filename} {size/1e6:.2f} MB")
    return len(sel)


# 1) 梦幻世界
col = bpy.data.collections.get("可编辑夜晚世界")
dream = objects_of_collection(col) if col else []
n1 = do_export(dream, "DreamWorld.fbx", "门后梦幻世界") if dream else 0

# 2) 门
door = []
r = bpy.data.objects.get("完整六格白门与门框")
if r:
    door.extend(hierarchy(r))
for pn in ["空间门洞传送门开口", "空间门洞传送门开口.001"]:
    o = bpy.data.objects.get(pn)
    if o and o not in door:
        door.append(o)
door = [o for o in door if not any(k in o.name for k in
        ["环绕夜空", "发光星辰", "起伏草原", "远景草原", "薄雾", "暮光云", "三维草叶", "花茎"])]
n2 = do_export(door, "SuzumeDoor.fbx", "白门与门框") if door else 0

# 3) 水面
w = bpy.data.objects.get("浅水与平面反射")
n3 = do_export([w], "Water.fbx", "水面") if w else 0

print(f"\n{'='*70}")
print(f"汇总: 梦幻世界={n1} 门={n2} 水面={n3}")
for f in sorted(os.listdir(OUT)):
    print(f"  {f}  {os.path.getsize(os.path.join(OUT, f))/1e6:.2f} MB")
