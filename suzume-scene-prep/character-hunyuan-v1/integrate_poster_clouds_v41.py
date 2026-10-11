from pathlib import Path
import bpy,json,numpy as np,hashlib,sys
R=Path(__file__).parent;O=R/'poster-clouds-v41';source=R/'poster-water-v40/Suzume_dual_scene_water_v40.blend'
q=json.loads((O/'cloud-geometry-v41.json').read_text());assert hashlib.sha256(source.read_bytes()).hexdigest()==q['sourceNativeSha256'];data=np.load(O/'cloud-geometry-v41.npz')
bpy.ops.wm.open_mainfile(filepath=str(source));s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1);rows=[]
for rec in q['clouds']:
    ob=s.objects[rec['name']];old=ob.data;materials=list(old.materials);assert len(materials)==1;world=data[rec['key']+'_world'];faces=data[rec['key']+'_faces'];rgb=data[rec['key']+'_rgb']
    M=np.array(ob.matrix_world);local=(world-M[:3,3])@np.linalg.inv(M[:3,:3]).T;mesh=bpy.data.meshes.new('Dense lower cloud '+str(rec['index'])+' v41');mesh.from_pydata(local.tolist(),[],faces.tolist());mesh.update()
    mesh.polygons.foreach_set('use_smooth',np.ones(len(mesh.polygons),bool));mesh.materials.append(materials[0]);attr=mesh.color_attributes.new(name='surface_color',type='FLOAT_COLOR',domain='POINT');linear=np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4);colors=np.c_[linear,np.ones(len(rgb))].astype(np.float32);attr.data.foreach_set('color',colors.ravel())
    ob.data=mesh;ob['poster_cloud_revision']=41;ob['cloud_depth_is_inferred']=True;rows.append({'name':ob.name,'oldVertices':len(old.vertices),'oldTriangles':len(old.polygons),'newVertices':len(mesh.vertices),'newTriangles':len(mesh.polygons)})
    if old.users==0:bpy.data.meshes.remove(old)
s['poster_cloud_revision']=41;s.render.resolution_x=708;s.render.resolution_y=1000;s.render.resolution_percentage=100;s.render.use_border=False;s.render.use_crop_to_border=False;s.cycles.samples=28;s.cycles.use_denoising=True
native=O/'Suzume_dual_scene_clouds_v41.blend';bpy.ops.wm.save_as_mainfile(filepath=str(native));report={'revision':41,'nativeSha256':hashlib.sha256(native.read_bytes()).hexdigest(),'sourceNativeSha256':q['sourceNativeSha256'],'changedClouds':rows,'newCloudTriangles':sum(x['newTriangles'] for x in rows),'oldCloudTriangles':sum(x['oldTriangles'] for x in rows),'oneToOneComplete':False};(O/'integration-v41.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print('CLOUD_41_NATIVE_SAVED',report['newCloudTriangles'],flush=True)
if '--trial' in sys.argv:
    s.cycles.samples=24;s.render.use_border=True;s.render.use_crop_to_border=True;s.render.border_min_x=0;s.render.border_max_x=1;s.render.border_min_y=.42;s.render.border_max_y=.67;s.render.filepath=str(O/'cloud-detail-trial-v41.png');bpy.ops.render.render(write_still=True);print('CLOUD_41_TRIAL_DONE',flush=True)
