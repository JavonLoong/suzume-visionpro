from pathlib import Path
import ast,hashlib,json,sys
import numpy as np
import bpy,bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

R=Path(__file__).parent;O=R/'poster-right-bow-v56';source=R/'poster-right-arches-v55/Suzume_dual_scene_right_arches_v55.blend';native=O/'Suzume_dual_scene_right_bow_v56.blend'
D=json.loads((O/'right-bow-geometry-v56.json').read_text());surface_updates=json.loads((O/'surface-restoration-v56.json').read_text())['surfaces'];plans=np.load(O/'right-bow-removal-v56.npz');base=np.load(O/'source-right-bow-v56.npz');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(source)==D['sourceNativeSha256'];changed={D['name']}|{q['name'] for q in D['sourceObjects']}
if not any(flag in sys.argv for flag in ['--before','--close','--final']):
 for filename,names in [('verify_render_poster_v38.py',['tree_hash','movie_snapshot']),('verify_render_horizon_v42.py',['scene_snapshot'])]:
  tree=ast.parse((R/filename).read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'snapshot helpers','exec'))
 bpy.ops.wm.open_mainfile(filepath=str(source));movie_before=movie_snapshot();poster_before=scene_snapshot('Official poster courtyard v38');night_before=scene_snapshot('Night meadow through the door');groups_before={g.name:tree_hash(g) for g in bpy.data.node_groups};images_before={im.name:hashlib.sha256(im.packed_file.data).hexdigest() for im in bpy.data.images if im.packed_file}
 s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1);preserved={};rows=[]
 for update in surface_updates:
  mat=bpy.data.materials[update['material']];tex=[n for n in mat.node_tree.nodes if n.type=='TEX_IMAGE'];assert len(tex)==1;assert hashlib.sha256(tex[0].image.packed_file.data).hexdigest()==update['previousAtlasSha256'];tex[0].image.use_fake_user=True;im=bpy.data.images.load(str(O/update['newAtlas']),check_existing=False);im.name=update['newImageName'];im.pack();tex[0].image=im;poster_before['materials'].pop(update['material'])
 for row in D['sourceObjects']:
  ob=s.objects[row['name']];m=ob.data;v=np.empty((len(m.vertices),3),'f4');m.vertices.foreach_get('co',v.ravel());M=np.array(ob.matrix_world);assert np.max(abs(v@M[:3,:3].T+M[:3,3]-base[row['key']+'_vertices']))<2e-6
  ix=np.empty(len(m.loops),np.int32);m.loops.foreach_get('vertex_index',ix);faces=ix.reshape(-1,3);remove=plans[row['key']];chosen=faces[~remove].ravel();keep=np.repeat(~remove,3);normal=np.empty((len(m.corner_normals),3),'f4');m.corner_normals.foreach_get('vector',normal.ravel());uv=np.empty((len(m.loops),2),'f4');m.uv_layers.active.data.foreach_get('uv',uv.ravel());points=v[chosen];normal=normal[keep];uv=uv[keep]
  mesh=bpy.data.meshes.new(m.name+' right bow replaced v56');mesh.from_pydata(points.tolist(),[],np.arange(len(points)).reshape(-1,3).tolist());mesh.update()
  for mat in m.materials:mesh.materials.append(mat)
  smooth_faces=np.empty(len(m.polygons),bool);m.polygons.foreach_get('use_smooth',smooth_faces);mesh.polygons.foreach_set('use_smooth',smooth_faces[~remove]);layer=mesh.uv_layers.new(name=m.uv_layers.active.name);layer.data.foreach_set('uv',uv.ravel());mesh.normals_split_custom_set(normal.tolist())
  # Preserve Blender's packed normals rather than quantizing them a second
  # time. Each original retained triangle already has separate vertices.
  packed=np.empty((len(m.loops),2),np.int32);m.attributes['custom_normal'].data.foreach_get('value',packed.ravel());mesh.attributes['custom_normal'].data.foreach_set('value',packed[keep].ravel());mesh.update();ob.data=mesh
  preserved[ob.name]={'positions':hashlib.sha256(points.tobytes()).hexdigest(),'uv':hashlib.sha256(uv.tobytes()).hexdigest(),'normals':normal.copy()};rows.append({'name':ob.name,'key':row['key'],'removedTriangles':int(remove.sum()),'retainedTriangles':int((~remove).sum())})
 paint=bpy.data.materials['Reference-calibrated upper facade pigments v48'].copy();paint.name=D['surfaceMaterial'];atlas=bpy.data.images.load(str(O/D['texture']),check_existing=False);atlas.name='Measured right bowed beam paint v56';atlas.pack();tex=[n for n in paint.node_tree.nodes if n.type=='TEX_IMAGE'];assert len(tex)==1;tex[0].image=atlas;tex[0].extension='EXTEND'
 vertices=np.array(D['verticesNative']);faces=np.array(D['triangles']);surfaces=np.array(D['faceSurfaceIndices']);mesh=bpy.data.meshes.new(D['name']+' closed mesh');mesh.from_pydata(vertices.tolist(),[],faces.tolist());mesh.update();mesh.materials.append(paint)
 layer=mesh.uv_layers.new(name='Unwrapped observed beam paint');layer.data.foreach_set('uv',np.array(D['textureUV'],dtype='f4')[faces.ravel()].ravel())
 normals=np.cross(vertices[faces[:,1]]-vertices[faces[:,0]],vertices[faces[:,2]]-vertices[faces[:,0]]);smooth=np.zeros((14,len(vertices),3))
 for k in range(3):np.add.at(smooth,(surfaces,faces[:,k]),normals)
 smooth/=np.maximum(np.linalg.norm(smooth,axis=2)[:,:,None],1e-15);loops=smooth[surfaces[:,None],faces].reshape(-1,3);mesh.normals_split_custom_set(loops.tolist())
 ob=bpy.data.objects.new(D['name'],mesh);col=bpy.data.collections.new('Poster measured right bow v56');s.collection.children.link(col);col.objects.link(ob);ob['poster_bow_revision']=56;ob['unseen_section_depth_inferred']=True
 s['poster_right_bow_revision']=56;s.render.use_border=False;s.render.use_crop_to_border=False;s.render.resolution_x=708;s.render.resolution_y=1000;s.render.resolution_percentage=100;s.cycles.samples=28;s.cycles.use_denoising=True;bpy.ops.wm.save_as_mainfile(filepath=str(native));digest=sha(native);bpy.ops.wm.open_mainfile(filepath=str(native))
 assert movie_before==movie_snapshot();assert night_before==scene_snapshot('Night meadow through the door');after=scene_snapshot('Official poster courtyard v38');after['materials'].pop(D['surfaceMaterial'])
 for update in surface_updates:after['materials'].pop(update['material'])
 assert poster_before==after;assert groups_before=={g.name:tree_hash(g) for g in bpy.data.node_groups};images_after={im.name:hashlib.sha256(im.packed_file.data).hexdigest() for im in bpy.data.images if im.packed_file};assert all(images_after[k]==v for k,v in images_before.items());assert images_after['Measured right bowed beam paint v56']==D['textureSha256']
 for update in surface_updates:assert images_after[update['newImageName']]==update['atlasSha256']
 s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1);bpy.context.view_layer.update()
 for name,q in preserved.items():
  m=s.objects[name].data;p=np.empty((len(m.vertices),3),'f4');m.vertices.foreach_get('co',p.ravel());uv=np.empty((len(m.loops),2),'f4');m.uv_layers.active.data.foreach_get('uv',uv.ravel());assert hashlib.sha256(p.tobytes()).hexdigest()==q['positions'];assert hashlib.sha256(uv.tobytes()).hexdigest()==q['uv'];n=np.empty((len(m.corner_normals),3),'f4');m.corner_normals.foreach_get('vector',n.ravel());err=np.max(abs(n-q['normals']),axis=1)
  if err.max()>=2e-4:
   ii=np.argsort(err)[-8:];(O/'normal-diagnostics-v56.json').write_text(json.dumps({'name':name,'maximumError':float(err.max()),'mismatchedCorners':int((err>=2e-4).sum()),'examples':[{'corner':int(i),'before':q['normals'][i].tolist(),'after':n[i].tolist(),'position':p[i].tolist()} for i in ii]},indent=2))
  assert err.max()<2e-4
  next(row for row in rows if row['name']==name)['maximumRetainedNormalError']=float(err.max())
 m=s.objects[D['name']].data;p=np.array([q.co[:] for q in m.vertices]);error=float(np.max(abs(p-vertices)));assert error<2e-6;bm=bmesh.new();bm.from_mesh(m);bad=sum(not e.is_manifold for e in bm.edges);volume=bm.calc_volume();bm.free();assert bad==0 and volume>0
 uv=np.empty((len(m.loops),2),'f4');m.uv_layers.active.data.foreach_get('uv',uv.ravel());assert np.array_equal(uv,np.array(D['textureUV'],dtype='f4')[faces.ravel()])
 target=s.objects[D['support']];support_vertices=[target.matrix_world@q.co for q in target.data.vertices];trees={'beam':BVHTree.FromPolygons(p.tolist(),faces.tolist(),all_triangles=True),'support':BVHTree.FromPolygons(support_vertices,[q.vertices[:] for q in target.data.polygons],all_triangles=True)}
 direction=Vector((.271,.511,.816)).normalized()
 def inside(tree,point):
  origin=Vector(point);hits=0
  for _ in range(50):
   q,_,_,_=tree.ray_cast(origin,direction,100)
   if q is None:break
   hits+=1;origin=q+direction*1e-5
  return bool(hits%2)
 shared=[]
 for q in np.array(D['centerlineNative'])[:6]:
  if all(inside(tree,q) for tree in trees.values()):shared.append(q.tolist())
 assert shared,'Beam root does not physically overlap support'
 report={'revision':56,'sourceNativeSha256':D['sourceNativeSha256'],'nativeSha256':digest,'freshReopenVerified':True,'movieStatePreservedExactly':True,'nightScenePreservedExactly':True,'otherPosterObjectsMaterialsCameraLightingPreserved':True,'sharedNodeGroupsPreserved':True,'allExistingPackedImageBytesPreserved':True,'preservedOriginalPackedImages':len(images_before),'packedImageCount':len(images_after),'newPaintImageSha256':D['textureSha256'],'changedOriginalMeshes':rows,'retainedOriginalCoordinatesUVsAndNormalsPreserved':True,'addedMember':{'name':D['name'],'triangles':len(faces),'nonManifoldEdges':bad,'signedVolume':volume,'maximumVertexErrorMeters':error,'textureUVPreservedExactly':True},'supportJoint':{'support':D['support'],'sharedInteriorPoints':shared,'solidOverlapVerified':True},'fittedTopBoundaryMaximumErrorPixels':D['maximumTopBoundaryErrorPixels'],'fittedBottomBoundaryMaximumErrorPixels':D['maximumBottomBoundaryErrorPixels'],'measurementUncertaintyPixels':.6,'browserRuntimeVerified':False,'oneToOneComplete':False}
 report['surfaceMaterialUpdates']=surface_updates
 (O/'verification-v56.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print('RIGHT_BOW_56_NATIVE_VERIFIED',digest,flush=True)
elif '--before' in sys.argv:
 bpy.ops.wm.open_mainfile(filepath=str(source));s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1)
else:
 report=json.loads((O/'verification-v56.json').read_text());assert sha(native)==report['nativeSha256'];bpy.ops.wm.open_mainfile(filepath=str(native));s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1)
s.render.use_border=False;s.render.use_crop_to_border=False;s.render.resolution_percentage=100;s.cycles.use_denoising=True
if '--final' in sys.argv:
 s.render.resolution_x=708;s.render.resolution_y=1000;s.cycles.samples=28;s.render.filepath=str(O/'poster-front-v56.png');bpy.ops.render.render(write_still=True);print('RIGHT_BOW_56_FRONT_DONE',flush=True);s.camera.location=(9,-12,4);s.camera.rotation_euler=(Vector((0,2,3))-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.lens=30;s.render.resolution_x=720;s.render.resolution_y=468;s.cycles.samples=24;s.render.filepath=str(O/'poster-oblique-v56.png');bpy.ops.render.render(write_still=True);print('RIGHT_BOW_56_OBLIQUE_DONE',flush=True)
elif '--close' in sys.argv:
 s.camera.location=(2,13,5);s.camera.rotation_euler=(Vector((9,21,5.3))-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.lens=35;s.render.resolution_x=1000;s.render.resolution_y=600;s.cycles.samples=24;s.render.filepath=str(O/'right-bow-oblique-detail-v56.png');bpy.ops.render.render(write_still=True);print('RIGHT_BOW_56_CLOSE_DONE',flush=True)
else:
 s.render.resolution_x=2832;s.render.resolution_y=4000;s.cycles.samples=28;s.render.use_border=True;s.render.use_crop_to_border=True;s.render.border_min_x=500/708;s.render.border_max_x=1;s.render.border_min_y=.365;s.render.border_max_y=.430;s.render.filepath=str(O/('right-bow-before-v55.png' if '--before' in sys.argv else 'right-bow-detail-v56.png'));bpy.ops.render.render(write_still=True);print('RIGHT_BOW_56_DETAIL_DONE',flush=True)
