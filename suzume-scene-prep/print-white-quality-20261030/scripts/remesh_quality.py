import bpy,sys,time,numpy as np
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'analysis/sources';O=R/'analysis/remeshed';O.mkdir(exist_ok=True)
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for p in sorted(P.glob('*.npz')):
 n=p.stem
 if n[0] not in 'WS' or '_附件' in n or (args and not any(n.startswith(a) for a in args)):continue
 target=O/p.name
 if target.exists():continue
 t=time.time();d=np.load(p);me=bpy.data.meshes.new(n);me.from_pydata(d['vertices'],[],d['faces']);me.update();ob=bpy.data.objects.new(n,me);bpy.context.collection.objects.link(ob);ob.select_set(True);bpy.context.view_layer.objects.active=ob
 # Real shell growth, then a fresh surface union. Preserve windows and arches.
 disp=ob.modifiers.new('结构局部实体加厚','DISPLACE');disp.strength=.22 if n[0]=='W' else .32;disp.mid_level=0;bpy.ops.object.modifier_apply(modifier=disp.name)
 ob.data.remesh_voxel_size=.2 if n[0]=='W' else .16;ob.data.remesh_voxel_adaptivity=0
 bpy.ops.object.voxel_remesh();ob.data.calc_loop_triangles()
 v=np.empty((len(ob.data.vertices),3));ob.data.vertices.foreach_get('co',v.ravel());f=np.array([t.vertices[:] for t in ob.data.loop_triangles],dtype='int32')
 np.savez_compressed(target,vertices=v,faces=f);print('REMESHED',n,len(f),round(time.time()-t,1),flush=True)
 bpy.data.objects.remove(ob,do_unlink=True)
 for m in list(bpy.data.meshes):
  if m.users==0:bpy.data.meshes.remove(m)
