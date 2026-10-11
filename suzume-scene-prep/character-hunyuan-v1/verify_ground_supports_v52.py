from pathlib import Path
import bpy,json,hashlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).parent;O=R/'poster-ground-v52';v=json.loads((O/'verification-v52.json').read_text());native=O/'Suzume_dual_scene_ground_v52.blend';assert hashlib.sha256(native.read_bytes()).hexdigest()==v['nativeSha256'];bpy.ops.wm.open_mainfile(filepath=str(native));s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1);bpy.context.view_layer.update();steel=json.loads((R/'poster-left-steel-v44/steel-geometry-v44.json').read_text());rows=[]
for q in steel['members']:
 if q['name'] not in ['Poster left outer splayed I-column v44','Poster left middle bowed I-column v44','Poster left back I-column v44']:continue
 foot=s.objects[q['name'].replace(' v44',' footing v44')];m=foot.data;tree=BVHTree.FromPolygons([foot.matrix_world@p.co for p in m.vertices],[p.vertices[:] for p in m.polygons],all_triangles=True);p=Vector(min(q['centerlineNative'],key=lambda p:p[2]));hit=tree.ray_cast(p+Vector((0,0,.5)),Vector((0,0,-1)),1.0);assert hit[0] is not None,(q['name'],list(p));overlap=hit[0].z-p.z;assert -.003<overlap<.25;rows.append({'column':q['name'],'columnBaseCenter':list(p),'supportSurfaceZ':hit[0].z,'embeddedDepthMeters':overlap})
foundation=s.objects['Poster broken stair foundation v52'];m=foundation.data;tree=BVHTree.FromPolygons([foundation.matrix_world@p.co for p in m.vertices],[p.vertices[:] for p in m.polygons],all_triangles=True);step=s.objects['Poster entrance v50 step 2'];positions=[step.matrix_world@p.co for p in step.data.vertices];minimum=min(p.z for p in positions);stair=[]
for p in positions:
 if abs(p.z-minimum)>1e-5:continue
 hit=tree.ray_cast(p+Vector((0,0,.10)),Vector((0,0,-1)),.20);assert hit[0] is not None;overlap=hit[0].z-p.z;assert 0<=overlap<.006;stair.append({'point':list(p),'supportSurfaceZ':hit[0].z,'overlapMeters':overlap})
assert len(stair)>=8
assert len(rows)==3;(O/'column-support-verification-v52.json').write_text(json.dumps({'nativeSha256':v['nativeSha256'],'threeColumnBasesSupported':True,'contacts':rows,'lowestStairTreadSupported':True,'stairContacts':stair},indent=2));print('GROUND_52_COLUMN_SUPPORTS_VERIFIED',rows,flush=True)
