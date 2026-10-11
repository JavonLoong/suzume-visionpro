from pathlib import Path
import ast,json,hashlib,sys
import bpy,bmesh,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

R=Path(__file__).parent;O=R/'poster-right-facade-v54';source=R/'poster-low-rails-v53/Suzume_dual_scene_low_rails_v53.blend';native=O/'Suzume_dual_scene_right_facade_v54.blend';D=json.loads((O/'right-facade-geometry-v54.json').read_text());plans=np.load(O/'right-facade-removal-v54.npz');old=[q for q in D['sourceObjects'] if plans[q['key']].any()];changed={q['name'] for q in old+D['members']}
C=np.array(D['camera']['position']);rot=np.array(D['camera']['rotation']);f=D['camera']['focalPixels']
def projected_uv(v):
 q=(np.asarray(v)-C)@rot;px=1000+f*2.824*q[...,0]/-q[...,2];py=1412-f*2.824*q[...,1]/-q[...,2];return np.stack((px/2000,1-(py-1410)/600),axis=-1)
def clip_below(vertices,z=.20):
 out=[]
 for a,b in zip(vertices,[*vertices[1:],vertices[0]]):
  ain=a[2]<=z;bin=b[2]<=z
  if ain:out.append(a)
  if ain!=bin:out.append(a+(b-a)*((z-a[2])/(b[2]-a[2])))
 return [np.array([out[0],out[i],out[i+1]]) for i in range(1,len(out)-1)]

def subtract_volume(triangle,volume):
 center=np.array(volume['center']);t=np.array(volume['tangent']);r=np.array(volume['radial']);x0,x1=volume['x'];d0,d1=volume['d'];z0,z1=volume['z'];planes=[(t,-np.dot(center,t)-x0),(-t,np.dot(center,t)+x1),(-r,np.dot(center,r)-d0),(r,-np.dot(center,r)+d1),(np.array([0,0,1]),-z0),(np.array([0,0,-1]),z1)];inside=list(triangle);result=[]
 for n,c in planes:
  if not inside:break
  keep=[];outside=[]
  for a,b in zip(inside,[*inside[1:],inside[0]]):
   va=np.dot(n,a[:3])+c;vb=np.dot(n,b[:3])+c;ain=va>=0;bin=vb>=0
   (keep if ain else outside).append(a)
   if ain!=bin:
    q=a+(b-a)*(va/(va-vb));keep.append(q);outside.append(q)
  result.extend(np.array([outside[0],outside[i],outside[i+1]]) for i in range(1,len(outside)-1));inside=keep
 return result

if not any(flag in sys.argv for flag in ['--final','--close','--before']):
 assert hashlib.sha256(source.read_bytes()).hexdigest()==D['sourceNativeSha256']
 for filename,names in [('verify_render_poster_v38.py',['tree_hash','movie_snapshot']),('verify_render_horizon_v42.py',['scene_snapshot'])]:
  tree=ast.parse((R/filename).read_text(encoding='utf-8'));exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'snapshot helpers','exec'))
 bpy.ops.wm.open_mainfile(filepath=str(source));movie_before=movie_snapshot();poster_before=scene_snapshot('Official poster courtyard v38');night_before=scene_snapshot('Night meadow through the door');groups_before={g.name:tree_hash(g) for g in bpy.data.node_groups};images_before={im.name:hashlib.sha256(im.packed_file.data).hexdigest() for im in bpy.data.images if im.packed_file}
 s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1);bpy.context.view_layer.update();retained={};changes=[];baseline=np.load(R/D['sourceGeometryFile'])
 for row in old:
  ob=s.objects[row['name']];m=ob.data;plan=plans[row['key']];v=np.array([p.co[:] for p in m.vertices]);M=np.array(ob.matrix_world);world=v@M[:3,:3].T+M[:3,3];source_error=float(np.max(abs(world-baseline[row['key']+'_vertices'])));assert source_error<2e-6,(row['key'],source_error);assert all(len(p.vertices)==3 for p in m.polygons);assert len(m.materials)==1 and len(m.uv_layers)==1 and len(m.color_attributes)==0
  ix=np.array([p.vertices[:] for p in m.polygons]);loops=np.array([p.loop_indices[:] for p in m.polygons]);norm=np.empty((len(m.corner_normals),3),'f4');m.corner_normals.foreach_get('vector',norm.ravel());normworld=norm@np.linalg.inv(M[:3,:3]);uv=np.empty((len(m.loops),2),'f4');m.uv_layers.active.data.foreach_get('uv',uv.ravel())
  keep=plan==0;packed=np.concatenate([world[ix],normworld[loops],uv[loops]],axis=2);unchanged=packed[keep].reshape(-1,8);extra=[]
  for triangle in packed[plan==2]:extra.extend(clip_below(list(triangle)))
  for triangle in packed[plan==3]:
   pieces=[triangle]
   for volume in D['cutVolumes']:pieces=[q for p in pieces for q in subtract_volume(p,volume)]
   extra.extend(pieces)
  points=np.concatenate([unchanged,np.array(extra).reshape(-1,8)]) if extra else unchanged
  local=(points[:,:3]-M[:3,3])@np.linalg.inv(M[:3,:3]).T;normal=points[:,3:6]@M[:3,:3];normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-12)
  new=bpy.data.meshes.new(m.name+' lower facade replaced v54');new.from_pydata(local.tolist(),[],np.arange(len(local)).reshape(-1,3).tolist());new.update();new.materials.append(m.materials[0]);layer=new.uv_layers.new(name=m.uv_layers.active.name);layer.data.foreach_set('uv',points[:,6:8].astype('f4').ravel());new.normals_split_custom_set(normal.tolist());ob.data=new
  kept_count=len(unchanged);retained[ob.name]={'count':kept_count,'positions':hashlib.sha256(local[:kept_count].astype('f4').tobytes()).hexdigest(),'uv':hashlib.sha256(points[:kept_count,6:8].astype('f4').tobytes()).hexdigest()};changes.append({'key':row['key'],'name':ob.name,'removedTriangles':int((plan==1).sum()),'clippedOriginalTriangles':int((plan==2).sum()),'boundaryTrimmedOriginalTriangles':int((plan==3).sum()),'keptTriangles':int(keep.sum()),'newClipTriangles':len(extra),'finalTriangles':len(local)//3})
 paint=bpy.data.materials['Reference-calibrated upper facade pigments v48'].copy();paint.name=D['materials'][0];atlas=bpy.data.images.load(str(O/'right-facade-pigments-v54.png'),check_existing=False);atlas.name='Restored far-right source pigments v54';atlas.pack();nodes=[n for n in paint.node_tree.nodes if n.type=='TEX_IMAGE' and n.image and list(n.image.size)==[2000,600]];assert len(nodes)==1;nodes[0].image=atlas
 materials=[bpy.data.materials[name] for name in D['materials']]
 col=bpy.data.collections.new('Poster reconstructed lower facade v54');s.collection.children.link(col)
 for q in D['members']:
  m=bpy.data.meshes.new(q['name']+' closed solid');m.from_pydata(q['verticesNative'],[],q['triangles']);m.update()
  for mat in materials:m.materials.append(mat)
  m.polygons.foreach_set('material_index',q['materialIndices']);uv=projected_uv(np.array(q['verticesNative']));ix=np.array([p.vertices[:] for p in m.polygons]).ravel();layer=m.uv_layers.new(name='Reference surface UV');layer.data.foreach_set('uv',uv[ix].astype('f4').ravel());ob=bpy.data.objects.new(q['name'],m);col.objects.link(ob);ob['lower_facade_revision']=54;ob['unobserved_detail_inferred']=True
 s['lower_facade_revision']=54;s.render.use_border=False;s.render.use_crop_to_border=False;s.render.resolution_x=708;s.render.resolution_y=1000;s.render.resolution_percentage=100;s.cycles.samples=28;s.cycles.use_denoising=True
 bpy.ops.wm.save_as_mainfile(filepath=str(native));sha=hashlib.sha256(native.read_bytes()).hexdigest();bpy.ops.wm.open_mainfile(filepath=str(native));assert movie_before==movie_snapshot();assert night_before==scene_snapshot('Night meadow through the door');after=scene_snapshot('Official poster courtyard v38')
 after['materials'].pop(D['materials'][0]);assert poster_before==after;assert groups_before=={g.name:tree_hash(g) for g in bpy.data.node_groups};images_after={im.name:hashlib.sha256(im.packed_file.data).hexdigest() for im in bpy.data.images if im.packed_file};assert all(images_after[name]==value for name,value in images_before.items());assert images_after['Restored far-right source pigments v54']==hashlib.sha256((O/'right-facade-pigments-v54.png').read_bytes()).hexdigest()
 s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1);bpy.context.view_layer.update();closed=[]
 for name,want in retained.items():
  m=s.objects[name].data;v=np.array([p.co[:] for p in m.vertices],dtype='f4');uv=np.empty((len(m.loops),2),'f4');m.uv_layers.active.data.foreach_get('uv',uv.ravel());assert hashlib.sha256(v[:want['count']].tobytes()).hexdigest()==want['positions'];assert hashlib.sha256(uv[:want['count']].tobytes()).hexdigest()==want['uv']
 for q in D['members']:
  m=s.objects[q['name']].data;v=np.array([p.co[:] for p in m.vertices]);error=float(np.max(abs(v-np.array(q['verticesNative']))));assert error<2e-6;bm=bmesh.new();bm.from_mesh(m);bad=sum(not e.is_manifold for e in bm.edges);volume=bm.calc_volume();bm.free();assert bad==0 and volume>0,(q['name'],bad,volume);closed.append({'name':q['name'],'kind':q['kind'],'triangles':len(m.polygons),'nonManifoldEdges':bad,'signedVolume':volume,'maximumVertexErrorMeters':error})
 names=[q['name'] for q in D['sourceObjects']]+[q['name'] for q in D['members'] if q['kind'] in ['wall','pier','cornice','hood','floor','partition','foundation']];vv=[];ff=[];face_names=[];offset=0
 for name in names:
  ob=s.objects[name];vv.extend([ob.matrix_world@v.co for v in ob.data.vertices]);ff.extend([[i+offset for i in p.vertices] for p in ob.data.polygons]);face_names.extend([name]*len(ob.data.polygons));offset+=len(ob.data.vertices)
 tree=BVHTree.FromPolygons(vv,ff,all_triangles=True);probes=[];blocked=[]
 for q in D['structuralProbeSpecifications']:
  hit=tree.ray_cast(Vector(q['point']),Vector(q['direction']),q['distance'])
  if hit[0] is not None:blocked.append({**q,'object':face_names[hit[2]],'hit':list(hit[0]),'distanceToHit':hit[3]})
  else:probes.append(q)
 (O/'opening-probe-diagnostics-v54.json').write_text(json.dumps({'clear':len(probes),'blocked':blocked},indent=2));assert not blocked,blocked
 rec=next(q for q in D['openings'] if q['kind']=='door');a0,a1=.006904,.147421;a=(a0+a1)/2;rad=np.array([np.sin(a),np.cos(a),0]);t=np.array([np.cos(a),-np.sin(a),0]);chord=23.5*np.cos((a1-a0)/2);floor_probes=[]
 for x in [-.5,0,.5]:
  for d in [-.45,-1.5,-3.8]:
   point=rad*(chord-d)+t*x+np.array([0,0,1.10]);hit=tree.ray_cast(Vector(point),Vector((0,0,-1)),1.0);assert hit[0] is not None and abs(hit[0].z-rec['z'][0])<2e-6,(x,d,hit);floor_probes.append({'x':x,'inwardDepth':d,'floorZ':hit[0].z,'object':face_names[hit[2]]})
 ob=s.objects['Poster right entrance v54 stair foundation'];ft=BVHTree.FromPolygons([v.co for v in ob.data.vertices],[p.vertices[:] for p in ob.data.polygons],all_triangles=True);step=s.objects['Poster right entrance v54 step 2'];bottom=min(v.co.z for v in step.data.vertices);step_probes=[]
 for p in [v.co for v in step.data.vertices if abs(v.co.z-bottom)<1e-6]:
  hit=ft.ray_cast(p+Vector((0,0,.04)),Vector((0,0,-1)),.10);assert hit[0] is not None;gap=p.z-hit[0].z;assert -.004<gap<0;step_probes.append({'point':list(p),'gapMeters':gap})
 report={'revision':54,'nativeSha256':sha,'sourceNativeSha256':D['sourceNativeSha256'],'freshReopenVerified':True,'movieStatePreservedExactly':True,'nightScenePreservedExactly':True,'otherPosterObjectsMaterialsCameraLightingPreserved':True,'sharedNodeGroupsPreserved':True,'allPackedImageBytesPreserved':True,'packedImageCount':len(images_after),'preservedOriginalPackedImages':len(images_before),'restoredAtlasSha256':images_after['Restored far-right source pigments v54'],'unchangedOriginalFacePositionsAndUVsPreserved':True,'changedOriginalMeshes':changes,'addedSolids':closed,'structuralOpeningProbes':probes,'entranceFloorProbes':floor_probes,'stairFoundationProbes':step_probes,'browserRuntimeVerified':False,'oneToOneComplete':False};(O/'verification-v54.json').write_text(json.dumps(report,indent=2));print('RIGHT_FACADE_54_NATIVE_VERIFIED',sha,flush=True)
elif '--before' in sys.argv:
 assert hashlib.sha256(source.read_bytes()).hexdigest()==D['sourceNativeSha256'];bpy.ops.wm.open_mainfile(filepath=str(source));s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1)
else:
 report=json.loads((O/'verification-v54.json').read_text());assert hashlib.sha256(native.read_bytes()).hexdigest()==report['nativeSha256'];bpy.ops.wm.open_mainfile(filepath=str(native));s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1)

s.render.use_border=False;s.render.use_crop_to_border=False;s.render.resolution_percentage=100;s.cycles.use_denoising=True
if '--final' in sys.argv:
 s.render.resolution_x=708;s.render.resolution_y=1000;s.cycles.samples=28;s.render.filepath=str(O/'poster-front-v54.png');bpy.ops.render.render(write_still=True);print('RIGHT_FACADE_54_FRONT_DONE',flush=True)
 s.camera.location=(9,-12,4);s.camera.rotation_euler=(Vector((0,2,3))-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.lens=30;s.render.resolution_x=720;s.render.resolution_y=468;s.cycles.samples=24;s.render.filepath=str(O/'poster-oblique-v54.png');bpy.ops.render.render(write_still=True);print('RIGHT_FACADE_54_OBLIQUE_DONE',flush=True)
elif '--close' in sys.argv:
 s.camera.location=(2,13,3.2);s.camera.rotation_euler=(Vector((9,21,2.6))-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.lens=35;s.render.resolution_x=1000;s.render.resolution_y=600;s.cycles.samples=24;s.render.filepath=str(O/'right-facade-oblique-detail-v54.png');bpy.ops.render.render(write_still=True);print('RIGHT_FACADE_54_CLOSE_DONE',flush=True)
else:
 s.render.resolution_x=2124;s.render.resolution_y=3000;s.cycles.samples=28;s.render.use_border=True;s.render.use_crop_to_border=True;s.render.border_min_x=390/708;s.render.border_max_x=1;s.render.border_min_y=.285;s.render.border_max_y=.400;s.render.filepath=str(O/('right-facade-before-v53.png' if '--before' in sys.argv else 'right-facade-detail-v54.png'));bpy.ops.render.render(write_still=True);print('RIGHT_FACADE_54_DETAIL_DONE',flush=True)
