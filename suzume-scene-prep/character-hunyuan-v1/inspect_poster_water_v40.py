from pathlib import Path
import bpy,json,numpy as np,hashlib
from mathutils import Vector
R=Path(__file__).parent;O=R/'poster-water-v40';O.mkdir(exist_ok=True);native=R/'poster-steel-v39/Suzume_dual_scene_steel_v39.blend'
bpy.ops.wm.open_mainfile(filepath=str(native));s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1);bpy.context.view_layer.update()
waters=[o for o in s.objects if o.name.startswith('Live planar reflective shallow water')];assert len(waters)==1;ob=waters[0];mat=ob.data.materials[0]
rows=[]
for n in mat.node_tree.nodes:
    if n.type not in ['BSDF_PRINCIPLED','BSDF_REFRACTION','BUMP','MATH','VALUE']:continue
    row={'name':n.name,'type':n.type,'operation':getattr(n,'operation',None),'inputs':{}}
    for p in n.inputs:
        if p.is_linked:row['inputs'][p.name]={'link':p.links[0].from_node.name+':'+p.links[0].from_socket.name}
        elif hasattr(p,'default_value'):
            value=p.default_value
            try:value=list(value)
            except TypeError:pass
            row['inputs'][p.name]=value
    rows.append(row)
world=[ob.matrix_world@Vector(v) for v in ob.bound_box];cam=s.camera
report={'sourceSha256':hashlib.sha256(native.read_bytes()).hexdigest(),'scene':s.name,'waterObject':ob.name,'waterMaterial':mat.name,'waterBounds':[[min(p[i] for p in world),max(p[i] for p in world)] for i in range(3)],'waterVertices':len(ob.data.vertices),'nodes':rows,'camera':{'matrixWorld':[list(q) for q in cam.matrix_world],'lens':cam.data.lens,'sensorHeight':cam.data.sensor_height,'exposure':s.view_settings.exposure},'floorObjects':[o.name for o in s.objects if o.type=='MESH' and any(k in o.name.lower() for k in ['flagstone','floor','water'])]}
(O/'inspection-v40.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({k:report[k] for k in ['waterObject','waterMaterial','waterBounds','waterVertices','floorObjects']},indent=2),flush=True)
