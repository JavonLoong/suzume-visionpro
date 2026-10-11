from pathlib import Path
import bpy,json,numpy as np,hashlib,sys
R=Path(__file__).parent;O=R/'poster-horizon-v42';source=R/'poster-clouds-v41/Suzume_dual_scene_clouds_v41.blend';q=json.loads((O/'horizon-geometry-v42.json').read_text());a=np.load(O/'horizon-geometry-v42.npz')
assert hashlib.sha256(source.read_bytes()).hexdigest()==q['sourceNativeSha256']
bpy.ops.wm.open_mainfile(filepath=str(source));s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1);old=[s.objects[n] for n in q['replaces']];assert all(set(o.users_scene)=={s} for o in old);mat=old[0].data.materials[0];removed=[{'name':o.name,'vertices':len(o.data.vertices),'triangles':len(o.data.polygons)} for o in old]
m=bpy.data.meshes.new('Continuous restored horizon mesh v42');m.from_pydata(a['local'].tolist(),[],a['faces'].tolist());m.update();m.polygons.foreach_set('use_smooth',np.ones(len(m.polygons),bool));m.materials.append(mat);attr=m.color_attributes.new(name='surface_color',type='FLOAT_COLOR',domain='POINT');rgb=a['rgb'];linear=np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4);attr.data.foreach_set('color',np.c_[linear,np.ones(len(rgb))].astype(np.float32).ravel())
ob=bpy.data.objects.new(q['name'],m);s.collection.objects.link(ob);ob.location=a['origin'];ob['poster_cloud_revision']=42;ob['depth_is_inferred']=True
for o in old:
    data=o.data;bpy.data.objects.remove(o,do_unlink=True)
    if data.users==0:bpy.data.meshes.remove(data)
s['poster_horizon_revision']=42;s.render.resolution_x=708;s.render.resolution_y=1000;s.render.resolution_percentage=100;s.render.use_border=False;s.render.use_crop_to_border=False;s.cycles.samples=28;s.cycles.use_denoising=True
native=O/'Suzume_dual_scene_horizon_v42.blend';bpy.ops.wm.save_as_mainfile(filepath=str(native));report={'revision':42,'sourceNativeSha256':q['sourceNativeSha256'],'nativeSha256':hashlib.sha256(native.read_bytes()).hexdigest(),'removedClouds':removed,'newCloud':q['name'],'newVertices':len(m.vertices),'newTriangles':len(m.polygons),'oneToOneComplete':False};(O/'integration-v42.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print('HORIZON_42_NATIVE_SAVED',report['nativeSha256'],flush=True)
if '--trial' in sys.argv:
    s.cycles.samples=24;s.render.use_border=True;s.render.use_crop_to_border=True;s.render.border_min_x=0;s.render.border_max_x=1;s.render.border_min_y=.34;s.render.border_max_y=.52;s.render.filepath=str(O/'horizon-trial-v42.png');bpy.ops.render.render(write_still=True);print('HORIZON_42_TRIAL_DONE',flush=True)
