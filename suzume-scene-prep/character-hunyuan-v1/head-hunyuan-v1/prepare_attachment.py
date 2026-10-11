"""Prepare a reversible head/body seam; this is not the replacement head."""
import bpy,bmesh,numpy as np,json
from pathlib import Path
R=Path(__file__).parent;C=R.parent
bpy.ops.wm.open_mainfile(filepath=str(C/'Suzume_Hunyuan31_rigged.blend'))
mesh=bpy.data.objects['Suzume Hunyuan textured surface'];rig=bpy.data.objects['Suzume Hunyuan rig']
P=np.empty((len(mesh.data.vertices),3),np.float32);mesh.data.vertices.foreach_get('co',P.ravel())
rgb=np.load(C/'character-vertex-albedo.npy').astype(float)
z=P[:,2];ax=abs(P[:,0])
hair_region=(z>.975)|((z>.855)&(P[:,1]>.035)&(ax<.082))|((z>.925)&(ax<.085))
hair=(rgb.max(axis=1)<145)&(rgb[:,0]>rgb[:,1]*1.01)&hair_region
skin=(rgb[:,0]>rgb[:,1]*1.07)&(rgb[:,1]>rgb[:,2]*1.04)&(rgb[:,0]>115)
head_mask=(z>.984)|hair|(skin&(z>.951)&(abs(P[:,0])<.070))
# Smooth interpolation is deferred to the imported replacement neck. The seam
# sits within the uniform collar, which remains on the body side.
guide={'stage':'attachment_prepared_replacement_not_yet_generated','source':'Suzume_Hunyuan31_rigged.blend','meshRestAxes':'Blender Z up; face toward -Y; character left is +X','headVertexSelection':int(head_mask.sum()),'headBoundsRest':{'min':P[head_mask].min(axis=0).tolist(),'max':P[head_mask].max(axis=0).tolist()},'collarSeamRestZ':.951,'preserve':'White collar, red ribbon, torso weights, 20-bone rig and original UVs','headBone':'head','neckBone':'neck','sceneV16RigTransform':{'location':[-.15,.75,.055],'rotationZ':3.141592653589793,'scale':2.55,'headPoseScale':1.15},'ringSamples':[],'oneToOneComplete':False}
for height in [.945,.951,.958,.968]:
 selected=(abs(z-height)<.004)&skin&(abs(P[:,0])<.070)
 points=P[selected]
 if len(points):guide['ringSamples'].append({'restZ':height,'count':len(points),'centerXY':np.median(points[:,:2],axis=0).tolist(),'boundsXY':np.percentile(points[:,:2],[5,95],axis=0).tolist()})
for ob in bpy.context.scene.objects:ob.select_set(False)
mesh.select_set(True);bpy.context.view_layer.objects.active=mesh;before_objects=set(bpy.data.objects)
bpy.ops.object.mode_set(mode='EDIT');bm=bmesh.from_edit_mesh(mesh.data);bm.verts.ensure_lookup_table()
for f in bm.faces:f.select_set(False)
for e in bm.edges:e.select_set(False)
for v in bm.verts:v.select_set(bool(head_mask[v.index]))
for f in bm.faces:
 if all(head_mask[v.index] for v in f.verts):f.select_set(True)
bmesh.update_edit_mesh(mesh.data)
bpy.ops.mesh.separate(type='SELECTED');bpy.ops.object.mode_set(mode='OBJECT')
head=next(o for o in bpy.context.scene.objects if o.type=='MESH' and o not in before_objects)
head.name='Original head — alignment reference only';mesh.name='Body — preserved uniform and neck socket'
head['replacement_status']='Original extracted head for alignment; independent Hunyuan reconstruction still pending.'
mesh['socket_status']='Collar retained; replace the reference head and blend the new neck inside the collar.'
guide['bodyTriangles']=len(mesh.data.polygons);guide['referenceHeadTriangles']=len(head.data.polygons)
assert guide['bodyTriangles']>100000 and guide['referenceHeadTriangles']>10000,guide
for ob in bpy.context.scene.objects:ob.select_set(False)
head.select_set(True);bpy.context.view_layer.objects.active=head
bpy.context.scene['purpose']='Reversible attachment preparation, not the finished replacement head.'
bpy.ops.wm.save_as_mainfile(filepath=str(R/'head-socket-preparation.blend'))
(R/'attachment-guide.json').write_text(json.dumps(guide,ensure_ascii=False,indent=2),encoding='utf-8')
print('HEAD_SOCKET_PREPARED',json.dumps(guide),flush=True)
from mathutils import Vector
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=12;s.cycles.use_denoising=True
s.render.resolution_x=640;s.render.resolution_y=880;s.render.resolution_percentage=100
cam_data=bpy.data.cameras.new('Head socket inspection');cam=bpy.data.objects.new(cam_data.name,cam_data);s.collection.objects.link(cam);s.camera=cam;cam_data.type='ORTHO'
for label,visible,center,scale in [('head-reference',head,(0,0,1.02),.42),('body-socket',mesh,(0,0,.53),1.13)]:
 head.hide_render=visible!=head;mesh.hide_render=visible!=mesh;cam_data.ortho_scale=scale
 cam.location=Vector(center)+Vector((0,-4,0));cam.rotation_euler=(Vector(center)-cam.location).to_track_quat('-Z','Y').to_euler()
 s.render.filepath=str(R/f'{label}.png');bpy.ops.render.render(write_still=True)
print('HEAD_SOCKET_RENDERED',flush=True)
