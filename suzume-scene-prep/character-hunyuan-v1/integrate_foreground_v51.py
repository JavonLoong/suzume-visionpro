from pathlib import Path
import ast,json,hashlib,sys
import bpy,bmesh,numpy as np
from mathutils import Vector

R=Path(__file__).parent;O=R/'poster-foreground-v51';source=R/'poster-lower-facade-v50/Suzume_dual_scene_lower_facade_v50.blend';native=O/'Suzume_dual_scene_foreground_v51.blend'
D=json.loads((O/'foreground-geometry-v51.json').read_text(encoding='utf-8'));plans=np.load(O/'prop-removal-v51.npz');old=[q for q in D['sourceObjects'] if q['key'] in plans and plans[q['key']].any()]
ivyname='Individual three-dimensional ivy leaves.001';changed={q['name'] for q in old+D['members']}|{ivyname};C=np.array(D['camera']['position']);rot=np.array(D['camera']['rotation']);f=D['camera']['focalPixels']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,data): (O/name).write_text(json.dumps(data,indent=2),encoding='utf-8')
def projected_uv(v):
 q=(np.asarray(v)-C)@rot;px=1000+f*2.824*q[...,0]/-q[...,2];py=1412-f*2.824*q[...,1]/-q[...,2];return np.stack((px/2000,1-(py-1410)/600),axis=-1)
def attributes(m):
 out={}
 for name,width,field in [('instance_color',4,'color'),('instance_rotation',3,'vector'),('instance_scale',3,'vector')]:
  a=np.empty((len(m.vertices),width),'f4');m.attributes[name].data.foreach_get(field,a.ravel());out[name]=a
 return out
def images():return {im.name:hashlib.sha256(im.packed_file.data).hexdigest() for im in bpy.data.images if im.packed_file}

if '--final' not in sys.argv and '--close' not in sys.argv:
 assert sha(source)==D['sourceNativeSha256']
 for filename,names in [('verify_render_poster_v38.py',['tree_hash','movie_snapshot']),('verify_render_horizon_v42.py',['scene_snapshot'])]:
  tree=ast.parse((R/filename).read_text(encoding='utf-8'));exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'snapshot helpers','exec'))
 bpy.ops.wm.open_mainfile(filepath=str(source));movie_before=movie_snapshot();poster_before=scene_snapshot('Official poster courtyard v38');night_before=scene_snapshot('Night meadow through the door');groups_before={g.name:tree_hash(g) for g in bpy.data.node_groups};images_before=images()
 s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1);bpy.context.view_layer.update();retained={};changes=[];baseline=np.load(R/D['sourceGeometryFile'])
 for row in old:
  ob=s.objects[row['name']];m=ob.data;plan=plans[row['key']];v=np.array([p.co[:] for p in m.vertices]);M=np.array(ob.matrix_world);world=v@M[:3,:3].T+M[:3,3];assert np.max(abs(world-baseline[row['key']+'_vertices']))<2e-6;assert all(len(p.vertices)==3 for p in m.polygons);assert len(m.materials)==1 and len(m.uv_layers)==1 and len(m.color_attributes)==0;assert set(np.unique(plan)).issubset({0,1})
  ix=np.array([p.vertices[:] for p in m.polygons]);loops=np.array([p.loop_indices[:] for p in m.polygons]);norm=np.empty((len(m.corner_normals),3),'f4');m.corner_normals.foreach_get('vector',norm.ravel());uv=np.empty((len(m.loops),2),'f4');m.uv_layers.active.data.foreach_get('uv',uv.ravel());keep=plan==0
  local=v[ix[keep].ravel()];normal=norm[loops[keep].ravel()];uvkeep=uv[loops[keep].ravel()]
  new=bpy.data.meshes.new(m.name+' props removed v51');new.from_pydata(local.tolist(),[],np.arange(len(local)).reshape(-1,3).tolist());new.update();new.materials.append(m.materials[0]);layer=new.uv_layers.new(name=m.uv_layers.active.name);layer.data.foreach_set('uv',uvkeep.ravel());new.normals_split_custom_set(normal.tolist());ob.data=new
  retained[ob.name]={'positions':hashlib.sha256(local.astype('f4').tobytes()).hexdigest(),'uv':hashlib.sha256(uvkeep.tobytes()).hexdigest()};changes.append({'key':row['key'],'name':ob.name,'removedTriangles':int((plan==1).sum()),'finalTriangles':len(local)//3})
 removal=json.loads((O/'ivy-removal-v51.json').read_text());ivysrc=np.load(O/'ivy-source-v51.npz');ob=s.objects[ivyname];m=ob.data;points=np.array([v.co[:] for v in m.vertices],dtype='f4');attrs=attributes(m);assert np.array_equal(points,ivysrc['points']);assert np.allclose(np.array(ob.matrix_world),ivysrc['matrix'],rtol=0,atol=1e-8)
 for name,a in attrs.items():assert np.array_equal(a,ivysrc[name]),name
 keep=np.ones(len(points),bool);keep[removal['removedIndices']]=False;assert keep.sum()==removal['remainingCount'];new=bpy.data.meshes.new(m.name+' filtered v51');new.from_pydata(points[keep].tolist(),[],[]);new.update()
 for mat in m.materials:new.materials.append(mat)
 for name,a in attrs.items():
  field='color' if a.shape[1]==4 else 'vector';attr=new.attributes.new(name=name,type='FLOAT_COLOR' if field=='color' else 'FLOAT_VECTOR',domain='POINT');attr.data.foreach_set(field,a[keep].ravel())
 ob.data=new
 leafmat=bpy.data.materials[D['newMaterial']['clone']].copy();leafmat.name=D['newMaterial']['name']
 for n in leafmat.node_tree.nodes:
  if n.type=='ATTRIBUTE':n.attribute_name='surface_color'
  if n.type=='BSDF_PRINCIPLED':n.inputs['Roughness'].default_value=.96
 materials=[bpy.data.materials[name] for name in D['materials']];col=bpy.data.collections.new('Poster foreground plants and props v51');s.collection.children.link(col)
 for q in D['members']:
  m=bpy.data.meshes.new(q['name']+' closed solid');m.from_pydata(q['verticesNative'],[],q['triangles']);m.update()
  for mat in materials:m.materials.append(mat)
  m.polygons.foreach_set('material_index',q['materialIndices']);uv=projected_uv(np.array(q['verticesNative']));ix=np.array([p.vertices[:] for p in m.polygons]).ravel();layer=m.uv_layers.new(name='Reference surface UV');layer.data.foreach_set('uv',uv[ix].astype('f4').ravel());attr=m.color_attributes.new(name='surface_color',type='FLOAT_COLOR',domain='POINT');attr.data.foreach_set('color',np.array(q['colors'],dtype='f4').ravel());ob=bpy.data.objects.new(q['name'],m);col.objects.link(ob);ob['foreground_revision']=51;ob['unobserved_detail_inferred']=True
 s['foreground_revision']=51;s.render.use_border=False;s.render.use_crop_to_border=False;s.render.resolution_x=708;s.render.resolution_y=1000;s.render.resolution_percentage=100;s.cycles.samples=28;s.cycles.use_denoising=True
 bpy.ops.wm.save_as_mainfile(filepath=str(native));native_sha=sha(native);bpy.ops.wm.open_mainfile(filepath=str(native));assert movie_before==movie_snapshot();assert night_before==scene_snapshot('Night meadow through the door');after=scene_snapshot('Official poster courtyard v38');after['materials'].pop(D['newMaterial']['name']);assert poster_before==after;assert groups_before=={g.name:tree_hash(g) for g in bpy.data.node_groups};assert images_before==images()
 s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1);bpy.context.view_layer.update();closed=[]
 for name,want in retained.items():
  m=s.objects[name].data;v=np.array([p.co[:] for p in m.vertices],dtype='f4');uv=np.empty((len(m.loops),2),'f4');m.uv_layers.active.data.foreach_get('uv',uv.ravel());assert hashlib.sha256(v.tobytes()).hexdigest()==want['positions'];assert hashlib.sha256(uv.tobytes()).hexdigest()==want['uv']
 for q in D['members']:
  m=s.objects[q['name']].data;v=np.array([p.co[:] for p in m.vertices]);error=float(np.max(abs(v-np.array(q['verticesNative']))));assert error<2e-6;bm=bmesh.new();bm.from_mesh(m);bad=sum(not e.is_manifold for e in bm.edges);volume=bm.calc_volume();bm.free();assert bad==0 and volume>0,(q['name'],bad,volume);a=np.empty((len(v),4),'f4');m.color_attributes['surface_color'].data.foreach_get('color',a.ravel());assert np.array_equal(a,np.array(q['colors'],dtype='f4'));closed.append({'name':q['name'],'kind':q['kind'],'triangles':len(m.polygons),'nonManifoldEdges':bad,'signedVolume':volume,'maximumVertexErrorMeters':error,'vertexColorsPreserved':True})
 ob=s.objects[ivyname];m=ob.data;assert np.array_equal(np.array([v.co[:] for v in m.vertices],dtype='f4'),points[keep])
 for name,a in attributes(m).items():assert np.array_equal(a,attrs[name][keep])
 evaluated=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());em=evaluated.to_mesh();ivy_vertices=len(em.vertices);ivy_faces=len(em.polygons);assert ivy_vertices==int(keep.sum())*10;assert ivy_faces==int(keep.sum())*8;evaluated.to_mesh_clear()
 report={'revision':51,'nativeSha256':native_sha,'sourceNativeSha256':D['sourceNativeSha256'],'freshReopenVerified':True,'movieStatePreservedExactly':True,'nightScenePreservedExactly':True,'otherPosterObjectsMaterialsCameraLightingPreserved':True,'sharedNodeGroupsPreserved':True,'allPackedImageBytesPreserved':True,'packedImageCount':len(images_before),'unchangedOriginalFacePositionsAndUVsPreserved':True,'changedOriginalMeshes':changes,'addedSolids':closed,'ivy':{'sourceCount':len(points),'removedCount':int((~keep).sum()),'remainingCount':int(keep.sum()),'retainedPointsAndAttributesPreservedExactly':True,'evaluatedVertices':ivy_vertices,'evaluatedFaces':ivy_faces},'browserRuntimeVerified':False,'oneToOneComplete':False};write('verification-v51.json',report);print('FOREGROUND_51_NATIVE_VERIFIED',native_sha,flush=True)
 s.render.resolution_x=2124;s.render.resolution_y=3000;s.cycles.samples=28;s.render.use_border=True;s.render.use_crop_to_border=True;s.render.border_min_x=0;s.render.border_max_x=305/708;s.render.border_min_y=.286;s.render.border_max_y=.425;s.render.filepath=str(O/'foreground-detail-v51.png');bpy.ops.render.render(write_still=True);print('FOREGROUND_51_DETAIL_DONE',flush=True)
else:
 report=json.loads((O/'verification-v51.json').read_text());assert sha(native)==report['nativeSha256'];bpy.ops.wm.open_mainfile(filepath=str(native));s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1);s.render.use_border=False;s.render.use_crop_to_border=False;s.render.resolution_percentage=100;s.cycles.use_denoising=True
 if '--close' in sys.argv:
  s.camera.location=(-4.5,17,3.8);s.camera.rotation_euler=(Vector((-10.8,21.1,2.35))-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.lens=45;s.render.resolution_x=900;s.render.resolution_y=500;s.cycles.samples=24;s.render.filepath=str(O/'foreground-oblique-detail-v51.png');bpy.ops.render.render(write_still=True);print('FOREGROUND_51_CLOSE_DONE',flush=True)
 else:
  s.render.resolution_x=708;s.render.resolution_y=1000;s.cycles.samples=28;s.render.filepath=str(O/'poster-front-v51.png');bpy.ops.render.render(write_still=True);print('FOREGROUND_51_FRONT_DONE',flush=True)
  s.camera.location=(-9,-12,4);s.camera.rotation_euler=(Vector((0,2,3))-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.lens=30;s.render.resolution_x=720;s.render.resolution_y=468;s.cycles.samples=24;s.render.filepath=str(O/'poster-oblique-v51.png');bpy.ops.render.render(write_still=True);print('FOREGROUND_51_OBLIQUE_DONE',flush=True)
