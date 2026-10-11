from pathlib import Path
import ast,json,hashlib,sys
import bpy,bmesh,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).parent;O=R/'poster-low-rails-v53';source=R/'poster-ground-v52/Suzume_dual_scene_ground_v52.blend';native=O/'Suzume_dual_scene_low_rails_v53.blend';D=json.loads((O/'low-rails-geometry-v53.json').read_text());plans=np.load(O/'low-rails-removal-v53.npz');old=[q for q in D['sourceObjects'] if q['key'] in plans and plans[q['key']].any()];changed={q['name'] for q in old+D['members']};sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,data):(O/name).write_text(json.dumps(data,indent=2),encoding='utf-8')
def images():return {im.name:hashlib.sha256(im.packed_file.data).hexdigest() for im in bpy.data.images if im.packed_file}

if not any(flag in sys.argv for flag in ['--final','--close','--detail']):
 assert sha(source)==D['sourceNativeSha256']
 for filename,names in [('verify_render_poster_v38.py',['tree_hash','movie_snapshot']),('verify_render_horizon_v42.py',['scene_snapshot'])]:
  tree=ast.parse((R/filename).read_text(encoding='utf-8'));exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'snapshot helpers','exec'))
 bpy.ops.wm.open_mainfile(filepath=str(source));movie_before=movie_snapshot();poster_before=scene_snapshot('Official poster courtyard v38');night_before=scene_snapshot('Night meadow through the door');groups_before={g.name:tree_hash(g) for g in bpy.data.node_groups};images_before=images();s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1);bpy.context.view_layer.update();retained={};changes=[];baseline=np.load(R/D['sourceGeometryFile'])
 for row in old:
  ob=s.objects[row['name']];m=ob.data;plan=plans[row['key']];v=np.array([p.co[:] for p in m.vertices]);M=np.array(ob.matrix_world);world=v@M[:3,:3].T+M[:3,3];assert np.max(abs(world-baseline[row['key']+'_vertices']))<2e-6;assert all(len(p.vertices)==3 for p in m.polygons);assert len(m.materials)==1 and len(m.uv_layers)==1 and len(m.color_attributes)==0;assert set(np.unique(plan)).issubset({0,1})
  ix=np.array([p.vertices[:] for p in m.polygons]);loops=np.array([p.loop_indices[:] for p in m.polygons]);norm=np.empty((len(m.corner_normals),3),'f4');m.corner_normals.foreach_get('vector',norm.ravel());uv=np.empty((len(m.loops),2),'f4');m.uv_layers.active.data.foreach_get('uv',uv.ravel());keep=plan==0;local=v[ix[keep].ravel()];normal=norm[loops[keep].ravel()];uvkeep=uv[loops[keep].ravel()]
  new=bpy.data.meshes.new(m.name+' unmatched bricks removed v53');new.from_pydata(local.tolist(),[],np.arange(len(local)).reshape(-1,3).tolist());new.update();new.materials.append(m.materials[0]);layer=new.uv_layers.new(name=m.uv_layers.active.name);layer.data.foreach_set('uv',uvkeep.ravel());new.normals_split_custom_set(normal.tolist());ob.data=new;retained[ob.name]={'positions':hashlib.sha256(local.astype('f4').tobytes()).hexdigest(),'uv':hashlib.sha256(uvkeep.tobytes()).hexdigest()};changes.append({'key':row['key'],'name':ob.name,'removedTriangles':int((plan==1).sum()),'finalTriangles':len(local)//3})
 for q in D['newMaterials']:
  mat=bpy.data.materials[q['clone']].copy();mat.name=q['name']
  for n in mat.node_tree.nodes:
   if n.type=='ATTRIBUTE':n.attribute_name='surface_color'
   if n.type=='BSDF_PRINCIPLED':n.inputs['Roughness'].default_value=q['roughness'];n.inputs['Metallic'].default_value=q['metallic']
 materials=[bpy.data.materials[name] for name in D['materials']];col=bpy.data.collections.new('Poster low frame and pipe supports v53');s.collection.children.link(col)
 for q in D['members']:
  m=bpy.data.meshes.new(q['name']+' closed solid');m.from_pydata(q['verticesNative'],[],q['triangles']);m.update()
  for mat in materials:m.materials.append(mat)
  m.polygons.foreach_set('material_index',q['materialIndices']);layer=m.uv_layers.new(name='Fixture world UV');uv=np.array(q['verticesNative'])[:,:2]*.5;ix=np.array([p.vertices[:] for p in m.polygons]).ravel();layer.data.foreach_set('uv',uv[ix].astype('f4').ravel());attr=m.color_attributes.new(name='surface_color',type='FLOAT_COLOR',domain='POINT');attr.data.foreach_set('color',np.array(q['colors'],dtype='f4').ravel());ob=bpy.data.objects.new(q['name'],m);col.objects.link(ob);ob['low_fixture_revision']=53;ob['unobserved_detail_inferred']=True
 s['low_fixture_revision']=53;s.render.use_border=False;s.render.use_crop_to_border=False;s.render.resolution_x=708;s.render.resolution_y=1000;s.render.resolution_percentage=100;s.cycles.samples=28;s.cycles.use_denoising=True;bpy.ops.wm.save_as_mainfile(filepath=str(native));native_sha=sha(native);bpy.ops.wm.open_mainfile(filepath=str(native));assert movie_before==movie_snapshot();assert night_before==scene_snapshot('Night meadow through the door');after=scene_snapshot('Official poster courtyard v38')
 for name in D['materials']:after['materials'].pop(name)
 assert poster_before==after;assert groups_before=={g.name:tree_hash(g) for g in bpy.data.node_groups};assert images_before==images();s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1);bpy.context.view_layer.update();closed=[]
 for name,want in retained.items():
  m=s.objects[name].data;v=np.array([p.co[:] for p in m.vertices],dtype='f4');uv=np.empty((len(m.loops),2),'f4');m.uv_layers.active.data.foreach_get('uv',uv.ravel());assert hashlib.sha256(v.tobytes()).hexdigest()==want['positions'];assert hashlib.sha256(uv.tobytes()).hexdigest()==want['uv']
 for q in D['members']:
  m=s.objects[q['name']].data;v=np.array([p.co[:] for p in m.vertices]);error=float(np.max(abs(v-np.array(q['verticesNative']))));assert error<2e-6;bm=bmesh.new();bm.from_mesh(m);bad=sum(not e.is_manifold for e in bm.edges);volume=bm.calc_volume();bm.free();assert bad==0 and volume>0,(q['name'],bad,volume);a=np.empty((len(v),4),'f4');m.color_attributes['surface_color'].data.foreach_get('color',a.ravel());assert np.array_equal(a,np.array(q['colors'],dtype='f4'));closed.append({'name':q['name'],'kind':q['kind'],'triangles':len(m.polygons),'nonManifoldEdges':bad,'signedVolume':volume,'maximumVertexErrorMeters':error,'vertexColorsPreserved':True})
 G=json.loads((R/'poster-ground-v52/ground-geometry-v52.json').read_text());gv=[];gf=[]
 for q in G['members']:
  if q['kind'] not in ['shoreline','root soil','rock','fragment','stair foundation','chipped support']:continue
  m=s.objects[q['name']].data;offset=len(gv);gv.extend([v.co[:] for v in m.vertices]);gf.extend([[i+offset for i in p.vertices] for p in m.polygons])
 gt=BVHTree.FromPolygons(gv,gf,all_triangles=True);contacts=[]
 for kind,points in [('frame',D['frameGroundContacts']),('pipe',D['pipeGroundContacts'])]:
  for p in points:
   hit=gt.ray_cast(Vector(p)+Vector((0,0,.3)),Vector((0,0,-1)),1.0);assert hit[0] is not None,(kind,p);gap=p[2]-hit[0].z;assert abs(gap-.001)<2e-5,(kind,p,gap);contacts.append({'kind':kind,'point':p,'groundZ':hit[0].z,'gapMeters':gap})
 pipe=s.objects['Poster low corroded hollow pipe v51'];pt=BVHTree.FromPolygons([pipe.matrix_world@v.co for v in pipe.data.vertices],[p.vertices[:] for p in pipe.data.polygons],all_triangles=True);pipe_contacts=[]
 for q in D['members']:
  if q['kind']!='pipe strap':continue
  p=Vector(q['innerSurfaceNative']);out=Vector(q['outwardNative']);hit=pt.ray_cast(p+out*.05,-out,.1);assert hit[0] is not None;gap=(p-hit[0]).dot(out);assert -.002<gap<.00002,(q['name'],gap);pipe_contacts.append({'name':q['name'],'gapMeters':gap,'pipeSurfaceNative':list(hit[0])})
 C=np.array(D['camera']['position']);rot=np.array(D['camera']['rotation']);f=D['camera']['focalPixels'];anchor_error=[]
 for q in D['observedCenterlines']:
  p=(np.array(q['centerlineNative'])-C)@rot;uv=np.c_[354+f*p[:,0]/-p[:,2],500-f*p[:,1]/-p[:,2]];error=float(np.max(abs(uv-np.array(q['referencePixels']))));assert error<1e-4;anchor_error.append({'name':q['name'],'maximumProjectionErrorPixels708':error})
 report={'revision':53,'nativeSha256':native_sha,'sourceNativeSha256':D['sourceNativeSha256'],'freshReopenVerified':True,'movieStatePreservedExactly':True,'nightScenePreservedExactly':True,'otherPosterObjectsMaterialsCameraLightingPreserved':True,'allExistingVegetationPreservedExactly':True,'sharedNodeGroupsPreserved':True,'allPackedImageBytesPreserved':True,'packedImageCount':len(images_before),'unchangedOriginalFacePositionsAndUVsPreserved':True,'changedOriginalMeshes':changes,'addedSolids':closed,'groundContacts':contacts,'pipeStrapContacts':pipe_contacts,'centerlineProjectionChecks':anchor_error,'hiddenDepthAndFixtureIdentityInferred':True,'browserRuntimeVerified':False,'oneToOneComplete':False};write('verification-v53.json',report);print('LOW_RAILS_53_NATIVE_VERIFIED',native_sha,flush=True)
else:
 report=json.loads((O/'verification-v53.json').read_text());assert sha(native)==report['nativeSha256'];bpy.ops.wm.open_mainfile(filepath=str(native));s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1);s.render.use_border=False;s.render.use_crop_to_border=False;s.render.resolution_percentage=100;s.cycles.use_denoising=True

if '--close' in sys.argv:
 s.camera.location=(-4.5,17,3.8);s.camera.rotation_euler=(Vector((-10.8,21.1,2.35))-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.lens=45;s.render.resolution_x=900;s.render.resolution_y=500;s.cycles.samples=24;s.render.filepath=str(O/'low-rails-oblique-detail-v53.png');bpy.ops.render.render(write_still=True);print('LOW_RAILS_53_CLOSE_DONE',flush=True)
elif '--final' in sys.argv:
 s.render.resolution_x=708;s.render.resolution_y=1000;s.cycles.samples=28;s.render.filepath=str(O/'poster-front-v53.png');bpy.ops.render.render(write_still=True);print('LOW_RAILS_53_FRONT_DONE',flush=True)
 s.camera.location=(-9,-12,4);s.camera.rotation_euler=(Vector((0,2,3))-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.lens=30;s.render.resolution_x=720;s.render.resolution_y=468;s.cycles.samples=24;s.render.filepath=str(O/'poster-oblique-v53.png');bpy.ops.render.render(write_still=True);print('LOW_RAILS_53_OBLIQUE_DONE',flush=True)
else:
 s.render.resolution_x=2124;s.render.resolution_y=3000;s.cycles.samples=28;s.render.use_border=True;s.render.use_crop_to_border=True;s.render.border_min_x=0;s.render.border_max_x=305/708;s.render.border_min_y=.275;s.render.border_max_y=.35;s.render.filepath=str(O/'low-rails-detail-v53.png');bpy.ops.render.render(write_still=True);print('LOW_RAILS_53_DETAIL_DONE',flush=True)
