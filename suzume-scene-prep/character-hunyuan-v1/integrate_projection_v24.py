"""Build a separate complete 3D camera/courtyard candidate, preserving v23."""
from pathlib import Path
import bpy, bmesh, sys, json, math, hashlib
import numpy as np
from mathutils import Vector, Matrix, Euler
R=Path(__file__).parent;sys.path.insert(0,str(R))
from projection_geometry_v24 import O,F,P,old_edges,new_edges,map_source,place_new_bay,height,center,bay_spec

def world_vertices(o):
    a=np.empty((len(o.data.vertices),3),np.float64);o.data.vertices.foreach_get('co',a.ravel());M=np.array(o.matrix_world)
    return a@M[:3,:3].T+M[:3,3]
def set_world(o,a):
    inv=np.linalg.inv(np.array(o.matrix_world));a=a@inv[:3,:3].T+inv[:3,3]
    o.data=o.data.copy();o.data.vertices.foreach_set('co',a.astype('f4').ravel());o.data.update()
    if not o.modifiers:
        try:o.data.normals_split_custom_set([(0,0,0)]*len(o.data.loops))
        except Exception:pass

# Original arrays avoid ambiguous inversions of the selectively moved ivy and
# debris; all near-door geometry remains byte-for-byte equivalent in world space.
bpy.ops.wm.open_mainfile(filepath=str(R/'Suzume_scene_Hunyuan_v19.blend'))
s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72);bpy.context.view_layer.update()
environment={}
for o in s.objects:
    if o.type!='MESH':continue
    n=o.name
    if n.startswith(('Broken radial dome steelwork solid mesh','Brick and masonry debris solid mesh')) or n in ['Individual three-dimensional ivy leaves','Branching tree crowns surrounding the ruined hotel','Forest trunks','Continuous forest terrain','Live planar reflective shallow water','Flooded polygon flagstones and broken slabs solid mesh']:
        row={'world':world_vertices(o),'matrix':np.array(o.matrix_world)}
        for key in ['instance_rotation','instance_scale']:
            attr=o.data.attributes.get(key)
            if attr:row[key]=np.array([d.vector[:] for d in attr.data])
        environment[n]=row

bpy.ops.wm.open_mainfile(filepath=str(R/'movie-bays-v23/Suzume_scene_movie_bays_v23.blend'))
s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72);bpy.context.view_layer.update()
changes=[]
oldfit=json.loads((R/'movie-calibration-v20/courtyard-fit-v20.json').read_text(encoding='utf-8'))
p=oldfit['parameters'];k=oldfit['depthScale'];C=np.array(oldfit['depthScaleCenter']);c,sn=np.cos(p['yaw']),np.sin(p['yaw']);rot=np.array([[c,sn],[-sn,c]])
top=C[2]+k*(.89*p['heightScale']+p['heightOffset']-C[2]);ls=(top+.22)/1.11
def unmap_20(a):
    a=a.copy();a[:,:2]=(C[:2]+(a[:,:2]-C[:2])/k-[p['translateX'],p['translateY']])@rot
    t=np.clip((np.linalg.norm(a[:,:2],axis=1)-21.7)/.8,0,1);t=t*t*(3-2*t)
    upper=a[:,2]>=k*.89*(1-t)+top*t;slope=np.where(upper,k*p['heightScale'],ls)
    off=np.where(upper,C[2]+k*(p['heightOffset']-C[2]),-.22+.22*ls)
    a[:,2]=(a[:,2]-t*off)/(k*(1-t)+t*slope)
    return a
for o in list(bpy.data.objects):
    if o.name.startswith('Circular ruined hotel with exterior entrance solid mesh'):
        set_world(o,map_source(unmap_20(world_vertices(o))));changes.append({'name':o.name,'operation':'Continuous ring and shared levels'})

# Selected facade meshes are rebuilt, not projected textures or flattened cards.
oldright={o.name[:-4]:o.data.materials[0] for o in bpy.data.collections['Movie right facade — solid openings v21'].objects}
for cname in ['Movie left and central bays — solid windows v23','Movie right facade — solid openings v21']:
    col=bpy.data.collections[cname]
    for o in list(col.all_objects):bpy.data.objects.remove(o,do_unlink=True)
    for child in list(col.children):bpy.data.collections.remove(child)
    bpy.data.collections.remove(col)
newcol=bpy.data.collections.new('Movie courtyard projection v24 — complete solid rooms');s.collection.children.link(newcol)
walls={};newcount=0
for filename,which in [('bay-geometry-v24.json','left'),('right-geometry-v24.json','right')]:
    D=json.loads((O/filename).read_text(encoding='utf-8'))
    for rec in D['meshes']:
        index=rec.get('bay',16);a=place_new_bay(rec['positions'],index)
        mesh=bpy.data.meshes.new(rec['name']+' geometry v24');mesh.from_pydata(a.tolist(),[],np.arange(len(a)).reshape(-1,3).tolist());mesh.update()
        if rec.get('uv'):
            layer=mesh.uv_layers.new(name='UVMap');uv=np.array(rec['uv'],np.float32).reshape(-1,2);ids=np.array([l.vertex_index for l in mesh.loops]);layer.data.foreach_set('uv',uv[ids].ravel())
        z=np.array(rec['positions']).reshape(-1,3)[:,1];dz=(height(z+1e-5,index)-height(z-1e-5,index))/2e-5
        n=np.array(rec['normals']).reshape(-1,3)[:,[0,2,1]]*[1,-1,1];n[:,2]/=dz;n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-9)
        mesh.normals_split_custom_set_from_vertices(n.tolist())
        mat=bpy.data.materials['Movie bay material '+rec['material']+' v23'] if which=='left' else oldright[rec['name']]
        mesh.materials.append(mat);o=bpy.data.objects.new(rec['name']+' v24',mesh);newcol.objects.link(o);o['movie_bay']=index
        if rec.get('role')=='lowerWall' or rec['name'].startswith('Solid plaster wall'):walls[index]=o;o['geometry_role']='lowerWall'
        newcount+=1

rot_angle=float(np.mean(new_edges[13:18]-old_edges[13:18]));cr,sr=np.cos(rot_angle),np.sin(rot_angle);rigid=np.array([[cr,sr,0],[-sr,cr,0],[0,0,1]])
for name,row in environment.items():
    if name=='Flooded polygon flagstones and broken slabs solid mesh':continue
    o=bpy.data.objects[name];v=row['world'];a=v.copy();far=np.linalg.norm(v[:,:2],axis=1)>8
    if name.startswith('Broken radial dome'):
        a=map_source(v,architectural=False)
    elif name.startswith('Brick and masonry') or name=='Individual three-dimensional ivy leaves':
        a[far]=map_source(v[far],architectural=name.startswith('Individual'))
    else:
        # A geometry-nodes emitter must restore its object matrix too, or its
        # instances keep the inherited 3x scale even when the points are fixed.
        o.matrix_world=Matrix(row['matrix']);set_world(o,v)
        matrix=np.eye(4);matrix[:3,:3]=rigid;matrix[:3,3]=center
        o.matrix_world=Matrix(matrix)@Matrix(row['matrix'])
        a=v@rigid.T+center
    if name.startswith(('Broken radial dome','Brick and masonry')) or name=='Individual three-dimensional ivy leaves':set_world(o,a)
    if name=='Individual three-dimensional ivy leaves':
        # Restore source size and rotate each far leaf with its new bay.
        for key in ['instance_scale','instance_rotation']:
            if key not in row:continue
            for i,d in enumerate(o.data.attributes[key].data):d.vector=row[key][i]
        attr=o.data.attributes.get('instance_rotation')
        for i in np.flatnonzero(far):
            oldang=math.atan2(v[i,0],v[i,1]);newang=math.atan2(a[i,0]-center[0],a[i,1]-center[1]);delta=newang-oldang
            attr.data[int(i)].vector=(Matrix.Rotation(-delta,4,'Y')@Euler(row['instance_rotation'][i],'XYZ').to_matrix().to_4x4()).to_euler('XYZ')
    changes.append({'name':name,'operation':'Source-scale environment','vertices':len(a),'nearGeometryPreserved':bool(np.allclose(a[~far],v[~far])) if name.startswith(('Brick','Individual')) else None})
bed=bpy.data.objects.get('Movie courtyard continuous basin bed')
if bed:
    original=environment['Flooded polygon flagstones and broken slabs solid mesh']['world'];a=original@rigid.T+center;a[:,2]-=.04;set_world(bed,a)

camera=bpy.data.objects['Door front camera'];camera.animation_data_clear();camera.data.animation_data_clear()
camera.location=(P['cameraX'],-P['distance'],P['cameraZ']);camera.rotation_euler=(math.pi/2-P['pitch'],0,0);camera.data.lens=P['lensMm'];camera.data.sensor_fit='VERTICAL';camera.data.sensor_height=36
s.camera=camera

# The previous night hill (18 m high) was composed for a different, wider
# reference shot. Keep the first 12 m intact and lower the distant ridge for
# this movie camera; every plant follows the same continuous ground change.
night_changes=[]
def night_drop(v):
    # These meshes use local Three Y-up coordinates under the native axes root.
    x=v[:,0];depth=-v[:,2];t=np.clip((depth-12)/28,0,1);t=t*t*(3-2*t)
    return 16.8*np.exp(-((depth-116)/39)**2)*(.78+.22*np.sin(x*.024+.8)**2)*t
for name in ['Rolling meadow ground','Individual meadow flowers','Modeled flower stems','Spatial grass blades']:
    o=bpy.data.objects[name];v=np.empty((len(o.data.vertices),3),np.float64);o.data.vertices.foreach_get('co',v.ravel());delta=night_drop(v);v[:,1]-=delta
    o.data=o.data.copy();o.data.vertices.foreach_set('co',v.astype('f4').ravel());o.data.update()
    if name=='Rolling meadow ground':o.data.normals_split_custom_set([(0,0,0)]*len(o.data.loops))
    night_changes.append({'name':name,'maximumHeightReduction':float(delta.max()),'near12MetersUnchanged':True})
for o in bpy.data.collections['Editable night realm'].all_objects:
    if o.name.startswith('Spatial twilight cloud volume '):o.location.y*=.25;o.scale.y*=.25

def local_point(i,x,z):
    b=bay_spec(i);a=b['angle'];r=b['chordRadius'];return Vector((np.sin(a)*r+x*np.cos(a)+center[0],np.cos(a)*r-x*np.sin(a)+center[1],z))
light_specs=[]
for name,i,x,z,dist,lift,power,size in [
    ('Cool courtyard fill on the left facade v23',13,-.3,3.5,3.2,1.4,64,(7,5)),
    ('Localized sunlight around the arched window v23',13,2.25,2.8,3.2,2.2,1200,None),
    ('Soft courtyard fill on the movie facade v22',16,0,3.7,3.5,1.25,1000,(5.5,4.5))]:
    ob=bpy.data.objects[name];a=bay_spec(i)['angle'];normal=Vector((-np.sin(a),-np.cos(a),0));target=local_point(i,x,z);ob.location=target+normal*dist+Vector((0,0,lift));ob.rotation_euler=(target-ob.location).to_track_quat('-Z','Y').to_euler();ob.data.energy=power
    if size:ob.data.size,ob.data.size_y=size
    else:ob.data.shadow_soft_size=.05
    light_specs.append({'name':name,'type':ob.data.type,'position':list(ob.location),'target':list(target),'color':list(ob.data.color),'powerWatts':power,'dimensions':size,'angleRadians':ob.data.spot_size/2 if ob.data.type=='SPOT' else None})

bpy.context.view_layer.update()
baseline=json.loads((R/'movie-bays-v23/verification-v23.json').read_text(encoding='utf-8'))['characters'];characters={}
for name,row in baseline.items():
    o=bpy.data.objects[name];e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=e.to_mesh();a=np.empty((len(mesh.vertices),3),np.float32);mesh.vertices.foreach_get('co',a.ravel());M=np.array(o.matrix_world);a=a@M[:3,:3].T+M[:3,3];e.to_mesh_clear();value=hashlib.sha256(np.round(a,6).astype('<f4').tobytes()).hexdigest();assert value==row['worldHash'];characters[name]=row
for i,wall in walls.items():
    bm=bmesh.new();bm.from_mesh(wall.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-4);assert all(e.is_manifold for e in bm.edges),(i,'wall topology');bm.free()
s['movie_facade_revision']=24;s['courtyard_radius']=23.5;s['one_to_one_complete']=False
s.render.use_border=False;s.render.resolution_x=720;s.render.resolution_y=468;s.render.resolution_percentage=100;s.cycles.samples=24;s.cycles.use_denoising=True
audit={'revision':24,'parameters':P,'courtyardRadius':23.5,'newObjects':newcount,'changes':changes,'nightLandscapeChanges':night_changes,'cloudHeightFactor':.25,'lights':light_specs,'characters':characters,'fiveWallsWatertight':True,'oneToOneComplete':False,'visualReviewPending':True}
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Suzume_scene_movie_projection_v24.blend'));(O/'integration-v24.json').write_text(json.dumps(audit,indent=2),encoding='utf-8');print('PROJECTION_24_SAVED',newcount,flush=True)
if '--render' in sys.argv:
    s.render.filepath=str(O/'movie-front-v24.png');bpy.ops.render.render(write_still=True)

