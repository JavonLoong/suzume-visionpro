# -*- coding: utf-8 -*-
"""从 visionpro 已验证的 USDZ 资产转换出 Unity 使用的 FBX 与贴图。
包含：DreamWorld.fbx, DoorFrame.fbx, DoorLeaf.fbx, Character.fbx 及全部烘焙贴图。
"""
import os
import sys
import json
import zipfile
from pathlib import Path
import bpy
from mathutils import Vector

sys.stdout.reconfigure(encoding="utf-8")

RES_DIR = Path(r"D:\虚拟C盘\JavonLoongSkill\suzume-scene-prep\visionpro\VisionProPortal\VisionProPortal\Resources")
UNITY_MODELS = Path(r"D:\虚拟C盘\JavonLoongSkill\suzume-scene-prep\picounity\Assets\Models")
UNITY_TEXTURES = Path(r"D:\虚拟C盘\JavonLoongSkill\suzume-scene-prep\picounity\Assets\Textures")

UNITY_MODELS.mkdir(parents=True, exist_ok=True)
UNITY_TEXTURES.mkdir(parents=True, exist_ok=True)

# 1. 解压所有 USDZ 内的贴图到 Assets/Textures
extracted_textures = {}
for name in ("DreamWorld", "DoorFrame", "DoorLeaf", "Character"):
    usdz_path = RES_DIR / f"{name}.usdz"
    with zipfile.ZipFile(usdz_path, "r") as z:
        for info in z.infolist():
            if info.filename.lower().endswith(".png"):
                fname = os.path.basename(info.filename)
                out_path = UNITY_TEXTURES / fname
                with z.open(info) as src, open(out_path, "wb") as dst:
                    dst.write(src.read())
                extracted_textures[fname] = str(out_path)
                print(f"[Texture] Extracted {fname} ({info.file_size} bytes)")

# 2. 逐个导入 USDZ 并导出为 FBX
report = {}
for name in ("DreamWorld", "DoorFrame", "DoorLeaf", "Character"):
    usdz_path = RES_DIR / f"{name}.usdz"
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.usd_import(filepath=str(usdz_path))

    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    mesh_info = []
    for o in meshes:
        # 清理父级缩放/旋转，烘焙到网格顶点（Blender Z-up: +X右, +Y朝门内, +Z上）
        bpy.context.view_layer.update()
        world_verts = [o.matrix_world @ v.co for v in o.data.vertices]
        lo = [min(v[i] for v in world_verts) for i in range(3)]
        hi = [max(v[i] for v in world_verts) for i in range(3)]
        mats = [m.name for m in o.data.materials if m]
        texs = []
        for m in o.data.materials:
            if m and m.use_nodes:
                for n in m.node_tree.nodes:
                    if n.type == "TEX_IMAGE" and n.image:
                        texs.append(os.path.basename(n.image.filepath or n.image.name))
        mesh_info.append({
            "name": o.name,
            "parent": o.parent.name if o.parent else None,
            "vertices": len(o.data.vertices),
            "polygons": len(o.data.polygons),
            "bounds_blender_xyz": [lo, hi],
            "materials": mats,
            "textures": texs,
        })
        print(f"[{name}] Mesh {o.name} (parent={o.parent.name if o.parent else None}): "
              f"verts={len(o.data.vertices)} mats={mats} texs={texs} "
              f"bounds=({lo[0]:.2f},{lo[1]:.2f},{lo[2]:.2f})->({hi[0]:.2f},{hi[1]:.2f},{hi[2]:.2f})")

    out_fbx = UNITY_MODELS / f"{name}.fbx"
    bpy.ops.export_scene.fbx(
        filepath=str(out_fbx),
        use_selection=False,
        apply_unit_scale=True,
        global_scale=1.0,
        apply_scale_options="FBX_SCALE_UNITS",
        object_types={"MESH", "EMPTY"},
        use_mesh_modifiers=True,
        mesh_smooth_type="FACE",
        use_tspace=True,
        path_mode="AUTO",
        axis_forward="-Z",
        axis_up="Y",
        bake_space_transform=True,
        add_leaf_bones=False,
    )
    report[name] = {
        "fbx_size": out_fbx.stat().st_size,
        "meshes": mesh_info,
    }
    print(f"[FBX] Wrote {out_fbx.name} ({out_fbx.stat().st_size / 1024 / 1024:.2f} MB)")

report_path = UNITY_MODELS / "visionpro_fbx_report.json"
report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print("ALL_DONE")
