"""Editable scene rig for the untouched Hunyuan surface; original GLB retained."""
import bpy, math, json, numpy as np
from pathlib import Path
from mathutils import Vector, Matrix
R=Path(__file__).parent
bpy.ops.wm.open_mainfile(filepath=str(R/'Suzume_Hunyuan31.blend'))
s=bpy.context.scene
mesh=next(o for o in s.objects if o.type=='MESH')
mesh.name='Suzume Hunyuan textured surface'
# glTF nodes retain a Y-up-to-Z-up object transform. Bake that conversion
# before measuring local anatomy or attaching a Z-up skeleton.
mesh.data.transform(mesh.matrix_world);mesh.matrix_world=Matrix.Identity(4)
# Coordinates are measured in the imported, unscaled Z-up mesh.
spec={
 'root':((0,0,0),(0,0,.12),None),
 'pelvis':((0,0,.69),(0,0,.766),'root'),
 'spine':((0,0,.766),(0,0,.847),'pelvis'),
 'chest':((0,0,.847),(0,0,.938),'spine'),
 'neck':((0,0,.938),(0,0,.985),'chest'),
 'head':((0,0,.985),(0,0,1.135),'neck'),
}
for side,sign in [('R',-1),('L',1)]:
 spec.update({
  'upper_arm.'+side:((sign*.086,0,.918),(sign*.133,-.002,.760),'chest'),
  'forearm.'+side:((sign*.133,-.002,.760),(sign*.173,-.010,.620),'upper_arm.'+side),
  'hand.'+side:((sign*.173,-.010,.620),(sign*.180,-.014,.564),'forearm.'+side),
  'fingers.'+side:((sign*.180,-.014,.564),(sign*.181,-.012,.519),'hand.'+side),
  'thigh.'+side:((sign*.051,0,.690),(sign*.057,-.006,.350),'pelvis'),
  'shin.'+side:((sign*.057,-.006,.350),(sign*.061,.007,.069),'thigh.'+side),
  'foot.'+side:((sign*.061,.007,.069),(sign*.061,-.073,.026),'shin.'+side),
 })
ad=bpy.data.armatures.new('Suzume editable skeleton');rig=bpy.data.objects.new('Suzume Hunyuan rig',ad);s.collection.objects.link(rig)
bpy.context.view_layer.objects.active=rig;rig.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
for name,(a,b,parent) in spec.items():
 bone=ad.edit_bones.new(name);bone.head=a;bone.tail=b
 if parent:bone.parent=ad.edit_bones[parent]
bpy.ops.object.mode_set(mode='OBJECT');rig.show_in_front=True;ad.display_type='OCTAHEDRAL'
# Partition by actual separated arms, skirt and lower legs, then blend joints.
# Quantised weights avoid a Python operator for each of the 298k vertices.
P=np.empty((len(mesh.data.vertices),3),np.float32);mesh.data.vertices.foreach_get('co',P.ravel())
x,y,z=P.T;ax=np.abs(x);N=len(P);W={name:np.zeros(N,np.float32) for name in spec}
def ramp(a,b,v):
 t=np.clip((v-a)/(b-a),0,1);return t*t*(3-2*t)
head=ramp(.959,.985,z);head=np.maximum(head,((y>.045)&(z>.875)&(ax<.075)).astype(float))
arm_boundary=np.interp(z,[.49,.52,.56,.60,.64,.68,.72,.75,.78,.81,.84,.87,.90,.94],[.145,.143,.132,.128,.123,.110,.092,.080,.081,.074,.068,.063,.056,.044])
blend_width=.003+ramp(.79,.90,z)*.016
arm=ramp(arm_boundary-blend_width,arm_boundary+blend_width,ax)*(1-ramp(.909,.938,z))*ramp(.475,.500,z)
arm*=1-head
leg=(1-ramp(.425,.742,z))*(1-arm)*(1-head)
torso=np.clip(1-head-arm-leg,0,1)
W['head']=head
chest=ramp(.783,.887,z);neck=ramp(.925,.965,z)
W['pelvis']=torso*(1-ramp(.751,.807,z))
W['spine']=torso*ramp(.751,.807,z)*(1-chest)
W['chest']=torso*ramp(.751,.807,z)*chest*(1-neck)
W['neck']=torso*ramp(.751,.807,z)*chest*neck
for side,sign in [('R',-1),('L',1)]:
 mask=(x*sign>=0).astype(float)
 upper=ramp(.738,.780,z);hand=1-ramp(.603,.635,z);finger=1-ramp(.551,.579,z)
 W['upper_arm.'+side]=arm*mask*upper
 W['forearm.'+side]=arm*mask*(1-upper)*(1-hand)
 W['hand.'+side]=arm*mask*(1-upper)*hand*(1-finger)
 W['fingers.'+side]=arm*mask*(1-upper)*hand*finger
 thigh=ramp(.315,.385,z);foot=1-ramp(.055,.110,z)
 cloth_blend=ramp(.420,.450,z)
 leg_mask=mask*(1-cloth_blend)+ramp(-.030,.030,x*sign)*cloth_blend
 W['thigh.'+side]=leg*leg_mask*thigh
 W['shin.'+side]=leg*leg_mask*(1-thigh)*(1-foot)
 W['foot.'+side]=leg*leg_mask*(1-thigh)*foot
total=sum(W.values());assert np.min(total)>.98
for name,weights in W.items():
 weights/=total
 group=mesh.vertex_groups.new(name=name)
 quant=np.rint(weights*128).astype(np.int16)
 for q in np.unique(quant):
  if q:group.add(np.flatnonzero(quant==q).tolist(),int(q)/128,'REPLACE')
mod=mesh.modifiers.new('Anatomical character deformation','ARMATURE');mod.object=rig;mod.use_deform_preserve_volume=True
mesh.parent=rig
rig['workflow']='Consistent four views -> Hunyuan 3D 3.1 -> retained original mesh -> measured, editable skeleton.'
rig['limitations']='Reconstructed topology and grouped finger deformation; not production retopology or a film-original rig.'
for ob in s.objects:ob.select_set(False)
rig.select_set(True);bpy.context.view_layer.objects.active=rig
s['asset_status']='Packed textured Hunyuan model with editable 20-bone scene rig; neutral rest pose.'
bpy.ops.wm.save_as_mainfile(filepath=str(R/'Suzume_Hunyuan31_rigged.blend'))
(R/'rig-audit.json').write_text(json.dumps({'bones':len(spec),'vertices':N,'weightsMin':float(total.min()),'weightsMax':float(total.max()),'originalSurfaceRetained':True,'packedImages':all(im.packed_file for im in bpy.data.images if im.type=='IMAGE'),'rig':spec},indent=2))
print('RIG_COMPLETE',len(spec),N,flush=True)
