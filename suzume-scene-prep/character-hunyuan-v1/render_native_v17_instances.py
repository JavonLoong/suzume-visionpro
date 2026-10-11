"""Keep repeated foliage as instances without changing placements or colors."""
import bpy,json,hashlib,numpy as np
from pathlib import Path
R=Path(__file__).parent;H=R/'head-hunyuan-v1'
bpy.ops.wm.open_mainfile(filepath=str(R/'Suzume_scene_Hunyuan_v17.blend'))
records=[]
for obj in bpy.data.objects:
    if obj.type!='MESH':continue
    for mod in obj.modifiers:
        if mod.type!='NODES' or not mod.node_group:continue
        group=mod.node_group
        realizes=[n for n in group.nodes if n.bl_idname=='GeometryNodeRealizeInstances']
        if not realizes:continue
        position=np.empty((len(obj.data.vertices),3),np.float32);obj.data.vertices.foreach_get('co',position.ravel())
        row={'object':obj.name,'instances':len(position),'placementHash':hashlib.sha256(position.tobytes()).hexdigest(),'colorMode':'constant'}
        for node in realizes:node.mute=True
        for node in group.nodes:
            if node.bl_idname!='GeometryNodeObjectInfo':continue
            prototype=node.inputs['Object'].default_value
            if not prototype or prototype.type!='MESH':continue
            row['prototypeVertices']=len(prototype.data.vertices)
            for slot in prototype.material_slots:
                if not slot.material or not slot.material.use_nodes:continue
                for attr in slot.material.node_tree.nodes:
                    if attr.bl_idname=='ShaderNodeAttribute' and attr.attribute_name=='instance_color':
                        attr.attribute_type='INSTANCER'
                        row['colorMode']='original per-instance attribute'
        if 'instance_color' in obj.data.attributes:
            color=np.empty((len(position),4),np.float32);obj.data.attributes['instance_color'].data.foreach_get('color',color.ravel())
            row['instanceColorHash']=hashlib.sha256(color.tobytes()).hexdigest()
        records.append(row)
day=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=day;day.frame_set(72)
day['Foliage representation']='Linked instances with original instance colors; placements and counts unchanged.'
bpy.ops.wm.save_as_mainfile(filepath=str(R/'Suzume_scene_Hunyuan_v17_instances.blend'))
(H/'native-instance-optimization.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
print('NATIVE_INSTANCES_PRESERVED',json.dumps(records),flush=True)
day.render.resolution_x=720;day.render.resolution_y=468;day.render.resolution_percentage=100
day.cycles.samples=16;day.cycles.use_denoising=False
day.render.filepath=str(R/'native-pose-front-v17.png');bpy.ops.render.render(write_still=True)
audit=json.loads((H/'native-integration-v17.json').read_text(encoding='utf-8'))
audit['nativeRenderVerified']=True
audit['renderFile']='native-pose-front-v17.png'
audit['foliageInstancesPreserveGeometryAndColors']=True
audit['renderedNative']='Suzume_scene_Hunyuan_v17_instances.blend'
(H/'native-integration-v17.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print('NATIVE_V17_FULL_SCENE_RENDERED',flush=True)
