from pathlib import Path
import ast,hashlib,json,sys,bpy,bmesh,numpy as np
from mathutils import Vector
R=Path(__file__).parent;O=R/'poster-lower-clouds-v43';source=R/'poster-horizon-v42/Suzume_dual_scene_horizon_v42.blend';native=O/'Suzume_dual_scene_lower_clouds_v43.blend'
spec=json.loads((O/'lower-cloud-geometry-v43.json').read_text());a=np.load(O/'lower-cloud-geometry-v43.npz');changed={q['name'] for q in spec['clouds']}
assert hashlib.sha256(source.read_bytes()).hexdigest()==spec['sourceNativeSha256']
if '--final' not in sys.argv:
    tree=ast.parse((R/'verify_render_poster_v38.py').read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['tree_hash','movie_snapshot']],type_ignores=[]),'snapshot functions','exec'))
    tree=ast.parse((R/'verify_render_horizon_v42.py').read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='scene_snapshot'],type_ignores=[]),'scene snapshot','exec'))
    bpy.ops.wm.open_mainfile(filepath=str(source));before_movie=movie_snapshot();before_poster=scene_snapshot('Official poster courtyard v38');before_night=scene_snapshot('Night meadow through the door');before_groups={n.name:tree_hash(n) for n in bpy.data.node_groups}
    s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1);mat=s.objects['Restored central horizon cloud bank v42'].data.materials[0]
    for q in spec['clouds']:
        key=q['key'];m=bpy.data.meshes.new(q['name']+' mesh');m.from_pydata(a[key+'_local'].tolist(),[],a[key+'_faces'].tolist());m.update();m.polygons.foreach_set('use_smooth',np.ones(len(m.polygons),bool));m.materials.append(mat)
        rgb=a[key+'_rgb'];linear=np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4);attr=m.color_attributes.new(name='surface_color',type='FLOAT_COLOR',domain='POINT');attr.data.foreach_set('color',np.c_[linear,np.ones(len(rgb))].astype('f4').ravel())
        ob=bpy.data.objects.new(q['name'],m);s.collection.objects.link(ob);ob.location=a[key+'_origin'];ob['poster_cloud_revision']=43;ob['unobserved_depth_inferred']=True
    s['poster_lower_cloud_revision']=43;s.render.use_border=False;s.render.use_crop_to_border=False;s.render.resolution_x=708;s.render.resolution_y=1000;s.render.resolution_percentage=100;s.cycles.samples=28;s.cycles.use_denoising=True
    bpy.ops.wm.save_as_mainfile(filepath=str(native));sha=hashlib.sha256(native.read_bytes()).hexdigest();bpy.ops.wm.open_mainfile(filepath=str(native))
    assert before_movie==movie_snapshot();assert before_poster==scene_snapshot('Official poster courtyard v38');assert before_night==scene_snapshot('Night meadow through the door');assert before_groups=={n.name:tree_hash(n) for n in bpy.data.node_groups}
    s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1);bpy.context.view_layer.update();assert len(s.objects)==251
    P=np.array([[1,0,0,0],[0,0,1,0],[0,-1,0,0],[0,0,0,1]],float);payload=[];offset=0;exports=[];rows=[];probes={}
    for q in spec['clouds']:
        ob=s.objects[q['name']];m=ob.data;key=q['key'];v=np.empty((len(m.vertices),3),'f4');m.vertices.foreach_get('co',v.ravel());assert np.array_equal(v,a[key+'_local'])
        M=np.array(ob.matrix_world);world=v@M[:3,:3].T+M[:3,3];error=float(np.max(abs(world-a[key+'_world'])));assert error<3e-5
        m.calc_loop_triangles();faces=np.array([t.vertices[:] for t in m.loop_triangles],dtype='<u4');assert np.array_equal(faces,a[key+'_faces'])
        area=np.linalg.norm(np.cross(v[faces[:,1]]-v[faces[:,0]],v[faces[:,2]]-v[faces[:,0]]),axis=1)/2;assert np.all(area>0)
        bm=bmesh.new();bm.from_mesh(m);bad=sum(not edge.is_manifold for edge in bm.edges);volume=bm.calc_volume();bm.free();assert bad==0 and volume>0
        rgba=np.empty((len(v),4),'f4');m.color_attributes['surface_color'].data.foreach_get('color',rgba.ravel());rgb=a[key+'_rgb'];expected=np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4);assert np.max(abs(rgba[:,:3]-expected))<1e-7
        normals=np.empty((len(v),3),'f4');m.vertices.foreach_get('normal',normals.ravel());arrays=[(v[:,[0,2,1]]*[1,1,-1]).astype('<f4'),(normals[:,[0,2,1]]*[1,1,-1]).astype('<f4'),rgba[:,:3].astype('<f4'),faces]
        info={'name':q['name'],'vertices':len(v),'triangles':len(faces),'matrix':(P@M@P.T).T.ravel().tolist()}
        for name,data in zip(['positions','normals','colors','indices'],arrays):
            raw=data.tobytes();info[name]={'byteOffset':offset,'byteLength':len(raw)};payload.append(raw);offset+=len(raw)
        exports.append(info);probes[q['name']]=[{'index':int(j),'nativeWorld':a[key+'_world'][j].tolist()} for j in [0,len(v)//3,len(v)-1]]
        rows.append({'name':q['name'],'triangles':len(faces),'nonManifoldEdges':bad,'signedLocalVolume':volume,'minimumTriangleArea':float(area.min()),'maximumWorldVertexErrorMeters':error})
    binary=b''.join(payload);(O/'lower-clouds-v43.bin').write_bytes(binary)
    (O/'browser-clouds-v43.json').write_text(json.dumps({'revision':43,'nativeSha256':sha,'binarySha256':hashlib.sha256(binary).hexdigest(),'clouds':exports,'triangles':sum(q['triangles'] for q in rows),'browserRuntimeVerified':False},indent=2),encoding='utf-8')
    (O/'geometry-probes-v43.json').write_text(json.dumps(probes,indent=2),encoding='utf-8')
    report={'revision':43,'nativeSha256':sha,'sourceNativeSha256':spec['sourceNativeSha256'],'freshReopenVerified':True,'movieStatePreservedExactly':True,'nightScenePreservedExactly':True,'allExistingPosterObjectsAndMaterialsPreserved':True,'sharedNodeGroupsPreserved':True,'addedClosedClouds':rows,'posterObjectCount':len(s.objects),'browserRuntimeVerified':False,'oneToOneComplete':False}
    (O/'verification-v43.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print('LOWER_CLOUD_43_NATIVE_VERIFIED',sha,flush=True)
    if '--side-trial' in sys.argv:
        s.render.use_border=False;s.render.use_crop_to_border=False;s.camera.location=(-9,-12,4);s.camera.rotation_euler=(Vector((0,2,3))-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.lens=30;s.render.resolution_x=720;s.render.resolution_y=468;s.cycles.samples=24;s.render.filepath=str(O/'side-trial-v43.png');bpy.ops.render.render(write_still=True);print('LOWER_CLOUD_43_SIDE_TRIAL_DONE',flush=True)
    else:
        s.cycles.samples=24;s.render.use_border=True;s.render.use_crop_to_border=True;s.render.border_min_x=0;s.render.border_max_x=1;s.render.border_min_y=.36;s.render.border_max_y=.50;s.render.filepath=str(O/'lower-sky-trial-v43.png');bpy.ops.render.render(write_still=True);print('LOWER_CLOUD_43_TRIAL_DONE',flush=True)
else:
    report=json.loads((O/'verification-v43.json').read_text());assert hashlib.sha256(native.read_bytes()).hexdigest()==report['nativeSha256'];bpy.ops.wm.open_mainfile(filepath=str(native));s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1)
    s.render.use_border=False;s.render.use_crop_to_border=False;s.render.resolution_x=708;s.render.resolution_y=1000;s.render.resolution_percentage=100;s.cycles.samples=28;s.cycles.use_denoising=True;s.render.filepath=str(O/'poster-front-v43.png');bpy.ops.render.render(write_still=True);print('LOWER_CLOUD_43_FRONT_DONE',flush=True)
    s.render.resolution_x=1416;s.render.resolution_y=2000;s.cycles.samples=24;s.render.use_border=True;s.render.use_crop_to_border=True;s.render.border_min_x=0;s.render.border_max_x=1;s.render.border_min_y=.36;s.render.border_max_y=.50;s.render.filepath=str(O/'lower-sky-detail-v43.png');bpy.ops.render.render(write_still=True);print('LOWER_CLOUD_43_DETAIL_DONE',flush=True)
    if '--front-detail-only' not in sys.argv:
        s.render.use_border=False;s.render.use_crop_to_border=False;s.camera.location=(-9,-12,4);s.camera.rotation_euler=(Vector((0,2,3))-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.lens=30;s.render.resolution_x=720;s.render.resolution_y=468;s.cycles.samples=24;s.render.filepath=str(O/'poster-oblique-v43.png');bpy.ops.render.render(write_still=True);print('LOWER_CLOUD_43_OBLIQUE_DONE',flush=True)
