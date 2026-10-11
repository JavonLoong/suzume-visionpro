"""Compare physically consistent world-space illumination; do not save the source."""
from pathlib import Path
import bpy,json,sys
from mathutils import Vector,Matrix
R=Path(__file__).parent;O=R/'movie-lighting-v27';O.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'movie-shore-v26/Suzume_scene_movie_shore_v26.blend'))
s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72);bpy.context.view_layer.update()
sun=bpy.data.objects['DirectionalLight'];oldSunMatrix=sun.matrix_world.copy();bg=s.world.node_tree.nodes.get('Background')
names=['Soft courtyard fill on the movie facade v22','Cool courtyard fill on the left facade v23','Localized sunlight around the arched window v23']
variants=[
 {'name':'rebalance','worldStrength':.10,'sunEnergy':1.25,'sunWorldPosition':None,'rightFill':1800,'leftFill':64,'archSpot':600},
 {'name':'side-sun','worldStrength':.10,'sunEnergy':2.4,'sunWorldPosition':[-35,-10,32],'rightFill':0,'leftFill':128,'archSpot':600}
]
s.render.use_border=False;s.render.resolution_x=540;s.render.resolution_y=351;s.render.resolution_percentage=100;s.cycles.samples=12;s.cycles.use_denoising=True;s.render.use_persistent_data=True
audit=[]
for q in variants:
    bg.inputs['Strength'].default_value=q['worldStrength'];sun.data.energy=q['sunEnergy'];sun.matrix_world=oldSunMatrix
    if q['sunWorldPosition']:
        pos=Vector(q['sunWorldPosition']);sun.matrix_world=Matrix.Translation(pos)@(-pos).to_track_quat('-Z','Y').to_matrix().to_4x4()
    for name,key in zip(names,['rightFill','leftFill','archSpot']):bpy.data.lights[name].energy=q[key]
    bpy.data.lights[names[1]].color=(.45,.60,1.0)
    bpy.context.view_layer.update();q={**q,'actualSunWorldMatrix':[list(row) for row in sun.matrix_world],'actualSunToSource':list(sun.matrix_world.to_quaternion()@Vector((0,0,1))),'renderSize':[540,351],'samples':12}
    s.render.filepath=str(O/('trial-'+q['name']+'.png'));bpy.ops.render.render(write_still=True);audit.append(q);(O/'trial-lighting-v27.json').write_text(json.dumps(audit,indent=2),encoding='utf-8');print('LIGHTING_27_TRIAL_DONE',q['name'],flush=True)
