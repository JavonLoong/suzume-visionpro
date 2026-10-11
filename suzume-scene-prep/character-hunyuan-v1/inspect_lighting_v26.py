"""Read-only lighting evidence for the next movie appearance calibration."""
from pathlib import Path
import bpy,json,numpy as np
R=Path(__file__).parent;O=R/'movie-shore-v26'
bpy.ops.wm.open_mainfile(filepath=str(O/'Suzume_scene_movie_shore_v26.blend'))
s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72);bpy.context.view_layer.update()
def inputs(node):
    result={}
    for x in node.inputs:
        if not hasattr(x,'default_value'):continue
        v=x.default_value
        if isinstance(v,(int,float,str,bool)):result[x.name]=v
        else:
            try:result[x.name]=list(v)
            except TypeError:pass
    return result
result={'scene':s.name,'viewTransform':s.view_settings.view_transform,'exposure':s.view_settings.exposure,'look':s.view_settings.look,
        'lights':[{'name':o.name,'type':o.data.type,'location':list(o.location),'rotation':list(o.rotation_euler),'power':o.data.energy,'color':list(o.data.color),'size':getattr(o.data,'size',None),'sizeY':getattr(o.data,'size_y',None),'angle':getattr(o.data,'angle',None)}for o in s.objects if o.type=='LIGHT'],
        'worldNodes':[{'name':n.name,'type':n.type,'inputs':inputs(n)}for n in s.world.node_tree.nodes]}
(O/'lighting-state-v26.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print('LIGHTING_STATE_V26',result['viewTransform'],result['exposure'],len(result['lights']),flush=True)
