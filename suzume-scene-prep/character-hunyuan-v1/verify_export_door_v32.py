"""Fresh-file checks and a complete posed character export for the browser."""
from pathlib import Path
import bpy,json,numpy as np,hashlib,sys
from mathutils import Vector
R=Path(__file__).parent;O=R/'movie-door-v32';W=R/'viewer/character-v32';W.mkdir(exist_ok=True);sys.path.insert(0,str(R))
from night_audit_v30 import fingerprint
f=O/'Suzume_scene_movie_door_v32.blend';bpy.ops.wm.open_mainfile(filepath=str(f));s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72)
a=json.loads((O/'integration-v32.json').read_text());body=bpy.data.objects['Suzume Hunyuan textured surface'];rig=bpy.data.objects['Suzume Hunyuan rig']
assert fingerprint(body,True)==a['bodyEvaluatedHash']
for n,h in a['preservedHeadHashes'].items():assert fingerprint(bpy.data.objects[n],True)==h
hinges=[bpy.data.objects[n] for n in ['Animated door leaf and hinges','Synchronized night door leaf']]
for frame in [1,36,48,60,72]:
 s.frame_set(frame);bpy.context.view_layer.update();assert np.max(np.abs(np.array(hinges[0].matrix_world)-np.array(hinges[1].matrix_world)))<1e-6
 M=hinges[0].matrix_world;assert abs((M@Vector((1.6,0,0))-M@Vector((0,0,0))).length-1.4089207)<1e-6
s.frame_set(72);bpy.context.view_layer.update();partition=[]
names=[body.name]+list(a['preservedHeadHashes'])
for n in names:
 o=bpy.data.objects[n];partner=bpy.data.objects['Suzume Hunyuan entered portion' if n==body.name else n+' — entered portion'];assert o.data==partner.data
 dm=o.material_slots[0].material;nm=partner.material_slots[0].material
 assert dm['spatial_half']=='courtyard' and nm['spatial_half']=='otherworld'
 gate=float(dm['portal_plane_blender_y']);assert abs(gate-.071999914944)<1e-6;assert abs(float(nm['portal_plane_blender_y'])-gate)<1e-6
 partition.append({'name':n,'sharedGeometry':True,'dayHalf':dm['spatial_half'],'nightHalf':nm['spatial_half'],'planeY':gate})
dep=bpy.context.evaluated_depsgraph_get();copies=[]
for n in names:
 ob=bpy.data.objects[n];mesh=bpy.data.meshes.new_from_object(ob.evaluated_get(dep),preserve_all_data_layers=True,depsgraph=dep);mesh.transform(ob.matrix_world);mesh.materials.clear()
 for slot in ob.material_slots:
  mat=slot.material.copy();nodes=mat.node_tree.nodes;out=next(q for q in nodes if q.type=='OUTPUT_MATERIAL' and q.is_active_output);mix=nodes.get('Spatial doorway half-space')
  if mix:mat.node_tree.links.new(mix.inputs[1].links[0].from_socket,out.inputs['Surface'])
  mat['spatial_half']='full_surface';mesh.materials.append(mat)
 copies.append(bpy.data.objects.new(n+' — baked v32',mesh))
es=bpy.data.scenes.new('Complete character export v32');bpy.context.window.scene=es
for o in copies:es.collection.objects.link(o);o.select_set(True)
bpy.context.view_layer.objects.active=copies[0]
for fmt,ext in [('GLTF_SEPARATE','gltf'),('GLB','glb')]:bpy.ops.export_scene.gltf(filepath=str(W/f'suzume-posed-v32.{ext}'),export_format=fmt,use_selection=True,use_active_scene=True,export_animations=False,export_cameras=False,export_lights=False)
report={'revision':32,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'reopened':True,'dimensionsInvariantAtFiveAngles':True,'dayNightDoorMatricesMatch':True,'characterPartition':partition,'feet':a['footCollision'],'headGeometryPreserved':True,'partTriangles':{o.name:len(o.data.polygons) for o in copies},'browserRuntimeVerified':False,'oneToOneComplete':False}
(O/'verification-v32.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print('DOOR_32_REOPEN_AND_EXPORT_OK',json.dumps(report),flush=True)
