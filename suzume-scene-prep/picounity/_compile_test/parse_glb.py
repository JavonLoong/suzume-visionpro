# -*- coding: utf-8 -*-
"""直接解析 GLB 二进制里的 JSON chunk，列出节点/网格/材质名。"""
import json
import struct
import sys
import os

sys.stdout.reconfigure(encoding="utf-8")

FILES = [
    r"D:\虚拟C盘\JavonLoongSkill\suzume-scene-prep\picounity\Assets\Models\DreamWorld.glb",
    r"D:\虚拟C盘\JavonLoongSkill\suzume-scene-prep\picounity\Assets\Models\SuzumeDoor.glb",
    r"D:\虚拟C盘\JavonLoongSkill\suzume-scene-prep\picounity\Assets\Models\Water.glb",
]


def read_glb_json(path):
    with open(path, "rb") as f:
        magic, version, length = struct.unpack("<4sII", f.read(12))
        assert magic == b"glTF", magic
        chunk_len, chunk_type = struct.unpack("<II", f.read(8))
        data = f.read(chunk_len)
        return json.loads(data.decode("utf-8"))


for p in FILES:
    print("\n" + "=" * 72)
    print(os.path.basename(p), f"{os.path.getsize(p)/1e6:.2f} MB")
    g = read_glb_json(p)
    nodes = g.get("nodes", [])
    meshes = g.get("meshes", [])
    mats = g.get("materials", [])
    scenes = g.get("scenes", [])
    print(f"  nodes={len(nodes)} meshes={len(meshes)} materials={len(mats)} scenes={len(scenes)}")
    print(f"  场景根节点: {scenes[0].get('nodes') if scenes else None}")
    print("  --- 节点名 ---")
    for i, n in enumerate(nodes):
        nm = n.get("name", f"node{i}")
        has_mesh = "mesh" in n
        kids = len(n.get("children", []))
        print(f"    [{i:3d}] {nm:44s} mesh={has_mesh} children={kids}")
    print("  --- 材质名 ---")
    for i, m in enumerate(mats):
        print(f"    [{i:3d}] {m.get('name', '?')}")
