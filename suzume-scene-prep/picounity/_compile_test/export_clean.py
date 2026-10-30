# -*- coding: utf-8 -*-
"""可靠导出：先把握目标对象链接进活动场景根集合（使其可选中），再精确选中导出。
导出后立即回读校验对象清单。
用法: blender -b <file>.blend -P export_clean.py
"""
import bpy
import sys
import os

sys.stdout.reconfigure(encoding="utf-8")
OUT = r"D:\虚拟C盘\JavonLoongSkill\suzume-scene-prep\picounity\Assets\Models"
os.makedirs(OUT, exist_ok=True)

root_col = bpy.context.scene.collection


def ensure_linked(objs):
    """把对象及其父级链接进活动场景根集合，保证它们位于视图层、可被选中。"""
    added = []
    for o in objs:
        # 先把父级链补上（保持变换层级）
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
    print(f"导出 {label} -> {filename}")
    added = ensure_linked(targets)
    print(f"  链接进根集合: {len(added)} 个")
    hard_deselect()
    ok = 0
    for o in targets:
        try:
            o.select_set(True)
            ok += 1
        except Exception as e:
            print(f"    选中失败 {o.name}: {e}")
    sel = sorted([o.name for o in bpy.context.view_layer.objects if o.select_get()])
    print(f"  选中 {ok}/{len(targets)}；实际选中 {len(sel)} 个:")
    for n in sel[:25]:
        print(f"      - {n}")
    if len(sel) > 25:
        print(f"      ...（共 {len(sel)}）")

    path = os.path.join(OUT, filename)
    bpy.ops.export_scene.gltf(
        filepath=path, export_format="GLB", use_selection=True,
        use_active_scene=True,          # 关键：只导出活动场景，避免混入其他场景的残留选择
        export_apply=True, export_yup=True, export_materials="EXPORT",
        export_cameras=False, export_lights=True,
    )
    print(f"  写出 {filename} {os.path.getsize(path)/1e6:.2f} MB")
    return len(sel)


# 1) 门后梦幻世界
col = bpy.data.collections.get("可编辑夜晚世界")
dream = objects_of_collection(col) if col else []
n1 = do_export(dream, "DreamWorld.glb", "门后梦幻世界") if dream else 0

# 2) 白门与门框
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
n2 = do_export(door, "SuzumeDoor.glb", "白门与门框") if door else 0

# 3) 水面
w = bpy.data.objects.get("浅水与平面反射")
n3 = do_export([w], "Water.glb", "水面") if w else 0

print(f"\n{'='*70}")
print(f"汇总: 梦幻世界={n1} 门={n2} 水面={n3}")
for f in sorted(os.listdir(OUT)):
    print(f"  {f}  {os.path.getsize(os.path.join(OUT, f))/1e6:.2f} MB")
