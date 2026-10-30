# -*- coding: utf-8 -*-
"""为 Unity 的 Character.fbx 绑定完整的 20 骨骼系统 (SuzumeHunyuanRig) 与平滑解析权重。
直接复用 rig_character.py 的 20 根骨骼拓扑与三次 Hermite (ramp) 权重划分，按 1.62m 身高同比例缩放。
"""
import json
from pathlib import Path
import numpy as np
import bpy
from mathutils import Matrix, Vector

RES_DIR = Path(r"D:\虚拟C盘\JavonLoongSkill\suzume-scene-prep\visionpro\VisionProPortal\VisionProPortal\Resources")
UNITY_MODELS = Path(r"D:\虚拟C盘\JavonLoongSkill\suzume-scene-prep\picounity\Assets\Models")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.usd_import(filepath=str(RES_DIR / "Character.usdz"))

meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
for o in meshes:
    bpy.context.view_layer.update()
    o.data.transform(o.matrix_world)
    o.matrix_world = Matrix.Identity(4)
    if o.parent:
        o.parent = None

# 删除可能残余的空节点
for o in list(bpy.context.scene.objects):
    if o.type != "MESH":
        bpy.data.objects.remove(o, do_unlink=True)

# 原始 rig_character.py 基于 1.135m 高度测量，当前网格已归一化为 1.62m 高度
SCALE = 1.62 / 1.135

spec_unscaled = {
    "root": ((0, 0, 0), (0, 0, 0.12), None),
    "pelvis": ((0, 0, 0.69), (0, 0, 0.766), "root"),
    "spine": ((0, 0, 0.766), (0, 0, 0.847), "pelvis"),
    "chest": ((0, 0, 0.847), (0, 0, 0.938), "spine"),
    "neck": ((0, 0, 0.938), (0, 0, 0.985), "chest"),
    "head": ((0, 0, 0.985), (0, 0, 1.135), "neck"),
}
for side, sign in [("R", -1), ("L", 1)]:
    spec_unscaled.update({
        "upper_arm." + side: ((sign * 0.086, 0, 0.918), (sign * 0.133, -0.002, 0.760), "chest"),
        "forearm." + side: ((sign * 0.133, -0.002, 0.760), (sign * 0.173, -0.010, 0.620), "upper_arm." + side),
        "hand." + side: ((sign * 0.173, -0.010, 0.620), (sign * 0.180, -0.014, 0.564), "forearm." + side),
        "fingers." + side: ((sign * 0.180, -0.014, 0.564), (sign * 0.181, -0.012, 0.519), "hand." + side),
        "thigh." + side: ((sign * 0.051, 0, 0.690), (sign * 0.057, -0.006, 0.350), "pelvis"),
        "shin." + side: ((sign * 0.057, -0.006, 0.350), (sign * 0.061, 0.007, 0.069), "thigh." + side),
        "foot." + side: ((sign * 0.061, 0.007, 0.069), (sign * 0.061, -0.073, 0.026), "shin." + side),
    })

spec = {
    name: (
        tuple(c * SCALE for c in head),
        tuple(c * SCALE for c in tail),
        parent,
    )
    for name, (head, tail, parent) in spec_unscaled.items()
}

ad = bpy.data.armatures.new("SuzumeEditableSkeleton")
rig = bpy.data.objects.new("SuzumeHunyuanRig", ad)
bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
rig.select_set(True)

bpy.ops.object.mode_set(mode="EDIT")
for name, (a, b, parent) in spec.items():
    bone = ad.edit_bones.new(name)
    bone.head = a
    bone.tail = b
    if parent:
        bone.parent = ad.edit_bones[parent]
bpy.ops.object.mode_set(mode="OBJECT")

for b in rig.data.bones:
    b.inherit_scale = "NONE"


def ramp(a, b, v):
    t = np.clip((v - a) / (b - a), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def assign_weights(mesh_obj, is_head_mesh=False):
    P = np.empty((len(mesh_obj.data.vertices), 3), np.float32)
    mesh_obj.data.vertices.foreach_get("co", P.ravel())
    # 还原到 rig_character.py 的 1.135m 测量尺度计算解剖权重
    Pn = P / SCALE
    x, y, z = Pn.T
    ax = np.abs(x)
    N = len(Pn)
    W = {name: np.zeros(N, np.float32) for name in spec}

    if is_head_mesh:
        # 独立重建的头模（含发簪、马尾与颈部上段）：平滑过渡 neck 与 head
        head_w = ramp(0.915, 0.965, z)
        # 马尾后侧发束归属 head
        ponytail = ((y > 0.035) & (z > 0.850)).astype(np.float32)
        head_w = np.maximum(head_w, ponytail)
        W["head"] = head_w
        W["neck"] = 1.0 - head_w
    else:
        head = ramp(0.959, 0.985, z)
        # 修复后背白衣误入马尾区域（fit_pose_v16.py 同款几何边界）
        ponytail_mask = ((y > 0.045) & (z > 0.960) & (ax < 0.075)).astype(np.float32)
        head = np.maximum(head, ponytail_mask)
        arm_boundary = np.interp(
            z,
            [0.49, 0.52, 0.56, 0.60, 0.64, 0.68, 0.72, 0.75, 0.78, 0.81, 0.84, 0.87, 0.90, 0.94],
            [0.145, 0.143, 0.132, 0.128, 0.123, 0.110, 0.092, 0.080, 0.081, 0.074, 0.068, 0.063, 0.056, 0.044],
        )
        blend_width = 0.003 + ramp(0.79, 0.90, z) * 0.016
        arm = (
            ramp(arm_boundary - blend_width, arm_boundary + blend_width, ax)
            * (1.0 - ramp(0.909, 0.938, z))
            * ramp(0.475, 0.500, z)
        )
        arm *= 1.0 - head
        leg = (1.0 - ramp(0.425, 0.742, z)) * (1.0 - arm) * (1.0 - head)
        torso = np.clip(1.0 - head - arm - leg, 0.0, 1.0)
        W["head"] = head
        chest = ramp(0.783, 0.887, z)
        neck = ramp(0.925, 0.965, z)
        W["pelvis"] = torso * (1.0 - ramp(0.751, 0.807, z))
        W["spine"] = torso * ramp(0.751, 0.807, z) * (1.0 - chest)
        W["chest"] = torso * ramp(0.751, 0.807, z) * chest * (1.0 - neck)
        W["neck"] = torso * ramp(0.751, 0.807, z) * chest * neck
        for side, sign in [("R", -1), ("L", 1)]:
            mask = (x * sign >= 0).astype(np.float32)
            upper = ramp(0.738, 0.780, z)
            hand = 1.0 - ramp(0.603, 0.635, z)
            finger = 1.0 - ramp(0.551, 0.579, z)
            W["upper_arm." + side] = arm * mask * upper
            W["forearm." + side] = arm * mask * (1.0 - upper) * (1.0 - hand)
            W["hand." + side] = arm * mask * (1.0 - upper) * hand * (1.0 - finger)
            W["fingers." + side] = arm * mask * (1.0 - upper) * hand * finger
            thigh = ramp(0.315, 0.385, z)
            foot = 1.0 - ramp(0.055, 0.110, z)
            cloth_blend = ramp(0.420, 0.450, z)
            leg_mask = mask * (1.0 - cloth_blend) + ramp(-0.030, 0.030, x * sign) * cloth_blend
            W["thigh." + side] = leg * leg_mask * thigh
            W["shin." + side] = leg * leg_mask * (1.0 - thigh) * (1.0 - foot)
            W["foot." + side] = leg * leg_mask * (1.0 - thigh) * foot

    total = sum(W.values())
    assert np.min(total) > 0.98, f"Weight total min too low: {np.min(total)}"
    mesh_obj.vertex_groups.clear()
    for name, weights in W.items():
        weights = weights / total
        group = mesh_obj.vertex_groups.new(name=name)
        quant = np.rint(weights * 128).astype(np.int16)
        for q in np.unique(quant):
            if q > 0:
                group.add(np.flatnonzero(quant == q).tolist(), int(q) / 128.0, "REPLACE")

    mod = mesh_obj.modifiers.new("AnatomicalCharacterDeformation", "ARMATURE")
    mod.object = rig
    mod.use_deform_preserve_volume = True
    mesh_obj.parent = rig


for m in meshes:
    is_head = "001" in m.name or (max(v.co.z for v in m.data.vertices) > 1.50)
    assign_weights(m, is_head_mesh=is_head)
    print(f"[Rigged] {m.name} (is_head={is_head}, verts={len(m.data.vertices)}, groups={len(m.vertex_groups)})")

# 添加一个顶层基准空节点，确保 Unity 导入 FBX 时生成顶层容器，不覆盖 SuzumeHunyuanRig 自身的轴向变换
origin_empty = bpy.data.objects.new("CharacterOrigin", None)
bpy.context.scene.collection.objects.link(origin_empty)

out_fbx = UNITY_MODELS / "Character.fbx"
bpy.ops.export_scene.fbx(
    filepath=str(out_fbx),
    use_selection=False,
    apply_unit_scale=True,
    global_scale=1.0,
    apply_scale_options="FBX_SCALE_UNITS",
    object_types={"EMPTY", "ARMATURE", "MESH"},
    use_mesh_modifiers=False,
    mesh_smooth_type="FACE",
    use_tspace=True,
    path_mode="AUTO",
    axis_forward="-Z",
    axis_up="Y",
    bake_space_transform=False,
    add_leaf_bones=False,
    armature_nodetype="NULL",
)

audit = {
    "bones": len(spec),
    "boneNames": list(spec.keys()),
    "scaleFromRawHunyuan": SCALE,
    "heightMetres": 1.62,
    "fbxBytes": out_fbx.stat().st_size,
    "meshes": [m.name for m in meshes],
    "rigSpecMetres": {k: {"head": list(v[0]), "tail": list(v[1]), "parent": v[2]} for k, v in spec.items()},
}
(UNITY_MODELS / "character_rig_report.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
print("RIGGED_CHARACTER_FBX_OK", json.dumps({"bones": len(spec), "bytes": out_fbx.stat().st_size}))
