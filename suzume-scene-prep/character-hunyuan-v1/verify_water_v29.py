"""Reopen water candidate, check actual nodes and preserved geometry, render views."""
from pathlib import Path
import bpy,json,sys,hashlib,math,numpy as np
from mathutils import Vector
R=Path(__file__).parent;O=R/'movie-water-v29';sys.path.insert(0,str(R));from projection_geometry_v24 import bay_spec,center,height
bpy.ops.wm.open_mainfile(filepath=str(O/'Suzume_scene_movie_water_v29.blend'))
s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72);bpy.context.view_layer.update()
a=json.loads((O/'integration-v29.json').read_text(encoding='utf-8'));q=a['parameters']
def fingerprint(ob,evaluated=False):
    e=ob.evaluated_get(bpy.context.evaluated_depsgraph_get()) if evaluated else ob;m=e.to_mesh() if evaluated else ob.data
    v=np.empty((len(m.vertices),3),np.float32);m.vertices.foreach_get('co',v.ravel());M=np.array(ob.matrix_world);v=v@M[:3,:3].T+M[:3,3]
    if evaluated:e.to_mesh_clear()
    return hashlib.sha256(np.round(v,6).astype('<f4').tobytes()).hexdigest()
for name,value in a['allDayMeshHashes'].items():
    ob=bpy.data.objects[name];assert fingerprint(ob)==value,name
    indices=np.empty(len(ob.data.loops),np.int32);ob.data.loops.foreach_get('vertex_index',indices);counts=np.empty(len(ob.data.polygons),np.int32);ob.data.polygons.foreach_get('loop_total',counts)
    assert hashlib.sha256(indices.astype('<i4').tobytes()+counts.astype('<i4').tobytes()).hexdigest()==a['topologyHashes'][name],name
assert len([o for o in s.objects if o.type=='MESH'])==len(a['allDayMeshHashes'])
for name,row in a['characters'].items():
    ob=bpy.data.objects[name];assert fingerprint(ob,True)==row['worldHash'],name
    partner='Suzume Hunyuan entered portion' if name=='Suzume Hunyuan textured surface' else name+' — entered portion';other=bpy.data.objects[partner];assert ob.data==other.data
    assert all(sl.material.get('spatial_half')=='courtyard' for sl in ob.material_slots);assert all(sl.material.get('spatial_half')=='otherworld' for sl in other.material_slots)
assert a['camera']=={'matrix':[list(row) for row in s.camera.matrix_world],'lens':s.camera.data.lens}
for row in json.loads((R/'movie-lighting-v27/integration-v27.json').read_text())['lights']:
    ob=bpy.data.objects[row['name']];assert np.allclose(ob.matrix_world.translation,row['worldPosition'],atol=1e-5);assert abs(ob.data.energy-row['power'])<1e-5;assert np.allclose(ob.data.color,row['color'],atol=1e-5)
surfaces=json.loads((R/'movie-surfaces-v28/integration-v28.json').read_text(encoding='utf-8'))
for row in surfaces['selectedObjects']:
    ob=bpy.data.objects[row['object']];assert [p.index for p in ob.data.polygons if p.material_index==row['paintedMaterialIndex']]==row['polygons'];assert ob.data.materials[row['paintedMaterialIndex']].get('film_surface_revision')==28
nodes=s.objects['Live planar reflective shallow water'].data.materials[0].node_tree.nodes
close=lambda x,y:np.allclose(x,y,rtol=1e-6,atol=1e-7)
assert close(nodes['Tinted water reflection'].inputs['Roughness'].default_value,q['reflectionRoughness'])
assert close(nodes['Tinted water reflection'].inputs['Base Color'].default_value[:3],q['reflectionTint'])
assert close(nodes['Shallow blue green transmission'].inputs['Color'].default_value[:3],q['transmissionTint'])
assert close(nodes['Shallow blue green transmission'].inputs['IOR'].default_value,1.333)
assert close(nodes['Shallow blue green transmission'].inputs['Roughness'].default_value,q['transmissionRoughness'])
fres=nodes['Artistic reflection balance'];addition=fres.inputs[1].links[0].from_node;power=addition.inputs[0].links[0].from_node
assert close(fres.inputs[0].default_value,q['fresnel'][0]);assert close(addition.inputs[1].default_value,q['fresnel'][1]);assert close(power.inputs[1].default_value,q['fresnelPower'])
weights=q['fresnel'][0]+q['fresnel'][1]*(1-np.linspace(0,1,101))**q['fresnelPower'];assert np.all((weights>=0)&(weights<=1));assert np.all(np.diff(weights)<=0)
assert close(nodes['Shallow water shadow transmission v29'].inputs['Color'].default_value[:3],q['shadowTransmission'])
assert close(nodes['Water optical depth v29'].inputs[0].default_value,q['hazeOpticalDepth']);assert close(nodes['Water scatter strength v29'].inputs[1].default_value,q['hazeStrength']);assert close(nodes['Blue shallow water scattering v29'].inputs['Color'].default_value[:3],q['hazeColorLinear'])
assert nodes['Water surface'].inputs['Surface'].links[0].from_node.name=='Shallow water scatter blend v29'
assert not any(n.type=='TEX_IMAGE' for n in nodes)
for i,base in enumerate([.0018,.00065,.00022],1):assert close(nodes['Wave height '+str(i)].inputs[1].default_value,base*q['rippleAmplitudeScale'])
for name in a['submergedAlgaeMaterials']:
    ns=bpy.data.materials[name].node_tree.nodes;assert close(ns['Bed algae amount v29'].inputs[1].default_value,q['algaeStrength']);assert ns['Submerged stone world position v29'].type=='NEW_GEOMETRY'
times=[];door=[]
for frame in [1,24,72,120]:s.frame_set(frame);bpy.context.view_layer.update();times.append(nodes['Wave time'].outputs[0].default_value);door.append(bpy.data.lights['Daylight entering the open doorway v19'].energy)
assert close(times,[(f-1)/24 for f in [1,24,72,120]]);assert door==[0,0,15,15];s.frame_set(72)
result={'revision':29,'freshReopenVerified':True,'allDayMeshGeometryAndTopologyPreserved':len(a['allDayMeshHashes']),'characterHeadFeetAndPortalPreserved':True,'cameraAndLightingPreserved':True,'physicalWallProjectionPreserved':28,'liveReflectionAndRefractionNodesVerified':True,'shallowShadowTransmissionAndScatterVerified':True,'referenceImageUsedInWater':False,'submergedAlgaeMaterialCount':len(a['submergedAlgaeMaterials']),'waterAnimationTimes':times,'doorLightByFrame':dict(zip([1,24,72,120],door)),'oneToOneComplete':False}
(O/'verification-v29.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print('WATER_29_REOPEN_VERIFIED',json.dumps(result),flush=True)
if '--render' in sys.argv:
    s.render.use_border=False;s.render.use_crop_to_border=False;s.render.resolution_x=720;s.render.resolution_y=468;s.render.resolution_percentage=100;s.cycles.samples=32;s.cycles.use_denoising=True;s.render.use_persistent_data=True
    s.render.filepath=str(O/'movie-front-v29.png');bpy.ops.render.render(write_still=True)
    b=bay_spec(13);angle=b['angle'];n=Vector((-math.sin(angle),-math.cos(angle),0));t=Vector((math.cos(angle),-math.sin(angle),0));target=Vector((b['chordRadius']*math.sin(angle)+center[0],b['chordRadius']*math.cos(angle)+center[1],float(height(3.5,13))))
    s.timeline_markers.clear();cam=s.camera.copy();cam.data=s.camera.data.copy();cam.animation_data_clear();cam.data.animation_data_clear();s.collection.objects.link(cam);s.camera=cam
    cam.location=target+n*12+t*8+Vector((0,0,5));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=28
    s.render.filepath=str(O/'movie-left-oblique-v29.png');bpy.ops.render.render(write_still=True)
