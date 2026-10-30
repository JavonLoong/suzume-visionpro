# -*- coding: utf-8 -*-
"""导出「对象名 -> 材质基色/自发光」映射为 JSON，供 Unity 侧还原颜色。
同时给出材质的节点构成摘要，判断是否程序化（需要烘焙）。
用法: blender -b <file>.blend -P dump_colors.py
"""
import bpy
import sys
import json
import os

sys.stdout.reconfigure(encoding="utf-8")
OUT = r"D:\虚拟C盘\JavonLoongSkill\suzume-scene-prep\picounity\Assets\Models\material_colors.json"


def base_color_of(mat):
    """从 Principled BSDF 或 Emission 取基色 / 自发光。"""
    color = [1.0, 1.0, 1.0, 1.0]
    emission = [0.0, 0.0, 0.0]
    emission_strength = 0.0
    node_kinds = []
    if not mat or not mat.use_nodes:
        return color, emission, emission_strength, ["(no nodes)"]
    for n in mat.node_tree.nodes:
        node_kinds.append(n.type)
        if n.type == "BSDF_PRINCIPLED":
            if "Base Color" in n.inputs:
                v = n.inputs["Base Color"].default_value
                color = [round(v[0], 4), round(v[1], 4), round(v[2], 4), round(v[3], 4)]
            if "Emission Color" in n.inputs:
                e = n.inputs["Emission Color"].default_value
                emission = [round(e[0], 4), round(e[1], 4), round(e[2], 4)]
            if "Emission Strength" in n.inputs:
                emission_strength = round(n.inputs["Emission Strength"].default_value, 3)
        elif n.type == "EMISSION":
            if "Color" in n.inputs:
                e = n.inputs["Color"].default_value
                emission = [round(e[0], 4), round(e[1], 4), round(e[2], 4)]
            if "Strength" in n.inputs:
                emission_strength = round(n.inputs["Strength"].default_value, 3)
    return color, emission, emission_strength, sorted(set(node_kinds))


# 目标对象
TARGET_COLLECTIONS = ["可编辑夜晚世界"]
TARGET_ROOTS = ["完整六格白门与门框"]

targets = set()
for cn in TARGET_COLLECTIONS:
    col = bpy.data.collections.get(cn)
    if col:
        def walk(c):
            for o in c.objects:
                targets.add(o.name)
            for ch in c.children:
                walk(ch)
        walk(col)
for rn in TARGET_ROOTS:
    r = bpy.data.objects.get(rn)
    if r:
        stack = [r]
        while stack:
            o = stack.pop()
            targets.add(o.name)
            stack.extend(o.children)
targets.add("浅水与平面反射")

result = {}
complex_mats = []
for name in sorted(targets):
    o = bpy.data.objects.get(name)
    if o is None or o.type != "MESH":
        continue
    mats = [m for m in o.data.materials if m]
    if not mats:
        continue
    m = mats[0]
    c, e, es, kinds = base_color_of(m)
    result[name] = {
        "material": m.name,
        "color": c,
        "emission": e,
        "emission_strength": es,
        "node_kinds": kinds,
    }
    # 判断是否程序化：含除 Principled/Output 之外的节点（如渐变、噪波、贴图）
    procedural = any(k not in ("BSDF_PRINCIPLED", "OUTPUT_MATERIAL", "MATERIAL_OUTPUT")
                     for k in kinds)
    if procedural:
        complex_mats.append(name)

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=1)

print(f"导出 {len(result)} 个对象的材质色 -> {OUT}")
print(f"\n含程序化节点的材质对象（需烘焙才准）: {len(complex_mats)}")
for n in complex_mats:
    info = result[n]
    print(f"  {n}: 节点={info['node_kinds']} 基色={info['color']}")

print("\n=== 全部对象颜色 ===")
for n in sorted(result):
    i = result[n]
    print(f"  {n:34s} 基色={i['color'][:3]} 自发光={i['emission']} x{i['emission_strength']} 节点={i['node_kinds']}")
