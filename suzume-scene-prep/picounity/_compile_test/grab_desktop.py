# -*- coding: utf-8 -*-
"""截取当前桌面，用于确认 Unity 编辑器已打开。"""
import sys
from datetime import datetime
from PIL import ImageGrab

sys.stdout.reconfigure(encoding="utf-8")

out = r"D:\虚拟C盘\JavonLoongSkill\suzume-scene-prep\picounity\preview\unity-editor-桌面.png"
img = ImageGrab.grab()
img.save(out)
print("saved:", out, img.size)
