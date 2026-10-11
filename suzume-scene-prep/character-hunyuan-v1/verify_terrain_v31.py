"""Verify saved geometry, contacts, realm membership and actual mesh skyline."""
from pathlib import Path
import bpy,json,sys,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).parent;O=R/'movie-terrain-v31';sys.path.insert(0,str(R));from night_audit_v30 import fingerprint,topology,material_digest,closed_mesh
bpy.ops.wm.open_mainfile(filepath=str(O/'Suzume_scene_movie_terrain_v31.blend'));s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72);bpy.context.view_layer.update();a=json.loads((O/'integration-v31.json').read_text(encoding='utf-8'));q=a['parameters']
for name,digest in a['allDayMeshHashes'].items():assert fingerprint(bpy.data.objects[name])==digest,name;assert topology(bpy.data.objects[name])==a['topologyHashes'][name],name
for name,row in a['oldNightMeshes'].items():
    if name!='Rolling meadow ground':assert fingerprint(bpy.data.objects[name])==row['worldHash'],name
    assert topology(bpy.data.objects[name])==row['topology'],name
for name,digest in a['oldMaterials'].items():assert material_digest(bpy.data.materials[name])==digest,name
for name,row in a['characters'].items():
    ob=bpy.data.objects[name];assert fingerprint(ob,True)==row['worldHash'];partner='Suzume Hunyuan entered portion' if name=='Suzume Hunyuan textured surface' else name+' — entered portion';other=bpy.data.objects[partner];assert ob.data==other.data
    assert all(sl.material.get('spatial_half')=='courtyard' for sl in ob.material_slots);assert all(sl.material.get('spatial_half')=='otherworld' for sl in other.material_slots)
ground=bpy.data.objects['Rolling meadow ground'];ext=bpy.data.objects['Continuous distant meadow v31'];assert fingerprint(ground)==a['groundWorldHash'];assert fingerprint(ext)==a['extensionWorldHash'];assert topology(ext)==a['extensionTopologyHash'];assert closed_mesh(ext)[1]
before=np.load(O/'original-ground-v31.npz');near=np.hypot(before['world'][:,0],before['world'][:,1])<=q['unchangedNearRadius'];local=np.array([v.co[:] for v in ground.data.vertices],np.float32);assert np.array_equal(local[near],before['local'][near])
realm=bpy.data.collections['Editable night realm'];night=bpy.data.scenes['Night meadow through the door'];assert realm in night.collection.children[:];assert bpy.data.objects['Night realm reached through the door'].instance_collection==realm
for name in a['newObjects']:assert realm in bpy.data.objects[name].users_collection[:]
for i,row in enumerate(q['fogVolumes']):
    ob=bpy.data.objects['Low meadow mist v31 '+str(i)];assert closed_mesh(ob)==(8,True);assert np.allclose(ob.matrix_world.translation,row['center']);assert np.allclose(ob.scale,row['halfSize'])
    ns=ob.data.materials[0].node_tree.nodes;assert abs(ns['Low mist density v31'].inputs[1].default_value-q['fogDensity']*row['weight'])<1e-7;assert not any(n.type=='TEX_IMAGE' for n in ns);out=next(n for n in ns if n.type=='OUTPUT_MATERIAL');assert out.inputs['Volume'].is_linked and not out.inputs['Surface'].is_linked
    volume=out.inputs['Volume'].links[0].from_node;color=volume.inputs['Emission Color'].links[0].from_node;assert color.bl_idname=='ShaderNodeCombineXYZ'
    for k in range(3):
        addition=color.inputs[k].links[0].from_node;scale=addition.inputs[1].links[0].from_node;assert addition.operation=='ADD' and scale.operation=='MULTIPLY';assert abs(addition.inputs[0].default_value-q['fogLeftLinear'][k])<1e-7;assert abs(scale.inputs[1].default_value-(q['fogRightLinear'][k]-q['fogLeftLinear'][k]))<1e-7
    gain=ns['Low mist density v31'].inputs[0].links[0].from_node.inputs[1].links[0].from_node;assert gain.operation=='ADD';assert abs(gain.inputs[0].default_value-q['fogLateralGain'][0])<1e-7
assert a['camera']=={'matrix':[list(row) for row in s.camera.matrix_world],'lens':s.camera.data.lens}
# Build BVH from actual saved triangulated terrain, not the fitting function.
vertices=[];polygons=[]
for ob in [ground,ext]:
    base=len(vertices);vertices.extend([ob.matrix_world@v.co for v in ob.data.vertices]);polygons.extend([tuple(base+i for i in p.vertices) for p in ob.data.polygons])
bvh=BVHTree.FromPolygons(vertices,polygons,all_triangles=True);P=q['referenceCamera'];C=Vector((P['cameraX'],-P['distance'],P['cameraZ']));f=1656*P['lensMm']/36;c=np.cos(P['pitch']);sn=np.sin(P['pitch']);rows=[]
def hits(px,py):
    up=(828-py)/f;direction=Vector(((px-1276)/f,c+up*sn,-sn+up*c));direction.normalize();return bvh.ray_cast(C,direction,1000)[0] is not None
for px,target in q['manualSkylineAnchors']:
    lo,hi=570.,690.;assert not hits(px,lo) and hits(px,hi)
    for _ in range(20):
        mid=(lo+hi)/2
        if hits(px,mid):hi=mid
        else:lo=mid
    rows.append({'referencePixel':[px,target],'meshSkylineY':hi,'errorPixels':hi-target})
error=max(abs(r['errorPixels']) for r in rows);assert error<3,rows
v=np.array([p.co[:] for p in ext.data.vertices]);tri=np.array([p.vertices[:] for p in ext.data.polygons]);volume=float(np.einsum('ij,ij->i',v[tri[:,0]],np.cross(v[tri[:,1]],v[tri[:,2]])).sum()/6);assert volume>0
result={'revision':31,'freshReopenVerified':True,'preservedDayMeshes':len(a['allDayMeshHashes']),'oldNightMeshesExceptGroundPreserved':len(a['oldNightMeshes'])-1,'oldMaterialGraphsPreserved':len(a['oldMaterials']),'nearGroundVerticesExactlyPreserved':int(near.sum()),'nearRadius':q['unchangedNearRadius'],'bodyHeadFeetAndPortalPreserved':True,'newObjectsSharedWithPortalRealm':True,'closedTerrainExtension':True,'extensionSignedVolume':volume,'actualMeshSkylineSamples':rows,'maximumAnnotatedSkylineErrorPixels':error,'fogVolumes':2,'referenceImageUsedInTerrainOrFog':False,'oneToOneComplete':False}
(O/'verification-v31.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print('TERRAIN_31_VERIFIED',json.dumps(result),flush=True)
if '--trial' in sys.argv:
    s.render.resolution_x=960;s.render.resolution_y=624;s.render.resolution_percentage=100;s.cycles.samples=12;s.cycles.use_denoising=True;s.render.use_persistent_data=True
    s.render.use_border=True;s.render.use_crop_to_border=True;s.render.border_min_x=.36;s.render.border_max_x=.58;s.render.border_min_y=.37;s.render.border_max_y=.71
    s.render.filepath=str(O/'trial-horizon-and-mist-v31.png');bpy.ops.render.render(write_still=True);print('TERRAIN_31_TRIAL_DONE',flush=True)
if '--render' in sys.argv:
    s.render.use_border=False;s.render.use_crop_to_border=False;s.render.resolution_x=720;s.render.resolution_y=468;s.render.resolution_percentage=100;s.cycles.samples=24;s.cycles.use_denoising=True
    s.render.filepath=str(O/'movie-front-v31.png');bpy.ops.render.render(write_still=True);print('TERRAIN_31_FRONT_DONE',flush=True)
    bpy.context.window.scene=night;night.timeline_markers.clear();night.frame_set(72);cam=s.camera.copy();cam.data=s.camera.data.copy();cam.animation_data_clear();cam.data.animation_data_clear();night.collection.objects.link(cam);night.camera=cam;cam.location=(-18,22,5.5);target=Vector((0,230,13));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=45
    night.render.use_border=False;night.render.use_crop_to_border=False;night.render.resolution_x=720;night.render.resolution_y=468;night.render.resolution_percentage=100;night.cycles.samples=24;night.cycles.use_denoising=True
    night.render.filepath=str(O/'night-wide-v31.png');bpy.ops.render.render(write_still=True);print('TERRAIN_31_WIDE_DONE',flush=True)
