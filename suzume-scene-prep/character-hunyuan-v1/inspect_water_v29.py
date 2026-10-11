"""Read the actual saved scene before changing the water optics."""
from pathlib import Path
import bpy,json,numpy as np,hashlib
from mathutils import Vector
R=Path(__file__).parent;O=R/'movie-water-v29';O.mkdir(exist_ok=True)
source=R/'movie-surfaces-v28/Suzume_scene_movie_surfaces_v28.blend';bpy.ops.wm.open_mainfile(filepath=str(source))
s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72);bpy.context.view_layer.update()
def value(v):
    if isinstance(v,(bool,int,float,str)):return v
    try:return list(v)
    except:return str(v)
def material(m):
    if not m:return None
    return {'name':m.name,'properties':{k:value(v) for k,v in m.items()},'nodes':[{'name':n.name,'type':n.bl_idname,'operation':getattr(n,'operation',None),'inputs':[{'index':index,'name':i.name,'value':value(i.default_value),'linked':i.is_linked} for index,i in enumerate(n.inputs) if hasattr(i,'default_value')],'image':n.image.name if getattr(n,'image',None) else None} for n in m.node_tree.nodes],'links':[[l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name] for l in m.node_tree.links]}
rows=[]
for name in [ob.name for ob in s.objects if ob.type=='MESH' and ob.name.startswith(('Live planar reflective shallow water','Flooded polygon flagstones and broken slabs solid mesh','Movie courtyard continuous basin bed'))]:
    ob=bpy.data.objects[name];a=np.array([list(ob.matrix_world@Vector(c)) for c in ob.bound_box]);rows.append({'name':name,'vertices':len(ob.data.vertices),'polygons':len(ob.data.polygons),'bboxMin':a.min(0).tolist(),'bboxMax':a.max(0).tolist(),'matrix':[list(row) for row in ob.matrix_world],'materials':[material(m) for m in ob.data.materials]})
result={'sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'scene':s.name,'objects':rows,'cameraPosition':list(s.camera.matrix_world.translation),'renderEngine':s.render.engine,'device':s.cycles.device,'oneToOneComplete':False}
(O/'source-inspection-v29.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
for row in rows:
    print('OBJECT',row['name'],row['vertices'],row['bboxMin'],row['bboxMax'],[m['name'] for m in row['materials']],flush=True)
    if row['name'].startswith('Live'):
        for n in row['materials'][0]['nodes']:
            if n['name'] in ['Tinted water reflection','Shallow blue green transmission','Artistic reflection balance','Millimeter water ripples','Wave height 1','Wave height 2','Wave height 3']:print('NODE',n,flush=True)
