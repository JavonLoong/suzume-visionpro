from pathlib import Path
import ast,json,hashlib,sys
import bpy,bmesh,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

R=Path(__file__).parent;O=R/'poster-upper-windows-v48';source=R/'poster-fascia-v47/Suzume_dual_scene_fascia_v47.blend';native=O/'Suzume_dual_scene_upper_windows_v48.blend';D=json.loads((O/'upper-window-geometry-v48.json').read_text());plans=np.load(O/'upper-window-removal-v48.npz');old=[q for q in D['sourceObjects'] if plans[q['key']].any()];changed={q['name'] for q in old+D['members']}
C=np.array(D['camera']['position']);rot=np.array(D['camera']['rotation']);f=D['camera']['focalPixels']
def projected_uv(v):
 q=(np.asarray(v)-C)@rot;px=1000+f*2.824*q[...,0]/-q[...,2];py=1412-f*2.824*q[...,1]/-q[...,2];return np.stack((px/2000,1-(py-1410)/600),axis=-1)
def clip_below(vertices,z=5.48):
 out=[]
 for a,b in zip(vertices,[*vertices[1:],vertices[0]]):
  ain=a[2]<=z;bin=b[2]<=z
  if ain:out.append(a)
  if ain!=bin:out.append(a+(b-a)*((z-a[2])/(b[2]-a[2])))
 return [np.array([out[0],out[i],out[i+1]]) for i in range(1,len(out)-1)]

if '--final' not in sys.argv:
 assert hashlib.sha256(source.read_bytes()).hexdigest()==D['sourceNativeSha256']
 for filename,names in [('verify_render_poster_v38.py',['tree_hash','movie_snapshot']),('verify_render_horizon_v42.py',['scene_snapshot'])]:
  tree=ast.parse((R/filename).read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'snapshot helpers','exec'))
 bpy.ops.wm.open_mainfile(filepath=str(source));movie_before=movie_snapshot();poster_before=scene_snapshot('Official poster courtyard v38');night_before=scene_snapshot('Night meadow through the door');groups_before={g.name:tree_hash(g) for g in bpy.data.node_groups}
 s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1);bpy.context.view_layer.update();retained={};changes=[];baseline=np.load(R/D['sourceGeometryFile'])
 for row in old:
  ob=s.objects[row['name']];m=ob.data;plan=plans[row['key']];v=np.array([p.co[:] for p in m.vertices]);M=np.array(ob.matrix_world);world=v@M[:3,:3].T+M[:3,3];source_error=float(np.max(abs(world-baseline[row['key']+'_vertices'])));assert source_error<2e-6,(row['key'],source_error);assert all(len(p.vertices)==3 for p in m.polygons);assert len(m.materials)==1 and len(m.uv_layers)==1 and len(m.color_attributes)==0
  ix=np.array([p.vertices[:] for p in m.polygons]);loops=np.array([p.loop_indices[:] for p in m.polygons]);norm=np.empty((len(m.corner_normals),3),'f4');m.corner_normals.foreach_get('vector',norm.ravel());normworld=norm@np.linalg.inv(M[:3,:3]);uv=np.empty((len(m.loops),2),'f4');m.uv_layers.active.data.foreach_get('uv',uv.ravel())
  keep=plan==0;packed=np.concatenate([world[ix],normworld[loops],uv[loops]],axis=2);unchanged=packed[keep].reshape(-1,8);extra=[]
  for triangle in packed[plan==2]:extra.extend(clip_below(list(triangle)))
  points=np.concatenate([unchanged,np.array(extra).reshape(-1,8)]) if extra else unchanged
  local=(points[:,:3]-M[:3,3])@np.linalg.inv(M[:3,:3]).T;normal=points[:,3:6]@M[:3,:3];normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-12)
  new=bpy.data.meshes.new(m.name+' upper openings v48');new.from_pydata(local.tolist(),[],np.arange(len(local)).reshape(-1,3).tolist());new.update();new.materials.append(m.materials[0]);layer=new.uv_layers.new(name=m.uv_layers.active.name);layer.data.foreach_set('uv',points[:,6:8].astype('f4').ravel());new.normals_split_custom_set(normal.tolist());ob.data=new
  kept_count=len(unchanged);retained[ob.name]={'count':kept_count,'positions':hashlib.sha256(local[:kept_count].astype('f4').tobytes()).hexdigest(),'uv':hashlib.sha256(points[:kept_count,6:8].astype('f4').tobytes()).hexdigest()};changes.append({'key':row['key'],'name':ob.name,'removedTriangles':int((plan==1).sum()),'clippedOriginalTriangles':int((plan==2).sum()),'keptTriangles':int(keep.sum()),'newClipTriangles':len(extra),'finalTriangles':len(local)//3})
 paint=bpy.data.materials['Reference-calibrated facade surface pigments.001'].copy();paint.name='Reference-calibrated upper facade pigments v48';atlas=bpy.data.images.load(str(O/'upper-facade-pigments-v48.png'),check_existing=False);atlas.name='Upper facade source resolution pigments v48';atlas.pack();texture_nodes=[n for n in paint.node_tree.nodes if n.type=='TEX_IMAGE' and n.image and list(n.image.size)==[1100,330]];assert len(texture_nodes)==1
 texture_nodes[0].image=atlas
 original_paint=bpy.data.materials['Reference-calibrated facade surface pigments.001'];original_paint.use_fake_user=True;original_image=next(n.image for n in original_paint.node_tree.nodes if n.type=='TEX_IMAGE' and n.image and list(n.image.size)==[1100,330]);assert hashlib.sha256(original_image.packed_file.data).hexdigest()=='0a3213ef7c7033e4b5d3b8c9ff43d630f0118aeb8d23867c3c9d36834f3a5498'
 cleanpaint=original_paint.copy();cleanpaint.name='Reference facade with foreground rods removed v48';cleanimage=bpy.data.images.load(str(O/'clean-facade-pigments-v48.png'),check_existing=False);cleanimage.name='Original facade minus thin foreground rods v48';cleanimage.pack();next(n for n in cleanpaint.node_tree.nodes if n.type=='TEX_IMAGE' and n.image and list(n.image.size)==[1100,330]).image=cleanimage;s.objects[D['sourceObjects'][18]['name']].data.materials[0]=cleanpaint
 def material(name,color,roughness,metalness):
  m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*color,1);bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Roughness'].default_value=roughness;bs.inputs['Metallic'].default_value=metalness;return m
 jamb=material('Poster upper window recessed faces v48',[.23,.27,.29],.87,.08);glass=material('Poster upper window glazing edge v48',[.10,.17,.23],.24,.20)
 divider_source=s.objects[D['sourceObjects'][16]['name']].data.materials[0];materials=[paint,jamb,glass,divider_source];newmatnames=[m.name for m in materials[:3]]+[cleanpaint.name]
 col=bpy.data.collections.new('Poster corrected upper window storey v48');s.collection.children.link(col)
 for q in D['members']:
  m=bpy.data.meshes.new(q['name']+' closed solid');m.from_pydata(q['verticesNative'],[],q['triangles']);m.update()
  for mat in materials:m.materials.append(mat)
  m.polygons.foreach_set('material_index',q['materialIndices']);uv=projected_uv(np.array(q['verticesNative']));ix=np.array([p.vertices[:] for p in m.polygons]).ravel();layer=m.uv_layers.new(name='Reference surface UV');layer.data.foreach_set('uv',uv[ix].astype('f4').ravel());ob=bpy.data.objects.new(q['name'],m);col.objects.link(ob);ob['upper_windows_revision']=48;ob['unobserved_detail_inferred']=True
 s['upper_windows_revision']=48;s.render.use_border=False;s.render.use_crop_to_border=False;s.render.resolution_x=708;s.render.resolution_y=1000;s.render.resolution_percentage=100;s.cycles.samples=28;s.cycles.use_denoising=True
 bpy.ops.wm.save_as_mainfile(filepath=str(native));sha=hashlib.sha256(native.read_bytes()).hexdigest();bpy.ops.wm.open_mainfile(filepath=str(native));assert movie_before==movie_snapshot();assert night_before==scene_snapshot('Night meadow through the door');after=scene_snapshot('Official poster courtyard v38')
 for name in newmatnames:after['materials'].pop(name)
 poster_before['materials'].pop('Reference-calibrated facade surface pigments.001');after['materials'].pop('Reference-calibrated facade surface pigments.001',None)
 assert poster_before==after;assert groups_before=={g.name:tree_hash(g) for g in bpy.data.node_groups}
 s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1);bpy.context.view_layer.update();closed=[]
 for name,want in retained.items():
  m=s.objects[name].data;v=np.array([p.co[:] for p in m.vertices],dtype='f4');uv=np.empty((len(m.loops),2),'f4');m.uv_layers.active.data.foreach_get('uv',uv.ravel());assert hashlib.sha256(v[:want['count']].tobytes()).hexdigest()==want['positions'];assert hashlib.sha256(uv[:want['count']].tobytes()).hexdigest()==want['uv']
 for q in D['members']:
  m=s.objects[q['name']].data;v=np.array([p.co[:] for p in m.vertices]);error=float(np.max(abs(v-np.array(q['verticesNative']))));assert error<2e-6;bm=bmesh.new();bm.from_mesh(m);bad=sum(not e.is_manifold for e in bm.edges);volume=bm.calc_volume();bm.free();assert bad==0 and volume>0,(q['name'],bad,volume);closed.append({'name':q['name'],'kind':q['kind'],'triangles':len(m.polygons),'nonManifoldEdges':bad,'signedVolume':volume,'maximumVertexErrorMeters':error})
 # Probe the structural opening before the pane is considered: the previous
 # wall and room divider must not remain immediately behind a painted window.
 wall_objects=[s.objects[q['name']] for q in D['sourceObjects']]+[s.objects[q['name']] for q in D['members'] if q['kind'] in ['wall','partition']]
 vv=[];ff=[];offset=0
 for ob in wall_objects:
  vv.extend([ob.matrix_world@v.co for v in ob.data.vertices]);ff.extend([[i+offset for i in p.vertices] for p in ob.data.polygons]);offset+=len(ob.data.vertices)
 tree=BVHTree.FromPolygons(vv,ff,all_triangles=True);probes=[]
 edges=(np.arange(33)-16.5)*np.pi/16;edges[13:21]=[-.745387,-.567705,-.415142,-.217486,.006904,.147421,.411245,.678266]
 for q in D['windowParts']:
  i=q['bay'];a=(edges[i]+edges[i+1])/2;h=(edges[i+1]-edges[i])/2;rad=np.array([np.sin(a),np.cos(a),0]);t=np.array([np.cos(a),-np.sin(a),0]);x=sum(q['x'])/2;z=sum(q['z'])/2;p=rad*(23.5*np.cos(h)) +t*x+[0,0,z];start=p-rad*.20;hit=tree.ray_cast(Vector(start),Vector(rad),1.0)[0];assert hit is None,(q,hit);probes.append({'window':q['id'],'bay':i,'start':start.tolist(),'direction':rad.tolist(),'clearDistanceMeters':1.0})
 assert bpy.data.images['Upper facade source resolution pigments v48'].packed_file and bpy.data.images['Original facade minus thin foreground rods v48'].packed_file
 report={'revision':48,'nativeSha256':sha,'sourceNativeSha256':D['sourceNativeSha256'],'freshReopenVerified':True,'movieStatePreservedExactly':True,'nightScenePreservedExactly':True,'otherPosterObjectsMaterialsCameraLightingPreserved':True,'sharedNodeGroupsPreserved':True,'unchangedOriginalFacePositionsAndUVsPreserved':True,'changedOriginalMeshes':changes,'addedSolids':closed,'structuralOpeningProbes':probes,'sourceResolutionAtlasPacked':True,'browserRuntimeVerified':False,'oneToOneComplete':False};(O/'verification-v48.json').write_text(json.dumps(report,indent=2));print('UPPER_WINDOWS_48_NATIVE_VERIFIED',sha,flush=True)
 s.render.resolution_x=2124;s.render.resolution_y=3000;s.cycles.samples=28;s.render.use_border=True;s.render.use_crop_to_border=True;s.render.border_min_x=0;s.render.border_max_x=300/708;s.render.border_min_y=.370;s.render.border_max_y=.445;s.render.filepath=str(O/'upper-window-detail-v48.png');bpy.ops.render.render(write_still=True);print('UPPER_WINDOWS_48_DETAIL_DONE',flush=True)
else:
 report=json.loads((O/'verification-v48.json').read_text());assert hashlib.sha256(native.read_bytes()).hexdigest()==report['nativeSha256'];bpy.ops.wm.open_mainfile(filepath=str(native));s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1)
 s.render.use_border=False;s.render.use_crop_to_border=False;s.render.resolution_x=708;s.render.resolution_y=1000;s.render.resolution_percentage=100;s.cycles.samples=28;s.cycles.use_denoising=True;s.render.filepath=str(O/'poster-front-v48.png');bpy.ops.render.render(write_still=True);print('UPPER_WINDOWS_48_FRONT_DONE',flush=True)
 s.camera.location=(-9,-12,4);s.camera.rotation_euler=(Vector((0,2,3))-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.lens=30;s.render.resolution_x=720;s.render.resolution_y=468;s.cycles.samples=24;s.render.filepath=str(O/'poster-oblique-v48.png');bpy.ops.render.render(write_still=True);print('UPPER_WINDOWS_48_OBLIQUE_DONE',flush=True)
