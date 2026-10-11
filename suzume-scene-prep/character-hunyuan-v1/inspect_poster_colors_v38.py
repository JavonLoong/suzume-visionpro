from pathlib import Path
import bpy,json
R=Path(__file__).parent;O=R/'poster-v38'
bpy.ops.wm.open_mainfile(filepath=str(O/'Suzume_dual_scene_restored_v38.blend'))
s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s
nodes=[]
for n in s.world.node_tree.nodes:
 row={'name':n.name,'type':n.bl_idname,'inputs':[]}
 for p in n.inputs:
  val=None
  if hasattr(p,'default_value'):
   val=p.default_value
   try:val=list(val)
   except TypeError:pass
  row['inputs'].append({'name':p.name,'value':val,'links':[q.from_node.name+':'+q.from_socket.name for q in p.links]})
 nodes.append(row)
out={'worldNodes':nodes,'worldLinks':[[l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name] for l in s.world.node_tree.links],'skyObjects':[o.name for o in s.objects if any(w in o.name.lower() for w in ['atmos','sky','dome'])]}
(O/'color-inspection-v38.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps(out,indent=2),flush=True)
