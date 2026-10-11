import bpy
import json
import os
from pathlib import Path

def report_ready():
    prefs = bpy.context.preferences.view
    report = {
        "pid": os.getpid(),
        "file": bpy.data.filepath,
        "language": prefs.language,
        "interface": prefs.use_translate_interface,
        "tooltips": prefs.use_translate_tooltips,
        "new_names": prefs.use_translate_new_dataname,
        "reports": prefs.use_translate_reports,
        "windows": len(bpy.context.window_manager.windows),
        "active_workspace": bpy.context.window.workspace.name,
        "workspaces": [w.name for w in bpy.data.workspaces],
        "scene_names": [s.name for s in bpy.data.scenes],
        "object_count": len(bpy.data.objects),
    }
    Path(__file__).with_name("中文窗口已打开.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return None

bpy.app.timers.register(report_ready, first_interval=1.0)
