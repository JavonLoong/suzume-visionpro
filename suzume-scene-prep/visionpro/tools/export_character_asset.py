"""Export the selected lightweight Hunyuan character to a metre-scale USDZ."""
import hashlib
import json
from pathlib import Path

import bpy
from mathutils import Matrix, Vector


ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "VisionProPortal" / "VisionProPortal" / "Resources"
VALIDATION = ROOT / "validation"
TEXTURE_CACHE = VALIDATION / "character-textures"
SOURCE = (
    ROOT.parent
    / "character-hunyuan-v1"
    / "hunyuan-credits-20261012"
    / "visionpro-character"
    / "Suzume_character_VisionPro_merged_100k.glb"
)
DESTINATION = RES / "Character.usdz"
TARGET_HEIGHT_METRES = 1.62

RES.mkdir(parents=True, exist_ok=True)
VALIDATION.mkdir(parents=True, exist_ok=True)
TEXTURE_CACHE.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(SOURCE))

# The portal character is viewed several metres away. Keeping the six source
# maps at 4K would add over 50 MB to the app with no visible benefit on device.
for index, image in enumerate(bpy.data.images):
    if image.source == "FILE" and max(image.size) > 2048:
        image.scale(2048, 2048)
        safe_name = "".join(char if char.isalnum() else "_" for char in image.name)
        path = TEXTURE_CACHE / f"{index:02d}_{safe_name}.png"
        image.filepath_raw = str(path)
        image.file_format = "PNG"
        image.save()
        image.pack()

meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
corners = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
lo = Vector(tuple(min(point[i] for point in corners) for i in range(3)))
hi = Vector(tuple(max(point[i] for point in corners) for i in range(3)))
centre = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
scale = TARGET_HEIGHT_METRES / (hi.z - lo.z)
normalise = Matrix.Scale(scale, 4) @ Matrix.Translation(-centre)

for obj in meshes:
    obj.data.transform(normalise @ obj.matrix_world)
    obj.matrix_world = Matrix.Identity(4)
    obj.name = "SuzumeCharacter_" + obj.name

bpy.ops.wm.usd_export(
    filepath=str(DESTINATION),
    selected_objects_only=False,
    export_animation=False,
    export_textures_mode="NEW",
    export_materials=True,
    generate_preview_surface=True,
    generate_materialx_network=False,
    export_armatures=False,
    export_shapekeys=False,
    export_lights=False,
    export_cameras=False,
    export_volumes=False,
    export_curves=False,
    export_points=False,
    triangulate_meshes=True,
    convert_orientation=True,
    export_global_forward_selection="NEGATIVE_Z",
    export_global_up_selection="Y",
    convert_scene_units="METERS",
    meters_per_unit=1.0,
    root_prim_path="/SuzumeCharacter",
    relative_paths=True,
    usdz_downscale_size="KEEP",
)

triangles = sum(sum(len(poly.vertices) - 2 for poly in obj.data.polygons) for obj in meshes)
report = {
    "source": str(SOURCE),
    "sourceSHA256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "output": str(DESTINATION),
    "outputSHA256": hashlib.sha256(DESTINATION.read_bytes()).hexdigest(),
    "bytes": DESTINATION.stat().st_size,
    "triangles": triangles,
    "objects": len(meshes),
    "targetHeightMetres": TARGET_HEIGHT_METRES,
    "scale": scale,
    "origin": "feet centre",
    "upAxis": "Y",
    "maximumTextureSize": 2048,
}
(VALIDATION / "character_export.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
)

for manifest_path in (RES / "AssetManifest.json", VALIDATION / "export_manifest.json"):
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["character"] = {
        "source": str(SOURCE),
        "sourceSHA256": report["sourceSHA256"],
        "heightMetres": TARGET_HEIGHT_METRES,
        "origin": "feet centre",
        "placement": [0.0, 0.0, -2.7],
        "yawDegrees": 180.0,
    }
    manifest.setdefault("files", {})["Character.usdz"] = {
        "bytes": report["bytes"],
        "sha256": report["outputSHA256"],
        "triangles": triangles,
        "objects": len(meshes),
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

print("CHARACTER_EXPORT=" + json.dumps(report, ensure_ascii=False))
