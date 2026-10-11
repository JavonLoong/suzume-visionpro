"""Inspect the actual saved night realm before changing its appearance."""
import bpy,json,numpy as np,sys
from pathlib import Path
from mathutils import Vector
R=Path(__file__).parent;O=R/'night-calibration-v19';O.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'Suzume_scene_Hunyuan_v17.blend'))
s=bpy.data.scenes['Night meadow through the door'];bpy.context.window.scene=s;s.frame_set(72)
report={'objects':[],'lights':[],'materials':[]}
for ob in s.objects:
    if ob.type=='LIGHT':report['lights'].append({'name':ob.name,'type':ob.data.type,'power':ob.data.energy,'position':list(ob.matrix_world.translation),'color':list(ob.data.color)})
    if ob.type!='MESH':continue
    if not any(word in ob.name.lower() for word in ['meadow','grass','flower','night sky','twilight']):continue
    row={'name':ob.name,'location':list(ob.location),'rotation':list(ob.rotation_euler),'scale':list(ob.scale),'vertices':len(ob.data.vertices),'hidden':ob.hide_render}
    points=np.array([v.co[:] for v in ob.data.vertices])
    if len(points):row['localBounds']=[points.min(0).tolist(),points.max(0).tolist()]
    row['attributes']=[{'name':a.name,'type':a.data_type,'domain':a.domain} for a in ob.data.attributes]
    if 'instance_color' in ob.data.attributes:
        colors=np.empty((len(ob.data.vertices),4),np.float32);ob.data.attributes['instance_color'].data.foreach_get('color',colors.ravel())
        row['instanceColorRange']=[colors.min(0).tolist(),colors.max(0).tolist()]
    row['nodes']=[]
    for mod in ob.modifiers:
        if mod.type=='NODES':
            for node in mod.node_group.nodes:
                record={'type':node.bl_idname,'name':node.name,'muted':node.mute}
                if node.bl_idname=='GeometryNodeObjectInfo':record['prototype']=node.inputs['Object'].default_value.name
                if hasattr(node,'domain'):record['domain']=node.domain
                row['nodes'].append(record)
    report['objects'].append(row)
for mat in bpy.data.materials:
    if not any(word in mat.name.lower() for word in ['meadow','grass','flower','night sky','twilight']):continue
    row={'name':mat.name,'nodes':[]}
    if mat.use_nodes:
        for node in mat.node_tree.nodes:
            record={'type':node.bl_idname,'name':node.name}
            if node.type=='ATTRIBUTE':record.update(attribute=node.attribute_name,attributeType=node.attribute_type)
            if node.type=='BSDF_PRINCIPLED':record.update(color=list(node.inputs['Base Color'].default_value),emission=list(node.inputs['Emission Color'].default_value),emissionStrength=node.inputs['Emission Strength'].default_value)
            row['nodes'].append(record)
        row['links']=[f'{l.from_node.name}.{l.from_socket.name} -> {l.to_node.name}.{l.to_socket.name}' for l in mat.node_tree.links]
    report['materials'].append(row)
(O/'baseline-inspection.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report),flush=True)
if '--render' in sys.argv:
    cam=s.camera;cam.location=(0,-4,1.75);cam.rotation_euler=(Vector((0,14,2.2))-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.lens=30;cam.data.sensor_fit='VERTICAL';cam.data.sensor_height=36
    s.render.resolution_x=480;s.render.resolution_y=320;s.render.resolution_percentage=100
    s.cycles.samples=16;s.cycles.use_denoising=True
    s.render.filepath=str(O/'night-baseline.png');bpy.ops.render.render(write_still=True)
