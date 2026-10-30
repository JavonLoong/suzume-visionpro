# -*- coding: utf-8 -*-
"""查看 glTF 导出器的可用参数。"""
import bpy
import sys

sys.stdout.reconfigure(encoding="utf-8")
props = bpy.ops.export_scene.gltf.get_rna_type().properties
names = [p.identifier for p in props]
print("共", len(names), "个参数")
print("\n与场景/选择相关的参数:")
for n in sorted(names):
    if any(k in n.lower() for k in ["scene", "collection", "select", "active", "filter"]):
        p = props[n]
        default = getattr(p, "default", None)
        print(f"  {n:38s} default={default}")
print("\n全部参数:")
for n in sorted(names):
    print("  ", n)
