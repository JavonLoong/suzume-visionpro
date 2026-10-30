# -*- coding: utf-8 -*-
"""补齐 Unity Android SDK 被暂停的 6 个组件：下载 zip -> 解压 -> 按 Unity 期望的目录名落位。"""
import os
import sys
import shutil
import tempfile
import urllib.request
import zipfile

sys.stdout.reconfigure(encoding="utf-8")

SDK = r"D:\Unity\Editors\2022.3.62f3\Editor\Data\PlaybackEngines\AndroidPlayer\SDK"

# (下载URL, 目标父目录, 期望的最终文件夹名 or None=保持zip内的顶层名)
JOBS = [
    ("https://dl.google.com/android/repository/build-tools_r34-windows.zip",
     os.path.join(SDK, "build-tools"), "34.0.0"),
    ("https://dl.google.com/android/repository/platform-tools_r32.0.0-windows.zip",
     SDK, "platform-tools"),
    ("https://dl.google.com/android/repository/platform-34-ext7_r02.zip",
     os.path.join(SDK, "platforms"), "android-34"),
    ("https://dl.google.com/android/repository/platform-35_r01.zip",
     os.path.join(SDK, "platforms"), "android-35"),
    ("https://dl.google.com/android/repository/platform-36_r02.zip",
     os.path.join(SDK, "platforms"), "android-36"),
    ("https://dl.google.com/android/repository/commandlinetools-win-8092744_latest.zip",
     os.path.join(SDK, "cmdline-tools"), "6.0"),
]


def download(url, dest):
    print(f"下载 {os.path.basename(url)} ...", flush=True)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=120) as r, open(dest, "wb") as f:
        total = int(r.headers.get("Content-Length") or 0)
        done = 0
        while True:
            chunk = r.read(1024 * 256)
            if not chunk:
                break
            f.write(chunk)
            done += len(chunk)
            if total:
                pct = done * 100 / total
                if int(pct) % 20 == 0:
                    print(f"   {pct:.0f}%", flush=True)
    print(f"  完成 {os.path.getsize(dest)/1e6:.1f} MB", flush=True)


def top_level_names(zip_path):
    with zipfile.ZipFile(zip_path) as z:
        tops = set()
        for n in z.namelist():
            parts = n.split("/")
            if parts and parts[0]:
                tops.add(parts[0])
        return tops


def extract_and_place(zip_path, parent, final_name):
    os.makedirs(parent, exist_ok=True)
    tops = top_level_names(zip_path)
    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(zip_path) as z:
            z.extractall(tmp)
        # 找出真正的顶层目录（可能被包了一层）
        with tempfile.TemporaryDirectory():
            pass
        src_root = tmp
        # 如果只有一个顶层目录且不是最终名，进入它
        entries = [e for e in os.listdir(src_root)]
        if len(entries) == 1 and os.path.isdir(os.path.join(src_root, entries[0])):
            inner = os.path.join(src_root, entries[0])
            # 有些 zip 顶层是 android-14 -> 其中还有一层
            final = os.path.join(parent, final_name)
            if os.path.exists(final):
                shutil.rmtree(final)
            shutil.move(inner, final)
            print(f"  落位 -> {final}", flush=True)
        else:
            final = os.path.join(parent, final_name)
            if os.path.exists(final):
                shutil.rmtree(final)
            os.makedirs(final, exist_ok=True)
            for e in entries:
                shutil.move(os.path.join(src_root, e), os.path.join(final, e))
            print(f"  落位 -> {final}", flush=True)
    print("  zip 顶层:", tops, flush=True)


def main():
    tmpdir = tempfile.mkdtemp(prefix="unitysdk_")
    for url, parent, final_name in JOBS:
        fname = os.path.basename(url)
        dest = os.path.join(tmpdir, fname)
        try:
            download(url, dest)
            extract_and_place(dest, parent, final_name)
        except Exception as e:
            print(f"  !! 失败 {fname}: {e!r}", flush=True)
        finally:
            try:
                os.remove(dest)
            except OSError:
                pass

    print("\n=== 最终 SDK 目录 ===", flush=True)
    for sub in ["build-tools", "platform-tools", "platforms", "cmdline-tools"]:
        fp = os.path.join(SDK, sub)
        print(f"  {sub}:", os.listdir(fp) if os.path.exists(fp) else "MISSING", flush=True)


if __name__ == "__main__":
    main()
