# -*- coding: utf-8 -*-
"""抓整个虚拟桌面（支持多显示器），裁剪出 Unity 窗口。"""
import sys
import time
import ctypes
from ctypes import wintypes
from PIL import ImageGrab

sys.stdout.reconfigure(encoding="utf-8")

user32 = ctypes.windll.user32

# 虚拟桌面范围
vx = user32.GetSystemMetrics(76)   # SM_XVIRTUALSCREEN
vy = user32.GetSystemMetrics(77)
vw = user32.GetSystemMetrics(78)
vh = user32.GetSystemMetrics(79)
print(f"虚拟桌面: 原点({vx},{vy}) 尺寸 {vw}x{vh}")

def find():
    hwnd = None
    while True:
        hwnd = user32.FindWindowExW(None, hwnd, None, None)
        if not hwnd:
            break
        n = user32.GetWindowTextLengthW(hwnd)
        if not n:
            continue
        buf = ctypes.create_unicode_buffer(n + 1)
        user32.GetWindowTextW(hwnd, buf, n + 1)
        if "Unity" in buf.value and "picounity" in buf.value:
            return hwnd, buf.value
    return None, None

hwnd, title = find()
if not hwnd:
    print("未找到 Unity 窗口")
    sys.exit(1)

user32.ShowWindow(hwnd, 4)  # SW_SHOWNOACTIVATE，不抢前台焦点
time.sleep(1)

rect = wintypes.RECT()
user32.GetWindowRect(hwnd, ctypes.byref(rect))
print("窗口 rect:", rect.left, rect.top, rect.right, rect.bottom)

# 抓整个虚拟桌面
full = ImageGrab.grab(all_screens=True)
print("虚拟桌面截图:", full.size)
# all_screens 图的 (0,0) 对应虚拟桌面原点 (vx,vy)
left = rect.left - vx
top = rect.top - vy
right = rect.right - vx
bottom = rect.bottom - vy
crop = full.crop((left, top, right, bottom))
out = r"D:\虚拟C盘\JavonLoongSkill\suzume-scene-prep\picounity\preview\unity-editor-窗口.png"
crop.save(out)
print("saved:", out, crop.size)
