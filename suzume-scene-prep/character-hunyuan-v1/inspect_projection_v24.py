from pathlib import Path
import bpy,json,numpy as np
R=Path(__file__).parent;O=R/'movie-projection-v24';O.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'movie-bays-v23/Suzume_scene_movie_bays_v23.blend'))
s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72);bpy.context.view_layer.update()
rows=[]
for o in s.objects:
    if any(q in o.name.lower() for q in ['door front camera','six-panel','door leaf','doorframe','door frame','portal aperture']):
        rows.append({'name':o.name,'type':o.type,'matrix':np.array(o.matrix_world).tolist(),'vertices':len(o.data.vertices) if o.type=='MESH' else None,'bounds':[(o.matrix_world@__import__('mathutils').Vector(c)).to_tuple() for c in o.bound_box] if o.type=='MESH' else None})
camera=s.camera
result={'camera':{'name':camera.name,'lens':camera.data.lens,'sensorHeight':camera.data.sensor_height,'sensorFit':camera.data.sensor_fit,'matrix':np.array(camera.matrix_world).tolist()},'objects':rows}
(O/'source-inspection-v24.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
