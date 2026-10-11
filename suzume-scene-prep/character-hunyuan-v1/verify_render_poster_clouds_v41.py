from pathlib import Path
import bpy,bmesh,json,hashlib,ast,numpy as np
from mathutils import Vector
R=Path(__file__).parent;O=R/'poster-clouds-v41';native=O/'Suzume_dual_scene_clouds_v41.blend';geometry=json.loads((O/'cloud-geometry-v41.json').read_text());source=np.load(O/'cloud-geometry-v41.npz');changed={q['name'] for q in geometry['clouds']}
tree=ast.parse((R/'verify_render_poster_v38.py').read_text());funcs=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['tree_hash','movie_snapshot']];exec(compile(ast.Module(body=funcs,type_ignores=[]),'snapshot helpers','exec'))
def poster_snapshot():
    s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1);bpy.context.view_layer.update();objects={};materials={}
    for o in s.objects:
        rec={'matrix':np.array(o.matrix_world).tolist(),'type':o.type,'render':o.hide_render,'modifiers':[[m.name,m.type,m.show_render,m.show_viewport] for m in o.modifiers]}
        if o.type=='MESH':
            rec['materials']=[m.name if m else None for m in o.data.materials]
            for m in o.data.materials:
                if m:materials[m.name]=tree_hash(m.node_tree)
            if o.name not in changed:
                v=np.empty(len(o.data.vertices)*3,np.float32);o.data.vertices.foreach_get('co',v);ix=np.empty(len(o.data.loops),np.int32);o.data.loops.foreach_get('vertex_index',ix);rec['mesh']=hashlib.sha256(v.tobytes()+ix.tobytes()).hexdigest()
                for attr in o.data.color_attributes:
                    co=np.empty(len(attr.data)*4,np.float32);attr.data.foreach_get('color',co);rec['color_'+attr.name]=hashlib.sha256(co.tobytes()).hexdigest()
        objects[o.name]=rec
    return {'objects':objects,'materials':materials,'world':tree_hash(s.world.node_tree),'cameraLens':s.camera.data.lens,'colors':[s.view_settings.view_transform,s.view_settings.look,s.view_settings.exposure]}
bpy.ops.wm.open_mainfile(filepath=str(R/'poster-water-v40/Suzume_dual_scene_water_v40.blend'));movie_before=movie_snapshot();poster_before=poster_snapshot()
bpy.ops.wm.open_mainfile(filepath=str(native));assert movie_before==movie_snapshot(),'Movie scene changed';assert poster_before==poster_snapshot(),'Non-cloud poster state changed'
s=bpy.data.scenes['Official poster courtyard v38'];rows=[];payload=[];offset=0;P=np.array([[1,0,0,0],[0,0,1,0],[0,-1,0,0],[0,0,0,1]],float);export=[]
for q in geometry['clouds']:
    o=s.objects[q['name']];m=o.data;v=np.empty((len(m.vertices),3),np.float32);m.vertices.foreach_get('co',v.ravel());M=np.array(o.matrix_world);world=v@M[:3,:3].T+M[:3,3];difference=float(np.max(abs(world-source[q['key']+'_world'])));assert difference<3e-5,(o.name,difference)
    m.calc_loop_triangles();faces=np.array([t.vertices[:] for t in m.loop_triangles],dtype='<u4');assert np.array_equal(faces,source[q['key']+'_faces'])
    area=np.linalg.norm(np.cross(v[faces[:,1]]-v[faces[:,0]],v[faces[:,2]]-v[faces[:,0]]),axis=1)/2;assert np.all(area>0),(o.name,int((area==0).sum()))
    bm=bmesh.new();bm.from_mesh(m);bad=sum(not e.is_manifold for e in bm.edges);volume=bm.calc_volume();bm.free();assert bad==0 and volume>0,(o.name,bad,volume)
    rgba=np.empty((len(v),4),np.float32);m.color_attributes['surface_color'].data.foreach_get('color',rgba.ravel());rgb=source[q['key']+'_rgb'];expected=np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4);assert np.max(abs(rgba[:,:3]-expected))<1e-7
    normal=np.empty((len(v),3),np.float32);m.vertices.foreach_get('normal',normal.ravel())
    arrays=[(v[:,[0,2,1]]*[1,1,-1]).astype('<f4'),(normal[:,[0,2,1]]*[1,1,-1]).astype('<f4'),rgba[:,:3].astype('<f4'),faces]
    info={'name':q['name'].removesuffix('.001'),'index':q['index'],'vertices':len(v),'triangles':len(faces),'matrix':(P@M@P.T).T.ravel().tolist()}
    for name,a in zip(['positions','normals','colors','indices'],arrays):
        raw=a.tobytes();info[name]={'byteOffset':offset,'byteLength':len(raw)};payload.append(raw);offset+=len(raw)
    export.append(info);rows.append({'name':o.name,'vertices':len(v),'triangles':len(faces),'nonManifoldEdges':bad,'signedLocalVolume':volume,'minimumLocalTriangleArea':float(area.min()),'maxWorldVertexErrorMeters':difference,'pigmentsMatchSource':True})
binary=b''.join(payload);(O/'clouds-v41.bin').write_bytes(binary);sha=hashlib.sha256(native.read_bytes()).hexdigest()
spec={'revision':41,'nativeSha256':sha,'binarySha256':hashlib.sha256(binary).hexdigest(),'clouds':export,'vertices':sum(q['vertices'] for q in rows),'triangles':sum(q['triangles'] for q in rows),'coordinates':'Native local mesh axes converted to Three.js, with explicit corresponding object matrices. Float32 positions, normals and linear RGB, UInt32 indices.','browserRuntimeVerified':False};(O/'browser-clouds-v41.json').write_text(json.dumps(spec,indent=2),encoding='utf-8')
report={'revision':41,'nativeSha256':sha,'freshReopenVerified':True,'movieStatePreservedExactly':True,'otherPosterGeometryAndColorsMaterialsCameraLightingPreserved':True,'waterRevision40Preserved':True,'changedCloudCount':len(rows),'clouds':rows,'browserGeometryExportedFromFreshNative':True,'browserRuntimeVerified':False,'oneToOneComplete':False};(O/'verification-v41.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print('CLOUD_41_NATIVE_VERIFIED_EXPORTED',spec['triangles'],flush=True)
s.render.use_border=False;s.render.use_crop_to_border=False;s.render.resolution_x=708;s.render.resolution_y=1000;s.render.resolution_percentage=100;s.cycles.samples=28;s.cycles.use_denoising=True;s.render.filepath=str(O/'poster-front-v41.png');bpy.ops.render.render(write_still=True);print('CLOUD_41_FRONT_DONE',flush=True)
s.render.resolution_x=1416;s.render.resolution_y=2000;s.cycles.samples=24;s.render.use_border=True;s.render.use_crop_to_border=True;s.render.border_min_x=0;s.render.border_max_x=1;s.render.border_min_y=.42;s.render.border_max_y=.67;s.render.filepath=str(O/'cloud-detail-v41.png');bpy.ops.render.render(write_still=True);print('CLOUD_41_DETAIL_DONE',flush=True)
s.render.use_border=False;s.render.use_crop_to_border=False;s.camera.location=(-9,-12,4);s.camera.rotation_euler=(Vector((0,2,3))-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.lens=30;s.render.resolution_x=720;s.render.resolution_y=468;s.cycles.samples=24;s.render.filepath=str(O/'poster-oblique-v41.png');bpy.ops.render.render(write_still=True);print('CLOUD_41_OBLIQUE_DONE',flush=True)
