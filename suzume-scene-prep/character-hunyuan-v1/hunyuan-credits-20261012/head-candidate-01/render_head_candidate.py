import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


SCRIPT_ROOT = Path(__file__).resolve().parent
script_args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
MODEL = Path(script_args[0]).resolve() if script_args else SCRIPT_ROOT / "Suzume_head_Hunyuan31_1p5m.glb"
ROOT = Path(script_args[1]).resolve() if len(script_args) > 1 else MODEL.parent
VIEWS = {
    "y_minus": Vector((0.0, -1.0, 0.0)),
    "y_plus": Vector((0.0, 1.0, 0.0)),
    "x_minus": Vector((-1.0, 0.0, 0.0)),
    "x_plus": Vector((1.0, 0.0, 0.0)),
}


def look_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(MODEL))

meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
corners = []
for obj in meshes:
    corners.extend(obj.matrix_world @ Vector(corner) for corner in obj.bound_box)

mins = Vector(tuple(min(v[i] for v in corners) for i in range(3)))
maxs = Vector(tuple(max(v[i] for v in corners) for i in range(3)))
center = (mins + maxs) * 0.5
size = maxs - mins

scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 640
scene.render.resolution_y = 640
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.film_transparent = False
scene.render.image_settings.color_mode = "RGBA"
scene.view_settings.look = "AgX - Medium High Contrast"
scene.world.color = (0.035, 0.035, 0.035)

camera_data = bpy.data.cameras.new("InspectionCamera")
camera = bpy.data.objects.new("InspectionCamera", camera_data)
scene.collection.objects.link(camera)
scene.camera = camera
camera.data.type = "ORTHO"
camera.data.lens = 70

def add_area(name, location, energy, size_m):
    data = bpy.data.lights.new(name=name, type="AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size_m
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.location = center + Vector(location)
    look_at(obj, center)
    return obj


span = max(size)
add_area("Key", (-1.2 * span, -1.4 * span, 1.2 * span), 750, 1.3 * span)
add_area("Fill", (1.3 * span, -0.8 * span, 0.3 * span), 420, 1.0 * span)
add_area("Rim", (0.6 * span, 1.4 * span, 1.0 * span), 650, 0.9 * span)

for name, direction in VIEWS.items():
    camera.location = center + direction * (3.2 * span)
    look_at(camera, center)
    horizontal = size.x if abs(direction.y) > 0.5 else size.y
    camera.data.ortho_scale = max(size.z, horizontal) * 1.18
    scene.render.filepath = str(ROOT / f"render-{name}.png")
    bpy.ops.render.render(write_still=True)

report = {
    "model": str(MODEL),
    "mesh_count": len(meshes),
    "vertices": sum(len(obj.data.vertices) for obj in meshes),
    "triangles": sum(len(obj.data.polygons) for obj in meshes),
    "bounds_min": list(mins),
    "bounds_max": list(maxs),
    "dimensions": list(size),
    "materials": sorted({mat.name for obj in meshes for mat in obj.data.materials if mat}),
    "renders": [str(ROOT / f"render-{name}.png") for name in VIEWS],
}
(ROOT / "inspection.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print("HEAD_INSPECTION=" + json.dumps(report, ensure_ascii=False))
