from pathlib import Path
import bpy,numpy as np,json
R=Path(__file__).parent;O=R/'movie-hair-v33';O.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'movie-door-v32/Suzume_scene_movie_door_v32.blend'));s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72)
o=bpy.data.objects['Suzume independent Hunyuan head'];p=np.array([v.co[:] for v in o.data.vertices]);original=p.copy();original[:,0]+=.004;original[:,2]-=1.1751030684-.9738872647*.118;original/=.118
e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();v=np.array([q.co[:] for q in m.vertices]);M=np.asarray(o.matrix_world);world=v@M[:3,:3].T+M[:3,3];e.to_mesh_clear();faces=np.array([q.vertices[:] for q in o.data.polygons]);attrs=[{'name':a.name,'domain':a.domain,'type':a.data_type,'count':len(a.data)} for a in o.data.color_attributes]
np.savez_compressed(O/'head-source-v33.npz',local=p,original=original,world=world,faces=faces)
result={'localBounds':[p.min(0).tolist(),p.max(0).tolist()],'originalBounds':[original.min(0).tolist(),original.max(0).tolist()],'worldBounds':[world.min(0).tolist(),world.max(0).tolist()],'colorAttributes':attrs,'shapeKeys':list(o.data.shape_keys.key_blocks.keys()) if o.data.shape_keys else [],'parent':o.parent.name}
(O/'source-head-v33.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
