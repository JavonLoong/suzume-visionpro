from pathlib import Path
import bpy,json,numpy as np
from mathutils import Vector
R=Path(__file__).parent;O=R/'movie-door-v32';O.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'movie-terrain-v31/Suzume_scene_movie_terrain_v31.blend'))
s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72)
names=['Animated door leaf and hinges','Synchronized night door leaf']
res={'hinges':{},'bones':{},'sweep':[]}
for n in names:
 o=bpy.data.objects[n]
 res['hinges'][n]={'parent':o.parent.name,'parentScale':list(o.parent.scale),'location':list(o.location),'scale':list(o.scale),'inverse':[list(v) for v in o.matrix_parent_inverse],'children':len(o.children),'drivers':[{'path':d.data_path,'index':d.array_index,'expression':d.driver.expression} for d in o.animation_data.drivers] if o.animation_data else []}
for f in [1,36,48,60,72]:
 s.frame_set(f);bpy.context.view_layer.update();o=bpy.data.objects[names[0]];M=o.matrix_world
 res['sweep'].append({'frame':f,'angle':o.rotation_euler.y,'width':(M@Vector((1.6,0,0))-M@Vector((0,0,0))).length,'thickness':(M@Vector((0,0,.095))-M@Vector((0,0,0))).length})
s.frame_set(72);rig=bpy.data.objects['Suzume Hunyuan rig']
for n in ['upper_arm.R','forearm.R','hand.R','fingers.R']:
 b=rig.pose.bones[n];res['bones'][n]={'head':list(b.head),'tail':list(b.tail),'worldHead':list(rig.matrix_world@b.head),'worldTail':list(rig.matrix_world@b.tail),'matrix':[list(v) for v in b.matrix],'constraints':[c.type for c in b.constraints]}
res['rigProps']={k:v if isinstance(v,(str,float,int)) else list(v) for k,v in rig.items() if isinstance(v,(str,float,int)) or k=='Right palm contact world'}
tree=getattr(s,'compositing_node_group',None)
res['compositorNodes']=[{'type':n.bl_idname,'name':n.name} for n in tree.nodes] if tree else []
(O/'source-rig-v32.json').write_text(json.dumps(res,indent=2),encoding='utf-8');print(json.dumps(res),flush=True)
