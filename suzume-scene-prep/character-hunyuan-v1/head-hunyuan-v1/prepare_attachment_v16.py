"""Prepare the CURRENT pose for replacement. The retained head is still original.

Never overwrite the viewer or its authoritative v16 source. Compare evaluated
triangles before and after separation to prove that preparing the seam has not
changed the fitted pose, shoe clearance, texture coordinates, or portal setup.
"""
import bpy, bmesh, hashlib, json
import numpy as np
from pathlib import Path

H = Path(__file__).parent
C = H.parent
bpy.ops.wm.open_mainfile(filepath=str(C / 'Suzume_scene_Hunyuan_v16.blend'))
day = bpy.data.scenes['Daytime circular hotel']
night = bpy.data.scenes['Night meadow through the door']
bpy.context.window.scene = day
day.frame_set(72)
body = bpy.data.objects['Suzume Hunyuan textured surface']
night_body = bpy.data.objects['Suzume Hunyuan entered portion']
rig = bpy.data.objects['Suzume Hunyuan rig']
inside = bpy.data.collections['Suzume — portion inside the otherworld']

def triangles(objects):
    chunks = []
    deps = bpy.context.evaluated_depsgraph_get()
    for obj in objects:
        evaluated = obj.evaluated_get(deps)
        mesh = evaluated.to_mesh(preserve_all_data_layers=True, depsgraph=deps)
        mesh.calc_loop_triangles()
        coords = np.empty((len(mesh.vertices), 3), np.float32)
        mesh.vertices.foreach_get('co', coords.ravel())
        matrix = np.array(obj.matrix_world, dtype=np.float64)
        coords = coords @ matrix[:3, :3].T + matrix[:3, 3]
        indices = np.empty((len(mesh.loop_triangles), 3), np.int32)
        mesh.loop_triangles.foreach_get('vertices', indices.ravel())
        chunks.append(coords[indices])
        evaluated.to_mesh_clear()
    result = np.concatenate(chunks)
    # Each triangle keeps its original winding and first corner on separation.
    quantized = np.rint(result.reshape((-1, 9)) * 1e6).astype(np.int64)
    order = np.lexsort(tuple(quantized[:, i] for i in range(8, -1, -1)))
    return quantized[order], float(result[:, :, 2].min())

before, minimum_before = triangles([body])
base = body.data.shape_keys.key_blocks[0].data
positions = np.empty((len(base), 3), np.float32)
base.foreach_get('co', positions.ravel())
rgb = np.load(C / 'character-vertex-albedo.npy').astype(float)
z, ax = positions[:, 2], np.abs(positions[:, 0])
hair_region = (z > .975) | ((z > .855) & (positions[:, 1] > .035) & (ax < .082)) | ((z > .925) & (ax < .085))
hair = (rgb.max(axis=1) < 145) & (rgb[:, 0] > rgb[:, 1] * 1.01) & hair_region
skin = (rgb[:, 0] > rgb[:, 1] * 1.07) & (rgb[:, 1] > rgb[:, 2] * 1.04) & (rgb[:, 0] > 115)
head_mask = (z > .984) | hair | (skin & (z > .951) & (ax < .070))
day_materials = [slot.material for slot in body.material_slots]
night_materials = [slot.material for slot in night_body.material_slots]
for obj in bpy.context.scene.objects:
    obj.select_set(False)
body.select_set(True)
bpy.context.view_layer.objects.active = body
objects_before = set(bpy.data.objects)
bpy.ops.object.mode_set(mode='EDIT')
bm = bmesh.from_edit_mesh(body.data)
bm.verts.ensure_lookup_table()
for face in bm.faces:
    face.select_set(False)
for edge in bm.edges:
    edge.select_set(False)
for vertex in bm.verts:
    vertex.select_set(bool(head_mask[vertex.index]))
for face in bm.faces:
    if all(head_mask[vertex.index] for vertex in face.verts):
        face.select_set(True)
bmesh.update_edit_mesh(body.data)
bpy.ops.mesh.separate(type='SELECTED')
bpy.ops.object.mode_set(mode='OBJECT')
head = next(obj for obj in bpy.data.objects if obj not in objects_before and obj.type == 'MESH')
head.name = 'Original head v16 — replacement reference only'
# Explicitly restore shared data; separation behavior must not depend on Blender
# choosing a particular linked object as the active mesh-data owner.
night_body.data = body.data
night_head = head.copy()
night_head.data = head.data
night_head.name = 'Original head v16 — otherworld reference only'
inside.objects.link(night_head)
for obj in [body, head, night_body, night_head]:
    materials = night_materials if obj in [night_body, night_head] else day_materials
    for slot, material in zip(obj.material_slots, materials):
        slot.link = 'OBJECT'
        slot.material = material
for obj in [head, night_head]:
    obj['replacement_status'] = 'Original Hunyuan head, extracted for alignment only. New independent head has NOT been generated.'
body['head_attachment_status'] = 'Current v16 pose preserved; uniform collar and original neck socket retained.'
bpy.context.view_layer.update()
after, minimum_after = triangles([body, head])
assert before.shape == after.shape, (before.shape, after.shape)
error = int(np.abs(before - after).max())
assert error <= 1, f'Separating head changed evaluated geometry by {error} micrometers'
assert len(rig.data.bones) == 20
assert night_body.data == body.data and night_head.data == head.data
for obj in [body, head, night_body, night_head]:
    assert any(mod.type == 'ARMATURE' and mod.object == rig for mod in obj.modifiers)
    expected = 'otherworld' if obj in [night_body, night_head] else 'courtyard'
    assert all(slot.material.get('spatial_half') == expected for slot in obj.material_slots)
    assert obj.data.uv_layers.active is not None
    assert obj.data.shape_keys.key_blocks['Film lower-body proportions v16'].value == 1

head_bone = rig.pose.bones['head']
neck_bone = rig.pose.bones['neck']
guide = {
    'stage': 'current_v16_attachment_prepared_not_a_replacement_head',
    'headModelSubmitted': False,
    'headModelGenerated': False,
    'headModelIntegrated': False,
    'source': 'Suzume_scene_Hunyuan_v16.blend',
    'output': 'head-socket-v16.blend',
    'trianglesBefore': len(before),
    'trianglesAfter': len(after),
    'bodyTriangles': len(body.data.polygons),
    'originalHeadTriangles': len(head.data.polygons),
    'maximumEvaluatedTriangleDifferenceMeters': error / 1e6,
    'minimumWorldHeightBefore': minimum_before,
    'minimumWorldHeightAfter': minimum_after,
    'triangleGeometryHashBefore': hashlib.sha256(before.tobytes()).hexdigest(),
    'triangleGeometryHashAfter': hashlib.sha256(after.tobytes()).hexdigest(),
    'rigBones': len(rig.data.bones),
    'shapeKeyPreserved': True,
    'sharedDayNightBodyGeometry': True,
    'sharedDayNightHeadGeometry': True,
    'complementaryPortalMaterialsPreserved': True,
    'nightInstanceIncludesHead': night_head.name in inside.objects,
    'rigWorldMatrix': [list(row) for row in rig.matrix_world],
    'headPoseMatrix': [list(row) for row in head_bone.matrix],
    'headRestMatrix': [list(row) for row in head_bone.bone.matrix_local],
    'neckPoseMatrix': [list(row) for row in neck_bone.matrix],
    'neckRestMatrix': [list(row) for row in neck_bone.bone.matrix_local],
    'notes': 'This is an unchanged-appearance preparation of v16. Both head objects are the OLD head. Align the new independent model in rest space, fit its neck inside the retained collar, and bind before replacing both references.',
    'oneToOneComplete': False,
}
day['Head replacement status'] = guide['notes']
text = bpy.data.texts.new('独立头模接合说明 v16')
text.write('此文件仍显示旧混元头部，并不是新头模。\n已保留 v16 的姿态、脚部间隙、服装、原 UV、骨骼与穿门裁切。\n新头模需要在静止空间对齐并接入颈口；庭院和异世界两侧须共同替换。\n')
bpy.ops.wm.save_as_mainfile(filepath=str(H / 'head-socket-v16.blend'))
(H / 'attachment-guide-v16.json').write_text(json.dumps(guide, ensure_ascii=False, indent=2), encoding='utf-8')
print('CURRENT_POSE_ATTACHMENT_VERIFIED', json.dumps(guide), flush=True)
