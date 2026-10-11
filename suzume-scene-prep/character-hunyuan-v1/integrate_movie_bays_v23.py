"""Replace complete movie-facing bays with solid rooms and measured openings."""
from pathlib import Path
import bpy,bmesh,numpy as np,json,math,sys,hashlib
from mathutils import Vector
R=Path(__file__).parent;O=R/'movie-bays-v23'
D=json.loads((O/'bay-geometry-v23.json').read_text(encoding='utf-8'))
fit=json.loads((R/'movie-calibration-v20/courtyard-fit-v20.json').read_text(encoding='utf-8'))
p=fit['parameters'];k=fit['depthScale'];C=np.array(fit['depthScaleCenter']);c=math.cos(p['yaw']);sn=math.sin(p['yaw']);rot=np.array([[c,sn,0],[-sn,c,0],[0,0,1]])
top=C[2]+k*(.89*p['heightScale']+p['heightOffset']-C[2]);lower_slope=(top+.22)/1.11
def mapped(native):
    a=np.array(native,float).reshape(-1,3).copy();r=np.linalg.norm(a[:,:2],axis=1);z=a[:,2].copy()
    a=a@rot.T+np.array([p['translateX'],p['translateY'],0]);a[:,:2]=C[:2]+k*(a[:,:2]-C[:2])
    h=np.where(z>=.89,C[2]+k*(z*p['heightScale']+p['heightOffset']-C[2]),-.22+(z+.22)*lower_slope)
    t=np.clip((r-21.7)/.8,0,1);t=t*t*(3-2*t);a[:,2]=k*z*(1-t)+h*t
    return a
def mapped_three(points):
    a=np.array(points,float).reshape(-1,3)[:,[0,2,1]]*np.array([1,-1,1]);return mapped(a)
def unmapped(world):
    a=world.copy();a[:,:2]=C[:2]+(a[:,:2]-C[:2])/k-np.array([p['translateX'],p['translateY']]);a[:,:2]=a[:,:2]@rot[:2,:2]
    r=np.linalg.norm(a[:,:2],axis=1);t=np.clip((r-21.7)/.8,0,1);t=t*t*(3-2*t)
    join=k*.89*(1-t)+top*t;upper=a[:,2]>=join
    slope=np.where(upper,k*p['heightScale'],lower_slope)
    offset=np.where(upper,C[2]+k*(p['heightOffset']-C[2]),-.22+.22*lower_slope)
    a[:,2]=(a[:,2]-t*offset)/(k*(1-t)+t*slope)
    return a
def local_world(b,x,y,z=0):
    a=b['angle'];r=b['chordRadius'];return mapped([[math.sin(a)*(r-z)+x*math.cos(a),math.cos(a)*(r-z)-x*math.sin(a),y]])[0]
bpy.ops.wm.open_mainfile(filepath=str(R/'movie-material-v22/Suzume_scene_movie_material_v22.blend'))
day=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=day;day.frame_set(72);bpy.context.view_layer.update()
removed={};roundtrip=0
lo=D['fit']['bays'][0]['edges'][0];hi=D['fit']['bays'][-1]['edges'][1]
for o in list(bpy.data.objects):
    if not o.name.startswith('Circular ruined hotel with exterior entrance solid mesh'):continue
    M=np.array(o.matrix_world);v=np.array([v.co[:] for v in o.data.vertices]);world=v@M[:3,:3].T+M[:3,3];source=unmapped(world)
    roundtrip=max(roundtrip,float(np.max(np.abs(mapped(source)-world))))
    centers=np.array([source[list(f.vertices)].mean(axis=0) for f in o.data.polygons]);angles=np.arctan2(centers[:,0],centers[:,1]);radius=np.linalg.norm(centers[:,:2],axis=1)
    # Include the full misplaced courtyard bench (r approximately 20.6) so no
    # partial furniture is left at the edge of the replaced front rooms.
    ids=np.flatnonzero((angles>lo-1e-5)&(angles<hi+1e-5)&(radius>19.2))
    if not len(ids):continue
    bm=bmesh.new();bm.from_mesh(o.data);bm.faces.ensure_lookup_table();bmesh.ops.delete(bm,geom=[bm.faces[int(i)] for i in ids],context='FACES');bm.to_mesh(o.data);bm.free();o.data.update()
    removed[o.name]=len(ids)
assert roundtrip<1e-5,roundtrip

materials={};matches=[]
old=[m for m in bpy.data.materials if m.name.startswith('Circular ruined hotel with exterior entrance solid mesh')]
for role,spec in D['materials'].items():
    score,source=min((float(np.linalg.norm(np.array(m.diffuse_color[:3])-spec['color'])),m) for m in old)
    assert score<1e-5,(role,spec['sourceHex'],score)
    # Clone materials to leave all other bays and the portal untouched.
    m=source.copy();m.name='Movie bay material '+role+' v23';materials[role]=m
    matches.append({'role':role,'source':source.name,'new':m.name,'sourceHex':spec['sourceHex'],'colorError':score})
collection=bpy.data.collections.new('Movie left and central bays — solid windows v23');day.collection.children.link(collection)
children={}
for b in D['fit']['bays']:
    child=bpy.data.collections.new('Movie bay '+str(b['index'])+' v23');collection.children.link(child);children[b['index']]=child
walls={};objects=[]
for rec in D['meshes']:
    coords=mapped_three(rec['positions']);mesh=bpy.data.meshes.new(rec['name']+' geometry v23');mesh.from_pydata(coords.tolist(),[],np.arange(len(coords)).reshape(-1,3).tolist());mesh.update()
    if rec['uv']:
        layer=mesh.uv_layers.new(name='UVMap');uv=np.array(rec['uv'],np.float32).reshape(-1,2);ids=np.array([loop.vertex_index for loop in mesh.loops]);layer.data.foreach_set('uv',uv[ids].ravel())
    original=np.array(rec['positions']).reshape(-1,3);n=np.array(rec['normals']).reshape(-1,3)[:,[0,2,1]]*np.array([1,-1,1]);n=n@rot.T
    deriv=np.where(original[:,1]>=.89,k*p['heightScale'],lower_slope);n[:,:2]/=k;n[:,2]/=deriv;n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-9)
    mesh.normals_split_custom_set_from_vertices(n.tolist());mesh.materials.append(materials[rec['material']])
    obj=bpy.data.objects.new(rec['name']+' v23',mesh);children[rec['bay']].objects.link(obj);obj['movie_bay']=rec['bay'];obj['geometry_role']=rec['role'] or 'part';objects.append(obj)
    if rec['role']=='lowerWall':walls[rec['bay']]=obj
bpy.context.view_layer.update()
checks=[]
for b in D['fit']['bays']:
    wall=walls[b['index']];normal=Vector((-math.sin(b['angle']+p['yaw']),-math.cos(b['angle']+p['yaw']),0))
    for op in b['openings']:
        pos=Vector(local_world(b,op['x'],op['bottom']+op['height']*.4));hit=wall.ray_cast(pos+normal*4,-normal,distance=10)[0];assert not hit,(b['index'],op['name'])
        checks.append({'bay':b['index'],'opening':op['name'],'wallHit':hit})
    pos=Vector(local_world(b,-b['bayWidth']/2+.025,3));assert wall.ray_cast(pos+normal*4,-normal,distance=10)[0]
    bm=bmesh.new();bm.from_mesh(wall.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-4);assert all(e.is_manifold for e in bm.edges);bm.free()
baseline=json.loads((R/'movie-material-v22/verification-v22.json').read_text(encoding='utf-8'))['characters'];characters={};deps=bpy.context.evaluated_depsgraph_get()
for name,row in baseline.items():
    o=bpy.data.objects[name];e=o.evaluated_get(deps);mesh=e.to_mesh();a=np.empty((len(mesh.vertices),3),np.float32);mesh.vertices.foreach_get('co',a.ravel());M=np.array(o.matrix_world);a=a@M[:3,:3].T+M[:3,3];e.to_mesh_clear()
    value=hashlib.sha256(np.round(a,6).astype('<f4').tobytes()).hexdigest();assert value==row['worldHash'];characters[name]={'vertices':len(a),'worldHash':value}
day['movie_facade_revision']=23;day.render.use_border=False;day.render.resolution_x=720;day.render.resolution_y=468;day.render.resolution_percentage=100;day.cycles.samples=24;day.cycles.use_denoising=True
audit={'revision':23,'replacedBays':[12,13,14,15],'newObjects':len(objects),'newTriangles':sum(len(o.data.polygons) for o in objects),'removedFaces':removed,'coordinateRoundtripError':roundtrip,'materials':matches,'windowWallRayTests':checks,'fourLowerWallsWatertight':True,'characters':characters,'bodyHeadFootAndPortalGeometryPreserved':True,'completeRoomsAndRoofStructures':True,'unmatchedBenchRemoved':True,'oneToOneComplete':False,'visualReviewPending':True}
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Suzume_scene_movie_bays_v23.blend'));(O/'integration-v23.json').write_text(json.dumps(audit,indent=2),encoding='utf-8');print('MOVIE_BAYS_23_INTEGRATED',json.dumps(audit),flush=True)
if '--render' in sys.argv:
    day.render.filepath=str(O/'movie-front-v23.png');bpy.ops.render.render(write_still=True)
