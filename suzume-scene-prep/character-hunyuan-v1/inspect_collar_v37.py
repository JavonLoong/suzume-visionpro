from pathlib import Path
import bpy,json,numpy as np
R=Path(__file__).parent;O=R/'movie-collar-v37';O.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'movie-face-v36/Suzume_scene_movie_face_v36.blend'));s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72)
ob=bpy.data.objects['Suzume Hunyuan textured surface'];e=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();m.calc_loop_triangles();world=np.array([ob.matrix_world@v.co for v in m.vertices]);faces=np.array([f.vertices[:] for f in m.loop_triangles]);e.to_mesh_clear()
head=bpy.data.objects['Suzume mathematical head v36'];neck_group=head.vertex_groups['Head part :: Clean neck'].index;neck_ids=[v.index for v in head.data.vertices if any(g.group==neck_group for g in v.groups)];e=head.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();neck=np.array([head.matrix_world@m.vertices[i].co for i in neck_ids]);e.to_mesh_clear()
uv=np.zeros((len(world),2));layer=ob.data.uv_layers.active
for loop in ob.data.loops:uv[loop.vertex_index]=layer.data[loop.index].uv[:]
np.savez_compressed(O/'body-source-v37.npz',world=world,faces=faces,local=np.array([v.co[:] for v in ob.data.vertices]),neck=neck,uv=uv)
report={'bodyVertices':len(world),'bodyTriangles':len(faces),'bodyBounds':[world.min(0).tolist(),world.max(0).tolist()],'neckBounds':[neck.min(0).tolist(),neck.max(0).tolist()],'modifiers':[{'name':m.name,'type':m.type} for m in ob.modifiers],'shapeKeys':[{'name':k.name,'value':k.value} for k in ob.data.shape_keys.key_blocks] if ob.data.shape_keys else [],'vertexGroups':[g.name for g in ob.vertex_groups],'materialSlots':[m.material.name for m in ob.material_slots]}
(O/'source-inspection-v37.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
