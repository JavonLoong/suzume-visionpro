"""Extend the existing ponytail and keep its lower volume behind the real shirt."""
from pathlib import Path
import bpy,numpy as np,json,hashlib,sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
R=Path(__file__).parent;O=R/'movie-hair-v33';sys.path.insert(0,str(R));from night_audit_v30 import fingerprint,topology
source=R/'movie-door-v32/Suzume_scene_movie_door_v32.blend';bpy.ops.wm.open_mainfile(filepath=str(source));s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72)
o=bpy.data.objects['Suzume independent Hunyuan head'];body=bpy.data.objects['Suzume Hunyuan textured surface'];data=np.load(O/'hair-deformation-v33.npz');fit=json.loads((O/'hair-fit-v33.json').read_text());original=np.load(O/'head-source-v33.npz');old=np.array([v.co[:] for v in o.data.vertices]);assert np.max(abs(old-original['local']))<1e-8
def world(ob):
 e=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();v=np.array([p.co[:] for p in m.vertices]);M=np.asarray(ob.matrix_world);v=v@M[:3,:3].T+M[:3,3];e.to_mesh_clear();return v
bodyhash=fingerprint(body,True);oldtopo=topology(o);pins={n:fingerprint(bpy.data.objects[n],True) for n in ['Left gold hairpin','Left red hairpin diagonal','Left red hairpin crossbar']}
colors=o.data.color_attributes[0];color_before=np.array([c.color[:] for c in colors.data]);p=data['local'].copy();mask=data['mask'];o.data.vertices.foreach_set('co',p.ravel());o.data.update();bpy.context.view_layer.update();w=world(o)
e=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();bv=np.array([v.co[:] for v in m.vertices]);M=np.asarray(body.matrix_world);bv=bv@M[:3,:3].T+M[:3,3];bf=[tuple(f.vertices) for f in m.polygons];e.to_mesh_clear();tree=BVHTree.FromPolygons(bv,bf,all_triangles=True)
# A height profile translates each lower cross-section as a whole, retaining its
# thickness. Ray hits are from behind the character towards the actual back cloth.
selected=np.flatnonzero((mask>.95)&(w[:,2]<2.65));deficit=np.zeros(len(w));hits={}
for i in selected:
 hit,normal,_,_=tree.ray_cast(Vector((w[i,0],-2,w[i,2])),Vector((0,1,0)),4)
 if hit is not None and normal.y<-.15:
  hits[int(i)]=hit.y;deficit[i]=max(0,w[i,1]-(hit.y-.018))
# A global C1 curve starts at the root, rather than bending abruptly at the
# first shirt collision. Choose its amplitude from all actual clearance rays.
phase=np.clip((3.01-w[:,2])/(3.01-2.13),0,1);curve=phase*phase*(3-2*phase)*mask
amplitude=float(np.max(deficit[selected]/np.maximum(curve[selected],1e-8)))+.004
shift=amplitude*curve
p[:,1]+=shift/2.9325;o.data.vertices.foreach_set('co',p.ravel());o.data.update();bpy.context.view_layer.update();after=world(o)
# The tip's depth correction changes projection slightly. Fit its X/Z to the
# measured image ray while retaining the newly established rear clearance.
tip=fit['tipVertex'];target=fit['targetTipPixels'];s.render.resolution_x=2552;s.render.resolution_y=1656
def pixel(v):
 q=world_to_camera_view(s,s.camera,Vector(v));return np.array([q.x*2552,(1-q.y)*1656])
base_tip=after[tip].copy();eps=.001;J=np.column_stack([(pixel(base_tip+np.eye(3)[axis]*eps)-pixel(base_tip))/eps for axis in [0,2]])
delta=np.linalg.solve(J,np.asarray(target)-pixel(base_tip));progress=np.maximum(.6-original['original'][:,2],0)/max(.001,.6-original['original'][tip,2]);weight=mask*progress**2
p[:,0]-=delta[0]*weight/2.9325;p[:,2]+=delta[1]*weight/2.9325;o.data.vertices.foreach_set('co',p.ravel());o.data.update();bpy.context.view_layer.update();after=world(o)
clear=[]
for i in selected:
 hit,normal,_,_=tree.ray_cast(Vector((after[i,0],-2,after[i,2])),Vector((0,1,0)),4)
 if hit is not None and normal.y<-.15:clear.append(float(hit.y-after[i,1]))
assert not clear or min(clear)>.01,min(clear)
assert fingerprint(body,True)==bodyhash and topology(o)==oldtopo
assert np.array_equal(color_before,np.array([c.color[:] for c in colors.data]))
for n,h in pins.items():assert fingerprint(bpy.data.objects[n],True)==h
face=original['original'][:,1]<=.225;face_delta=float(np.linalg.norm(after[face]-original['world'][face],axis=1).max());assert face_delta<1e-6
partner=bpy.data.objects[o.name+' — entered portion'];assert o.data==partner.data
for part,half in [(o,'courtyard'),(partner,'otherworld')]:assert part.material_slots[0].material['spatial_half']==half
o['hair_revision']=33;o['hair_calibration']='Localized ponytail extension and rear clearance based on the opening-frame tip. Face, eyes, hairpins and scalp front unchanged.'
report={'revision':33,'sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'headHash':fingerprint(o,True),'topologyHash':oldtopo,'bodyHashPreserved':bodyhash,'pinsPreserved':pins,'vertexColorsUnchanged':True,'faceFrontMaximumVertexChange':face_delta,'tipVertex':tip,'tipTargetPixels':target,'actualTipPixels':pixel(after[tip]).tolist(),'tipPixelError':float(np.linalg.norm(pixel(after[tip])-target)),'tipWorld':after[tip].tolist(),'maximumRearShift':float(shift.max()),'rearCurve':{'type':'continuous cubic smoothstep','startWorldZ':3.01,'endWorldZ':2.13,'amplitude':amplitude},'shirtRayClearanceSamples':len(clear),'minimumHairToBackClothGap':min(clear) if clear else None,'clearanceScope':'Backwards Y separation from actual back-facing body triangles for the lower ponytail, not a full collision proof.','sharedDayNightMesh':True,'oneToOneComplete':False}
np.savez_compressed(O/'integrated-hair-v33.npz',before=original['world'],after=after,mask=mask,local=p)
(O/'integration-v33.json').write_text(json.dumps(report,indent=2));s.render.resolution_x=720;s.render.resolution_y=468;s.render.resolution_percentage=100
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Suzume_scene_movie_hair_v33.blend'));print('HAIR_33_SAVED',json.dumps(report),flush=True)
