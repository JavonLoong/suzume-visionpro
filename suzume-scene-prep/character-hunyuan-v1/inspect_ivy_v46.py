from pathlib import Path
import bpy,json,numpy as np
R=Path(__file__).parent;O=R/'poster-railings-v46'
bpy.ops.wm.open_mainfile(filepath=str(R/'poster-rooftops-v45/Suzume_dual_scene_rooftops_v45.blend'));s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1)
rows=[]
for ob in s.objects:
    if 'ivy' not in ob.name.lower():continue
    row={'name':ob.name,'type':ob.type,'matrix':np.array(ob.matrix_world).tolist(),'modifiers':[]}
    if ob.type=='MESH':
        row['vertices']=len(ob.data.vertices);row['materials']=[m.name for m in ob.data.materials];row['attributes']=[{'name':a.name,'domain':a.domain,'type':a.data_type,'length':len(a.data)} for a in ob.data.attributes]
        verts=np.array([p.co[:] for p in ob.data.vertices]);row['bounds']=[verts.min(0).tolist(),verts.max(0).tolist()] if len(verts) else None
        for mod in ob.modifiers:
            rec={'name':mod.name,'type':mod.type}
            if mod.type=='NODES':rec['nodes']=[{'name':n.name,'type':n.bl_idname,'inputs':{i.name:str(i.default_value) for i in n.inputs if hasattr(i,'default_value')},'object':getattr(getattr(n,'object',None),'name',None)} for n in mod.node_group.nodes];rec['links']=[[l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name] for l in mod.node_group.links]
            if mod.type=='NODES':rec['mutedNodes']=[n.name for n in mod.node_group.nodes if n.mute]
            row['modifiers'].append(rec)
        if ob.modifiers:
            a=ob.data.color_attributes.get('instance_color');col=np.array([x.color[:] for x in a.data]);row['instanceColorRange']=[col.min(0).tolist(),col.max(0).tolist()]
            ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();row['evaluatedVertices']=len(me.vertices);row['evaluatedColors']=[x.name for x in me.color_attributes];ev.to_mesh_clear()
    rows.append(row)
(O/'ivy-inspection-v46.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2),flush=True)
