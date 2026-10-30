import json
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parent
BODY_PATH = ROOT / "fullbody-candidate-01" / "Suzume_fullbody_Hunyuan31_50k.glb"
HEAD_PATH = ROOT / "head-candidate-03" / "Suzume_head_Hunyuan31_50k.glb"
OUT = ROOT / "visionpro-character"
OUT.mkdir(parents=True, exist_ok=True)


def imported_meshes(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    return [obj for obj in bpy.data.objects if obj not in before and obj.type == "MESH"]


def bounds(objects):
    points = [obj.matrix_world @ Vector(corner) for obj in objects for corner in obj.bound_box]
    lo = Vector(tuple(min(p[i] for p in points) for i in range(3)))
    hi = Vector(tuple(max(p[i] for p in points) for i in range(3)))
    return lo, hi


bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

body_objects = imported_meshes(BODY_PATH)
body = max(body_objects, key=lambda obj: len(obj.data.polygons))
body.name = "Suzume_VisionPro_Body_50k"

# Remove the generated head while keeping the shirt, bow and lower neck.  The
# replacement bust overlaps this open boundary, so no seam is visible in the
# portal-scale view.
bm = bmesh.new()
bm.from_mesh(body.data)
cut_z = 0.955
delete_verts = [vert for vert in bm.verts if (body.matrix_world @ vert.co).z > cut_z]
bmesh.ops.delete(bm, geom=delete_verts, context="VERTS")
bm.to_mesh(body.data)
bm.free()
body.data.update()

head_objects = imported_meshes(HEAD_PATH)
head = max(head_objects, key=lambda obj: len(obj.data.polygons))
head.name = "Suzume_VisionPro_Head_50k"
head_scale = 0.280
head.scale = (head_scale,) * 3
head.location = (-0.0045, 0.0, 0.875)
bpy.context.view_layer.update()

lo, hi = bounds([body, head])
for obj in (body, head):
    obj["hunyuan_model"] = "3.1"
    obj["target"] = "Apple Vision Pro"
    obj["source_face_budget"] = "50k"

glb_path = OUT / "Suzume_character_VisionPro_merged_100k.glb"
bpy.ops.object.select_all(action="DESELECT")
for obj in (body, head):
    obj.select_set(True)
bpy.context.view_layer.objects.active = body
bpy.ops.export_scene.gltf(
    filepath=str(glb_path),
    export_format="GLB",
    use_selection=True,
    export_yup=True,
    export_animations=False,
)

report = {
    "bodySource": str(BODY_PATH),
    "headSource": str(HEAD_PATH),
    "bodyCutZ": cut_z,
    "headScale": head_scale,
    "headLocation": list(head.location),
    "dimensions": list(hi - lo),
    "vertices": sum(len(obj.data.vertices) for obj in (body, head)),
    "triangles": sum(len(obj.data.polygons) for obj in (body, head)),
    "output": str(glb_path),
}
(OUT / "merge-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print("VISIONPRO_CHARACTER=" + json.dumps(report, ensure_ascii=False))
