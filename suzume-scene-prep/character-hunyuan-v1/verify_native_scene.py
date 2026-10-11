import bpy,json,numpy as np,math,sys
from pathlib import Path
from mathutils import Vector
R=Path(__file__).parent;V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
bpy.ops.wm.open_mainfile(filepath=str(V/'suzume-full-scene-hunyuan-v14.blend'))
s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s
mesh=bpy.data.objects['Suzume Hunyuan textured surface'];rig=bpy.data.objects['Suzume Hunyuan rig']
s.frame_set(1);closed_hidden=mesh.hide_render
s.frame_set(72);open_visible=not mesh.hide_render
assert closed_hidden and open_visible
ev=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get());P=np.empty((len(ev.data.vertices),3),np.float32);ev.data.vertices.foreach_get('co',P.ravel());M=np.asarray(mesh.matrix_world);world=P@M[:3,:3].T+M[:3,3]
grip=np.array(rig['Right palm contact world']);distance=np.linalg.norm(world-grip,axis=1)
images=[{'name':i.name,'packed':bool(i.packed_file),'pixels':list(i.size)} for i in bpy.data.images if i.name.startswith('texture_pbr')]
assert len(images)==3 and all(i['packed'] and i['pixels']==[4096,4096] for i in images)
audit=json.loads((R/'integration-audit.json').read_text());audit.update({'reopenedSuccessfully':True,'closedFrameHidden':closed_hidden,'openFrameVisible':open_visible,'closestSurfaceToKnob':float(distance.min()),'characterBounds':[[float(v) for v in world.min(0)],[float(v) for v in world.max(0)]],'packedCharacterImages':images,'visualReview':'Weights corrected after front/side studio inspection; native scene render pending.'})
(R/'integration-audit.json').write_text(json.dumps(audit,indent=2))
print('REOPEN_CHECK',json.dumps(audit),flush=True)
s.camera=bpy.data.objects['Door front camera'];s.render.resolution_x=800;s.render.resolution_y=520;s.render.resolution_percentage=100;s.cycles.samples=16;s.cycles.use_denoising=True
if '--side-only' not in sys.argv:
 s.render.filepath=str(R/'scene-open-front-v14.png');bpy.ops.render.render(write_still=True)
s.camera.location=(-1.7,-6.8,1.6);s.camera.rotation_euler=(Vector((0,.1,1.75))-s.camera.location).to_track_quat('-Z','Y').to_euler()
s.cycles.use_denoising=False
s.render.filepath=str(R/'scene-open-side-v14.png');bpy.ops.render.render(write_still=True)
print('NATIVE_VERIFY_COMPLETE',flush=True)
