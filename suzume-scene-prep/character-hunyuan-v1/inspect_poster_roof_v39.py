from pathlib import Path
import bpy,numpy as np,json
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).parent;O=R/'poster-steel-v39'
bpy.ops.wm.open_mainfile(filepath=str(R/'poster-v38/Suzume_dual_scene_v38.blend'))
s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1);bpy.context.view_layer.update()
vertices=[];faces=[];offset=0
for ob in s.objects:
 if ob.type!='MESH' or not ob.name.startswith('Circular ruined hotel with exterior entrance solid mesh'):continue
 a=np.empty((len(ob.data.vertices),3),np.float32);ob.data.vertices.foreach_get('co',a.ravel());M=np.array(ob.matrix_world);a=a@M[:3,:3].T+M[:3,3]
 vertices.extend(a.tolist());faces.extend([[idx+offset for idx in p.vertices] for p in ob.data.polygons]);offset+=len(a)
tree=BVHTree.FromPolygons(vertices,faces,all_triangles=True);cam=s.camera;M=np.array(cam.matrix_world);C=M[:3,3];f=cam.data.lens/36*2824;rows=[]
for uv in [[1898,1580],[1898,1600],[1898,1610],[1898,1620],[1898,1640],[1900,1660]]:
 direction=np.array([(uv[0]-1000)/f,(1412-uv[1])/f,-1])@M[:3,:3].T;direction/=np.linalg.norm(direction)
 hit=tree.ray_cast(Vector(C),Vector(direction));rows.append({'pixel':uv,'roofWorld':list(hit[0]) if hit[0] else None,'normal':list(hit[1]) if hit[1] else None,'distance':hit[3]})
(O/'roof-attachment-v39.json').write_text(json.dumps(rows,indent=2),encoding='utf-8');print(json.dumps(rows,indent=2),flush=True)
