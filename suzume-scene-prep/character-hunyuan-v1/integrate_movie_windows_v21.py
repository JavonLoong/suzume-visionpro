"""Replace one complete architectural bay with fitted, solid window geometry."""
import bpy,bmesh,json,math,sys,numpy as np,hashlib
from pathlib import Path
from mathutils import Vector
R=Path(__file__).parent;O=R/'movie-windows-v21';D=json.loads((O/'bay-geometry-v21.json').read_text());F=D['fit']
M20=R/'movie-calibration-v20';fit=json.loads((M20/'courtyard-fit-v20.json').read_text());p=fit['parameters'];k=fit['depthScale'];cam=np.array(fit['depthScaleCenter'])
c=math.cos(p['yaw']);s=math.sin(p['yaw']);rot=np.array([[c,s,0],[-s,c,0],[0,0,1]])
def map_points(a):
    a=np.array(a,float).reshape(-1,3);a=a[:,[0,2,1]]*np.array([1,-1,1]);r=np.linalg.norm(a[:,:2],axis=1);oldz=a[:,2].copy()
    a=a@rot.T+np.array([p['translateX'],p['translateY'],0]);a[:,:2]=cam[:2]+k*(a[:,:2]-cam[:2])
    top=cam[2]+k*(.89*p['heightScale']+p['heightOffset']-cam[2]);height=np.where(oldz>=.89,cam[2]+k*(oldz*p['heightScale']+p['heightOffset']-cam[2]),-.22+(oldz+.22)*(top+.22)/1.11)
    blend=np.clip((r-21.7)/.8,0,1);blend=blend*blend*(3-2*blend);a[:,2]=oldz*k*(1-blend)+height*blend
    return a
def world_local(x,y,z=0):
    a=F['angle'];r=F['chordRadius'];return map_points([[math.sin(a)*(r-z)+x*math.cos(a),y,-math.cos(a)*(r-z)+x*math.sin(a)]])[0]

# Identify the old bay on the unmodified source mesh, where region boundaries
# are exact and topology still matches the v20 copy one-to-one.
bpy.ops.wm.open_mainfile(filepath=str(R/'Suzume_scene_Hunyuan_v19.blend'))
cut={}
for o in bpy.data.objects:
    if not o.name.startswith('Circular ruined hotel with exterior entrance solid mesh'):continue
    a=np.array([v.co[:] for v in o.data.vertices]);a=a[:,[0,2,1]]*np.array([1,-1,1])
    centers=np.array([a[list(f.vertices)].mean(axis=0) for f in o.data.polygons]);angles=np.arctan2(centers[:,0],centers[:,1]);r=np.linalg.norm(centers[:,:2],axis=1)
    ids=np.flatnonzero((angles>F['edges'][0]-1e-5)&(angles<F['edges'][1]+1e-5)&(r>20.5))
    if len(ids):cut[o.name]={'faces':ids.tolist(),'originalFaces':len(o.data.polygons)}
bpy.ops.wm.open_mainfile(filepath=str(M20/'Suzume_scene_movie_candidate_v20.blend'))
day=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=day;day.frame_set(72);bpy.context.view_layer.update()
for name,row in cut.items():
    o=bpy.data.objects[name];assert len(o.data.polygons)==row['originalFaces']
    bm=bmesh.new();bm.from_mesh(o.data);bm.faces.ensure_lookup_table();bmesh.ops.delete(bm,geom=[bm.faces[i] for i in row['faces']],context='FACES');bm.to_mesh(o.data);bm.free();o.data.update()

materials={};material_matches=[]
oldm=[m for m in bpy.data.materials if m.name.startswith('Circular ruined hotel with exterior entrance solid mesh')]
for role,spec in D['materials'].items():
    scores=[(np.linalg.norm(np.array(m.diffuse_color[:3])-spec['color']),m) for m in oldm];score,mat=min(scores,key=lambda q:q[0]);assert score<1e-5,(role,score)
    materials[role]=mat;material_matches.append({'role':role,'material':mat.name,'colorError':float(score)})
collection=bpy.data.collections.new('Movie right facade — solid openings v21');day.collection.children.link(collection)
new_objects=[]
for rec in D['meshes']:
    coords=map_points(rec['positions']);mesh=bpy.data.meshes.new(rec['name']+' geometry v21');mesh.from_pydata(coords.tolist(),[],np.arange(len(coords)).reshape(-1,3).tolist());mesh.update()
    if rec['uv']:
        layer=mesh.uv_layers.new(name='UVMap');uv=np.array(rec['uv'],np.float32).reshape(-1,2);ids=np.array([loop.vertex_index for loop in mesh.loops]);layer.data.foreach_set('uv',uv[ids].ravel())
    original=np.array(rec['positions']).reshape(-1,3);n=np.array(rec['normals']).reshape(-1,3)[:,[0,2,1]]*np.array([1,-1,1]);n=n@rot.T
    top=cam[2]+k*(.89*p['heightScale']+p['heightOffset']-cam[2]);deriv=np.where(original[:,1]>=.89,k*p['heightScale'],(top+.22)/1.11)
    n[:,:2]/=k;n[:,2]/=deriv;n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-9)
    mesh.normals_split_custom_set_from_vertices(n.tolist());mesh.materials.append(materials[rec['material']])
    obj=bpy.data.objects.new(rec['name']+' v21',mesh);collection.objects.link(obj);new_objects.append(obj)
bpy.context.view_layer.update()

# The wall is solid through its thickness and genuinely open at both windows.
wall=next(o for o in new_objects if o.name.startswith('Solid plaster wall'))
normal=Vector((-math.sin(F['angle']+p['yaw']),-math.cos(F['angle']+p['yaw']),0))
checks=[]
for name,x,y,expect in [('oculus',F['oculus']['x'],F['oculus']['centerY'],False),('rectangle',F['rectangle']['x'],F['rectangle']['bottom']+F['rectangle']['height']/2,False),('plaster control',-F['bayWidth']*.465,3,True)]:
    pt=Vector(world_local(x,y));hit=wall.ray_cast(pt+normal*4,-normal,distance=10)[0];assert hit==expect,(name,hit);checks.append({'point':name,'wallHit':hit})
bm=bmesh.new();bm.from_mesh(wall.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-4);nonmanifold=sum(not e.is_manifold for e in bm.edges);bm.free();assert nonmanifold==0,nonmanifold

body=bpy.data.objects['Suzume Hunyuan textured surface'];e=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();a=np.empty((len(m.vertices),3),np.float32);m.vertices.foreach_get('co',a.ravel());M=np.array(body.matrix_world);a=a@M[:3,:3].T+M[:3,3];e.to_mesh_clear()
bodyhash=hashlib.sha256(np.round(a,6).astype('<f4').tobytes()).hexdigest();assert bodyhash=='bda994f4f36c980ac7e48122ea45f395ce5defbd723d5c82f514aeca5561de47'
day['movie_facade_revision']=21;day.render.resolution_x=720;day.render.resolution_y=468;day.render.resolution_percentage=100;day.cycles.samples=32;day.cycles.use_denoising=True
audit={'revision':21,'replacedBay':16,'removedFaces':{n:len(q['faces']) for n,q in cut.items()},'newObjects':len(new_objects),'newTriangles':sum(len(o.data.polygons) for o in new_objects),'materials':material_matches,'windowWallRayTests':checks,'wallNonmanifoldEdgesAfterWelding':nonmanifold,'bodyWorldHash':bodyhash,'oneToOneComplete':False,'visualReviewPending':True}
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Suzume_scene_movie_windows_v21.blend'));(O/'integration-v21.json').write_text(json.dumps(audit,indent=2),encoding='utf-8');print('WINDOW_BAY_INTEGRATED',json.dumps(audit),flush=True)
if '--render' in sys.argv:
    day.render.filepath=str(O/'movie-front-v21.png');bpy.ops.render.render(write_still=True)
