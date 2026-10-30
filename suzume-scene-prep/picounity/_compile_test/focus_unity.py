# -*- coding: utf-8 -*-
"""等 Unity 启动 -> 还原窗口 -> 移到主屏 -> 置前 -> 截图。"""
import sys
import time
import ctypes
from ctypes import wintypes
from PIL import ImageGrab

sys.stdout.reconfigure(encoding="utf-8")
user32 = ctypes.windll.user32
SW_RESTORE = 9
HWND_TOP = 0
SWP_SHOWWINDOW = 0x0040

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

hwnd, title = None, None
for _ in range(120):
    hwnd, title = find()
    if hwnd:
        break
    time.sleep(2)

if not hwnd:
    print("未找到 Unity 窗口")
    sys.exit(1)
print("窗口:", title, "| 最小化:", bool(user32.IsIconic(hwnd)))

# 还原 → 移动到笔记本内屏 CSO161D (X=2650, Y=60) 小窗 (1280x720)，不抢占前台焦点
SWP_NOACTIVATE = 0x0010
for attempt in range(3):
    user32.ShowWindow(hwnd, 4)  # SW_SHOWNOACTIVATE
    time.sleep(1.0)
    user32.SetWindowPos(hwnd, HWND_TOP, 2650, 60, 1280, 720, SWP_SHOWWINDOW | SWP_NOACTIVATE)
    time.sleep(1.0)
    r = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    if r.left >= 2560:
        break

r = wintypes.RECT()
user32.GetWindowRect(hwnd, ctypes.byref(r))
print("最终 rect:", r.left, r.top, r.right, r.bottom)

time.sleep(5)
full = ImageGrab.grab(all_screens=True)
vx = user32.GetSystemMetrics(76); vy = user32.GetSystemMetrics(77)
crop = full.crop((r.left - vx, r.top - vy, r.right - vx, r.bottom - vy))
out = r"D:\虚拟C盘\JavonLoongSkill\suzume-scene-prep\picounity\preview\unity-editor-窗口.png"
crop.save(out)
print("saved:", out, crop.size)
