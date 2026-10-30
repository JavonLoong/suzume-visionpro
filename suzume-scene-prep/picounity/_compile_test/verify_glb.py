# -*- coding: utf-8 -*-
"""回读 GLB，验证内容有效（对象数、网格数、材质数、包围盒）。"""
import bpy
import sys
import mathutils
import os

sys.stdout.reconfigure(encoding="utf-8")

FILES = [
    r"D:\虚拟C盘\JavonLoongSkill\suzume-scene-prep\picounity\Assets\Models\DreamWorld.glb",
    r"D:\虚拟C盘\JavonLoongSkill\suzume-scene-prep\picounity\Assets\Models\SuzumeDoor.glb",
    r"D:\虚拟C盘\JavonLoongSkill\suzume-scene-prep\picounity\Assets\Models\Water.glb",
]

for f in FILES:
    # 清空场景
    bpy.ops.wm.read_factory_settings(use_empty=True)
    print("\n" + "=" * 66)
    print("GLB:", os.path.basename(f), f"{os.path.getsize(f)/1e6:.2f} MB")
    try:
        bpy.ops.import_scene.gltf(filepath=f)
    except Exception as e:
        print("  导入失败:", e)
        continue
    objs = list(bpy.context.scene.objects)
    meshes = [o for o in objs if o.type == "MESH"]
    verts = sum(len(o.data.vertices) for o in meshes)
    tris = sum(len(o.data.loop_triangles) for o in meshes
               if (o.data.calc_loop_triangles() or True))
    mats = set()
    for o in meshes:
        for m in o.data.materials:
            if m:
                mats.add(m.name)
    print(f"  对象={len(objs)} 网格={len(meshes)} 顶点={verts} 三角面={tris} 材质={len(mats)}")
    print("  材质:", sorted(mats)[:10])

    mn = mathutils.Vector((1e9, 1e9, 1e9))
    mx = mathutils.Vector((-1e9, -1e9, -1e9))
    for o in meshes:
        try:
            for c in o.bound_box:
                w = o.matrix_world @ mathutils.Vector(c)
                mn.x = min(mn.x, w.x); mn.y = min(mn.y, w.y); mn.z = min(mn.z, w.z)
                mx.x = max(mx.x, w.x); mx.y = max(mx.y, w.y); mx.z = max(mx.z, w.z)
        except Exception:
            pass
    print(f"  包围盒 min=({mn.x:.2f},{mn.y:.2f},{mn.z:.2f}) max=({mx.x:.2f},{mx.y:.2f},{mx.z:.2f})")
    # 顶层对象
    tops = [o for o in objs if o.parent is None]
    print(f"  顶层({len(tops)}):", [o.name for o in tops[:8]])
