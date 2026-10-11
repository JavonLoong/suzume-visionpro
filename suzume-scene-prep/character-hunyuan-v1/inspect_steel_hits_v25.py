from pathlib import Path
import bpy,math,json
from mathutils import Vector
R=Path(__file__).parent;O=R/'movie-steel-v25'
bpy.ops.wm.open_mainfile(filepath=str(O/'Suzume_scene_movie_steel_v25.blend'))
s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72);bpy.context.view_layer.update();camera=s.camera;rows=[]
for x,y in [(116,100),(119,150),(123,150),(524,100),(527,100),(531,100),(524,180),(527,180),(531,180)]:
    v=Vector(((x/720-.5)*2*(720/468)*18/camera.data.lens,(.5-y/468)*2*18/camera.data.lens,-1));v=camera.matrix_world.to_3x3()@v;v.normalize()
    hit,loc,normal,face,obj,mat=s.ray_cast(bpy.context.evaluated_depsgraph_get(),camera.location,v,distance=100)
    material=obj.data.materials[obj.data.polygons[face].material_index] if hit else None
    rows.append({'pixel':[x,y],'object':obj.name if hit else None,'point':list(loc) if hit else None,'material':material.name if material else None})
(O/'pixel-hit-inspection-v25.json').write_text(json.dumps(rows,indent=2),encoding='utf-8');print(json.dumps(rows,indent=2))
