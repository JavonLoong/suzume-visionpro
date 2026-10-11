from pathlib import Path
import bpy,numpy as np,json
from mathutils import Vector
R=Path(__file__).parent;O=R/'poster-lower-clouds-v43';bpy.ops.wm.open_mainfile(filepath=str(O/'Suzume_dual_scene_lower_clouds_v43.blend'));s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1);s.camera.location=(-9,-12,4);s.camera.rotation_euler=(Vector((0,2,3))-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.lens=30;bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();rows=[]
for u,v in [[185,180],[215,180],[250,185],[275,185],[300,185],[290,175],[210,194]]:
    direction=s.camera.matrix_world.to_3x3()@Vector(((u-360)/390,(234-v)/390,-1));direction.normalize();hit,point,normal,face,obj,matrix=s.ray_cast(deps,s.camera.location,direction)
    row={'pixel':[u,v],'hit':hit,'name':obj.name if obj else None,'point':list(point)}
    if hit and obj.type=='MESH':
        row['polygon']=face;poly=obj.data.polygons[face];attr=obj.data.color_attributes.get('surface_color')
        if attr:row['linearVertexColors']=[list(attr.data[i].color) for i in poly.vertices]
    rows.append(row)
(O/'side-ray-diagnosis-v43.json').write_text(json.dumps(rows,indent=2),encoding='utf-8');print(json.dumps(rows,indent=2),flush=True)
