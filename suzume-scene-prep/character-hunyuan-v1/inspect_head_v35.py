from pathlib import Path
import bpy,json,numpy as np
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector
R=Path(__file__).parent;O=R/'movie-head-v35';O.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'movie-head-v34/Suzume_scene_movie_head_v34.blend'))
s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72)
s.render.resolution_x=2552;s.render.resolution_y=1656
h=bpy.data.objects['Suzume mathematical head v34'];e=h.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();m.calc_loop_triangles()
world=np.array([h.matrix_world@v.co for v in m.vertices]);faces=np.array([f.vertices[:] for f in m.loop_triangles]);e.to_mesh_clear()
uv=np.array([[p.x*2552,(1-p.y)*1656] for p in [world_to_camera_view(s,s.camera,Vector(v)) for v in world]])
groups={g.name:[v.index for v in h.data.vertices if any(q.group==g.index and q.weight>.5 for q in v.groups)] for g in h.vertex_groups if g.name.startswith('Head part :: ')}
report={name:{'vertices':len(ids),'min':uv[ids].min(axis=0).tolist(),'max':uv[ids].max(axis=0).tolist()} for name,ids in groups.items()}
np.savez_compressed(O/'head-source-v35.npz',world=world,faces=faces,uv=uv,local=np.array([v.co[:] for v in h.data.vertices]))
(O/'groups-v35.json').write_text(json.dumps(groups));(O/'source-inspection-v35.json').write_text(json.dumps(report,indent=2))
print('HEAD_35_INSPECTION',json.dumps(report),flush=True)
