from pathlib import Path
import ast, hashlib, json
import bpy, bmesh, numpy as np
from mathutils import Vector

R=Path(__file__).parent; O=R/'poster-horizon-v42'; C=R/'poster-clouds-v41'
native=O/'Suzume_dual_scene_horizon_v42.blend'
geometry=json.loads((O/'horizon-geometry-v42.json').read_text())
source=np.load(O/'horizon-geometry-v42.npz')
oldspec=json.loads((C/'cloud-geometry-v41.json').read_text())
olddata=np.load(C/'cloud-geometry-v41.npz')
changed=set(geometry['replaces'])|{geometry['name']}
tree=ast.parse((R/'verify_render_poster_v38.py').read_text())
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['tree_hash','movie_snapshot']],type_ignores=[]),'snapshot helpers','exec'))

def scene_snapshot(name):
    s=bpy.data.scenes[name]; bpy.context.window.scene=s
    if name=='Official poster courtyard v38':s.frame_set(1)
    bpy.context.view_layer.update(); objects={}; materials={}
    for ob in s.objects:
        if ob.type=='MESH':
            for mat in ob.data.materials:
                if mat:materials[mat.name]=tree_hash(mat.node_tree)
        if ob.name in changed:continue
        rec={'matrix':np.array(ob.matrix_world).tolist(),'type':ob.type,'render':ob.hide_render,'modifiers':[[m.name,m.type,m.show_render,m.show_viewport] for m in ob.modifiers]}
        if ob.type=='MESH':
            rec['materials']=[m.name if m else None for m in ob.data.materials]
            v=np.empty(len(ob.data.vertices)*3,np.float32); ob.data.vertices.foreach_get('co',v)
            ix=np.empty(len(ob.data.loops),np.int32); ob.data.loops.foreach_get('vertex_index',ix)
            rec['mesh']=hashlib.sha256(v.tobytes()+ix.tobytes()).hexdigest()
            for attr in ob.data.color_attributes:
                colors=np.empty(len(attr.data)*4,np.float32); attr.data.foreach_get('color',colors)
                rec['color_'+attr.name]=hashlib.sha256(colors.tobytes()).hexdigest()
        objects[ob.name]=rec
    camera=None if s.camera is None else [s.camera.name,np.array(s.camera.matrix_world).tolist(),s.camera.data.lens]
    return {'objects':objects,'materials':materials,'world':tree_hash(s.world.node_tree) if s.world else None,'camera':camera,'colors':[s.view_settings.view_transform,s.view_settings.look,s.view_settings.exposure]}

bpy.ops.wm.open_mainfile(filepath=str(C/'Suzume_dual_scene_clouds_v41.blend'))
movie_before=movie_snapshot(); poster_before=scene_snapshot('Official poster courtyard v38'); night_before=scene_snapshot('Night meadow through the door')
groups_before={n.name:tree_hash(n) for n in bpy.data.node_groups}
bpy.ops.wm.open_mainfile(filepath=str(native))
assert movie_before==movie_snapshot(),'Movie changed'
assert poster_before==scene_snapshot('Official poster courtyard v38'),'Unrelated poster state changed'
assert night_before==scene_snapshot('Night meadow through the door'),'Night scene changed'
assert groups_before=={n.name:tree_hash(n) for n in bpy.data.node_groups},'Shared node groups changed'
s=bpy.data.scenes['Official poster courtyard v38']; bpy.context.window.scene=s;s.frame_set(1);bpy.context.view_layer.update()
assert len(s.objects)==248
assert not any(name in s.objects for name in geometry['replaces'])
records=[q for q in oldspec['clouds'] if q['name'] not in geometry['replaces']]+[{'name':geometry['name'],'key':None}]
assert len(records)==27
rows=[];payload=[];offset=0;export=[];probes={}
P=np.array([[1,0,0,0],[0,0,1,0],[0,-1,0,0],[0,0,0,1]],float)
for q in records:
    ob=s.objects[q['name']];m=ob.data
    v=np.empty((len(m.vertices),3),np.float32);m.vertices.foreach_get('co',v.ravel())
    M=np.array(ob.matrix_world);world=v@M[:3,:3].T+M[:3,3]
    expected_world=source['world'] if q['key'] is None else olddata[q['key']+'_world']
    difference=float(np.max(abs(world-expected_world)));assert difference<3e-5,(ob.name,difference)
    if q['key'] is None:assert np.array_equal(v,source['local'])
    m.calc_loop_triangles();faces=np.array([t.vertices[:] for t in m.loop_triangles],dtype='<u4')
    expected_faces=source['faces'] if q['key'] is None else olddata[q['key']+'_faces']
    assert np.array_equal(faces,expected_faces)
    area=np.linalg.norm(np.cross(v[faces[:,1]]-v[faces[:,0]],v[faces[:,2]]-v[faces[:,0]]),axis=1)/2
    assert np.all(area>0),(ob.name,int((area==0).sum()))
    bm=bmesh.new();bm.from_mesh(m);bad=sum(not e.is_manifold for e in bm.edges);volume=bm.calc_volume();bm.free()
    assert bad==0 and volume>0,(ob.name,bad,volume)
    rgba=np.empty((len(v),4),np.float32);m.color_attributes['surface_color'].data.foreach_get('color',rgba.ravel())
    rgb=source['rgb'] if q['key'] is None else olddata[q['key']+'_rgb']
    expected=np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4);assert np.max(abs(rgba[:,:3]-expected))<1e-7
    normals=np.empty((len(v),3),np.float32);m.vertices.foreach_get('normal',normals.ravel())
    arrays=[(v[:,[0,2,1]]*[1,1,-1]).astype('<f4'),(normals[:,[0,2,1]]*[1,1,-1]).astype('<f4'),rgba[:,:3].astype('<f4'),faces]
    info={'name':ob.name.removesuffix('.001'),'vertices':len(v),'triangles':len(faces),'matrix':(P@M@P.T).T.ravel().tolist()}
    for name,a in zip(['positions','normals','colors','indices'],arrays):
        raw=a.tobytes();info[name]={'byteOffset':offset,'byteLength':len(raw)};payload.append(raw);offset+=len(raw)
    export.append(info)
    probes[info['name']]=[{'index':int(i),'nativeWorld':expected_world[i].tolist()} for i in [0,len(v)//3,len(v)-1]]
    rows.append({'name':ob.name,'vertices':len(v),'triangles':len(faces),'nonManifoldEdges':bad,'signedLocalVolume':volume,'minimumLocalTriangleArea':float(area.min()),'maxWorldVertexErrorMeters':difference,'pigmentsMatchSource':True})
binary=b''.join(payload);(O/'clouds-v42.bin').write_bytes(binary);sha=hashlib.sha256(native.read_bytes()).hexdigest()
spec={'revision':42,'nativeSha256':sha,'binarySha256':hashlib.sha256(binary).hexdigest(),'replaces':[q['name'].removesuffix('.001') for q in oldspec['clouds']],'clouds':export,'vertices':sum(q['vertices'] for q in rows),'triangles':sum(q['triangles'] for q in rows),'coordinates':'Native local mesh axes converted to Three.js with corresponding object matrices. Float32 positions, normals and linear RGB; UInt32 indices.','browserRuntimeVerified':False}
(O/'browser-clouds-v42.json').write_text(json.dumps(spec,indent=2),encoding='utf-8')
(O/'geometry-probes-v42.json').write_text(json.dumps(probes,indent=2),encoding='utf-8')
report={'revision':42,'nativeSha256':sha,'freshReopenVerified':True,'movieStatePreservedExactly':True,'nightScenePreservedExactly':True,'sharedNodeGroupsPreserved':True,'otherPosterGeometryAndColorsMaterialsCameraLightingPreserved':True,'waterRevision40Preserved':True,'posterObjectCount':len(s.objects),'lowerCloudCount':len(rows),'clouds':rows,'recoveredBankClosed':True,'continuousPartSpansFormerGap':geometry['continuousPartSpansFormerGap'],'browserGeometryExportedFromFreshNative':True,'browserRuntimeVerified':False,'oneToOneComplete':False}
(O/'verification-v42.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print('HORIZON_42_NATIVE_VERIFIED_EXPORTED',spec['triangles'],flush=True)
s.render.use_border=False;s.render.use_crop_to_border=False;s.render.resolution_x=708;s.render.resolution_y=1000;s.render.resolution_percentage=100;s.cycles.samples=28;s.cycles.use_denoising=True;s.render.filepath=str(O/'poster-front-v42.png');bpy.ops.render.render(write_still=True);print('HORIZON_42_FRONT_DONE',flush=True)
s.render.resolution_x=1416;s.render.resolution_y=2000;s.cycles.samples=24;s.render.use_border=True;s.render.use_crop_to_border=True;s.render.border_min_x=0;s.render.border_max_x=1;s.render.border_min_y=.37;s.render.border_max_y=.52;s.render.filepath=str(O/'horizon-detail-v42.png');bpy.ops.render.render(write_still=True);print('HORIZON_42_DETAIL_DONE',flush=True)
s.render.use_border=False;s.render.use_crop_to_border=False;s.camera.location=(-9,-12,4);s.camera.rotation_euler=(Vector((0,2,3))-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.lens=30;s.render.resolution_x=720;s.render.resolution_y=468;s.cycles.samples=24;s.render.filepath=str(O/'poster-oblique-v42.png');bpy.ops.render.render(write_still=True);print('HORIZON_42_OBLIQUE_DONE',flush=True)
