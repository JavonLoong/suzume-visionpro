from pathlib import Path
import bpy,json,numpy as np,hashlib
from mathutils.bvhtree import BVHTree
R=Path(__file__).parent;O=R/'poster-steel-v39'
bpy.ops.wm.open_mainfile(filepath=str(O/'Suzume_dual_scene_steel_v39.blend'))
s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1);bpy.context.view_layer.update()
def triangles(o):
    m=o.data;m.calc_loop_triangles();v=np.empty((len(m.vertices),3),np.float32);m.vertices.foreach_get('co',v.ravel());M=np.array(o.matrix_world);v=v@M[:3,:3].T+M[:3,3];faces=np.array([q.vertices[:] for q in m.loop_triangles]);return v,faces
ob=s.objects['Poster right I-section post 3 v39'];av,af=triangles(ob);aTree=BVHTree.FromPolygons(av.tolist(),af.tolist(),all_triangles=True)
def segment_hits_triangle(p,q,tri):
    direction=q-p;e1=tri[1]-tri[0];e2=tri[2]-tri[0];h=np.cross(direction,e2);det=np.dot(e1,h)
    if abs(det)<1e-10:return False
    inv=1/det;delta=p-tri[0];u=inv*np.dot(delta,h)
    if u<0 or u>1:return False
    z=np.cross(delta,e1);v=inv*np.dot(direction,z)
    if v<0 or u+v>1:return False
    t=inv*np.dot(e2,z);return 0<=t<=1
contacts=[]
for other in s.objects:
    if other.type!='MESH' or not other.name.startswith('Circular ruined hotel with exterior entrance solid mesh'):continue
    bv,bf=triangles(other);btree=BVHTree.FromPolygons(bv.tolist(),bf.tolist(),all_triangles=True)
    for ia,ib in aTree.overlap(btree):
        a=av[af[ia]];b=bv[bf[ib]]
        if any(segment_hits_triangle(a[i],a[(i+1)%3],b) or segment_hits_triangle(b[i],b[(i+1)%3],a) for i in range(3)):
            contacts.append({'roofObject':other.name,'ribTriangle':ia,'roofTriangle':ib});break
assert contacts,'Outer rib does not meet the existing roof geometry.'
report={'revision':39,'nativeSha256':hashlib.sha256((O/'Suzume_dual_scene_steel_v39.blend').read_bytes()).hexdigest(),'outerRibPhysicallyIntersectsRoof':True,'method':'Segment/triangle intersection on actual reopened native mesh triangles, after BVH candidate filtering.','contacts':contacts}
(O/'roof-contact-v39.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print('POSTER_39_ROOF_CONTACT_VERIFIED',len(contacts),flush=True)
