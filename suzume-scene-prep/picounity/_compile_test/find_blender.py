# -*- coding: utf-8 -*-
"""定位 Blender，并列出铃芽场景候选文件。"""
import os
import sys
import glob

sys.stdout.reconfigure(encoding="utf-8")

print("=== 找 Blender ===")
cands = []
roots = [
    r"C:\Program Files\Blender Foundation",
    r"D:\Program Files\Blender Foundation",
    r"D:\Blender",
    os.path.expandvars(r"%LOCALAPPDATA%\Programs"),
    r"C:\Program Files",
]
for root in roots:
    if not os.path.isdir(root):
        continue
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d.lower() not in
                 ("node_modules", ".git", "__pycache__", "windows", "system32", "driverstore", "winsxs")]
        for f in fn:
            if f.lower() == "blender.exe":
                cands.append(os.path.join(dp, f))
        # 控制深度
        if dp.count(os.sep) - root.count(os.sep) > 3:
            dn[:] = []
for c in cands:
    print("  BLENDER:", c)
print("  共找到:", len(cands))

# 也查 winget / 注册表常见位置
for p in glob.glob(r"C:\Program Files\Blender*") + glob.glob(r"D:\Blender*"):
    print("  目录:", p)

print()
print("=== 铃芽场景候选（最新 5 个 .blend）===")
base = r"D:\虚拟C盘\JavonLoongSkill\suzume-scene-prep"
blends = []
for dp, dn, fn in os.walk(base):
    dn[:] = [d for d in dn if d not in ("node_modules", ".git", "python-deps", "color-pipeline-deps")]
    for f in fn:
        if f.lower().endswith(".blend"):
            fp = os.path.join(dp, f)
            try:
                blends.append((os.path.getmtime(fp), os.path.getsize(fp), fp))
            except OSError:
                pass
blends.sort(reverse=True)
for mt, sz, fp in blends[:8]:
    import time
    print(f"  {time.strftime('%m-%d %H:%M', time.localtime(mt))}  {sz/1e6:7.1f}MB  {os.path.relpath(fp, base)}")
print("  共", len(blends), "个 .blend")
