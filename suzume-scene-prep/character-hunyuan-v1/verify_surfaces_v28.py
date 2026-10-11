"""Fresh-file preservation checks and two views of the fixed surface treatment."""
from pathlib import Path
import bpy,sys,json,hashlib,math,numpy as np
from mathutils import Vector
R=Path(__file__).parent;O=R/'movie-surfaces-v28';sys.path.insert(0,str(R))
from projection_geometry_v24 import bay_spec,center,height
bpy.ops.wm.open_mainfile(filepath=str(O/'Suzume_scene_movie_surfaces_v28.blend'))
s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72);bpy.context.view_layer.update()
audit=json.loads((O/'integration-v28.json').read_text(encoding='utf-8'))
def fingerprint(ob,evaluated=False):
    e=ob.evaluated_get(bpy.context.evaluated_depsgraph_get()) if evaluated else ob;m=e.to_mesh() if evaluated else ob.data
    a=np.empty((len(m.vertices),3),np.float32);m.vertices.foreach_get('co',a.ravel());M=np.array(ob.matrix_world);a=a@M[:3,:3].T+M[:3,3]
    if evaluated:e.to_mesh_clear()
    return hashlib.sha256(np.round(a,6).astype('<f4').tobytes()).hexdigest()
def topology(ob):
    indices=np.empty(len(ob.data.loops),np.int32);ob.data.loops.foreach_get('vertex_index',indices)
    counts=np.empty(len(ob.data.polygons),np.int32);ob.data.polygons.foreach_get('loop_total',counts)
    return hashlib.sha256(indices.astype('<i4').tobytes()+counts.astype('<i4').tobytes()).hexdigest()
for name,value in audit['allDayMeshHashes'].items():assert fingerprint(bpy.data.objects[name])==value,name
for name,value in audit['topologyHashes'].items():assert topology(bpy.data.objects[name])==value,name
assert len([o for o in s.objects if o.type=='MESH'])==len(audit['allDayMeshHashes'])
for name,row in audit['characters'].items():
    ob=bpy.data.objects[name];assert fingerprint(ob,True)==row['worldHash'],name
    partner='Suzume Hunyuan entered portion' if name=='Suzume Hunyuan textured surface' else name+' — entered portion';other=bpy.data.objects[partner];assert ob.data==other.data
    assert all(sl.material.get('spatial_half')=='courtyard' for sl in ob.material_slots);assert all(sl.material.get('spatial_half')=='otherworld' for sl in other.material_slots)
assert audit['camera']=={'matrix':[list(row) for row in s.camera.matrix_world],'lens':s.camera.data.lens}
for row in audit['selectedObjects']:
    ob=bpy.data.objects[row['object']];actual=[p.index for p in ob.data.polygons if p.material_index==row['paintedMaterialIndex']];assert actual==row['polygons'],ob.name
    assert ob.data.materials[row['paintedMaterialIndex']].get('original_material')==row['originalMaterial']
source=bpy.data.images['Film source v28 — unchanged'];assert source.packed_file and hashlib.sha256(source.packed_file.data).hexdigest()==audit['sourceSha256']
lut=bpy.data.images['Signed inverse AgX data v28'];assert lut.packed_file and lut.colorspace_settings.name=='Non-Color'
pixels=np.empty(len(lut.pixels),np.float32);lut.pixels.foreach_get(pixels);expected=np.load(O/'inverse-agx-lut-v28.npy').ravel();assert np.allclose(pixels,expected,rtol=1e-6,atol=1e-6);assert pixels.min()<0
assert bpy.data.images['Film foreground exclusion v28'].packed_file
group=bpy.data.node_groups['Film v28 fixed world pigments'];assert any(n.type=='NEW_GEOMETRY' for n in group.nodes);assert not any(n.type in ['CAMERA','TEX_COORD'] for n in group.nodes)
lighting=json.loads((R/'movie-lighting-v27/integration-v27.json').read_text(encoding='utf-8'))
for row in lighting['lights']:
    ob=bpy.data.objects[row['name']];assert np.allclose(ob.matrix_world.translation,row['worldPosition'],atol=1e-5);assert abs(ob.data.energy-row['power'])<1e-5;assert np.allclose(ob.data.color,row['color'],atol=1e-5)
values=[]
for frame in [1,24,72,120]:s.frame_set(frame);bpy.context.view_layer.update();values.append(bpy.data.lights['Daylight entering the open doorway v19'].energy)
assert values==[0,0,15,15];s.frame_set(72)
result={'revision':28,'freshReopenVerified':True,'allDayMeshGeometryAndTopologyUnchanged':len(audit['allDayMeshHashes']),'characterHeadFeetAndPortalPreserved':True,'cameraAndLightsPreserved':True,'fixedWorldProjection':True,'selectedPhysicalObjects':len(audit['selectedObjects']),'selectedPolygons':audit['selectedPolygonCount'],'newSurfaceGeometryCount':0,'sourceImagePackedUnmodified':True,'signedColorLutPackedAndReopened':True,'lutPixelMaxAbsError':float(np.max(np.abs(pixels-expected))),'doorLightByFrame':dict(zip([1,24,72,120],values)),'oneToOneComplete':False}
(O/'verification-v28.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print('SURFACES_28_REOPEN_VERIFIED',json.dumps(result),flush=True)
if '--render' in sys.argv:
    s.render.use_border=False;s.render.resolution_x=720;s.render.resolution_y=468;s.render.resolution_percentage=100;s.cycles.samples=24;s.cycles.use_denoising=True;s.render.use_persistent_data=True
    s.render.filepath=str(O/'movie-front-v28.png');bpy.ops.render.render(write_still=True)
    b=bay_spec(13);a=b['angle'];n=Vector((-math.sin(a),-math.cos(a),0));t=Vector((math.cos(a),-math.sin(a),0));target=Vector((b['chordRadius']*math.sin(a)+center[0],b['chordRadius']*math.cos(a)+center[1],float(height(3.5,13))))
    s.timeline_markers.clear();camera=s.camera.copy();camera.data=s.camera.data.copy();camera.animation_data_clear();camera.data.animation_data_clear();s.collection.objects.link(camera);s.camera=camera
    camera.location=target+n*12+t*8+Vector((0,0,5));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.lens=28
    s.render.filepath=str(O/'movie-left-oblique-v28.png');bpy.ops.render.render(write_still=True)
