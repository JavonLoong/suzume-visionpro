import bpy,numpy as np,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'analysis/reduced';O.mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for p in sorted((R/'analysis/remeshed').glob('*.npz')):
 t=time.time();d=np.load(p);me=bpy.data.meshes.new(p.stem);me.from_pydata(d['vertices'],[],d['faces']);me.update();ob=bpy.data.objects.new(p.stem,me);bpy.context.collection.objects.link(ob);ob.select_set(True);bpy.context.view_layer.objects.active=ob
 sm=ob.modifiers.new('白模表面微小台阶平顺','SMOOTH');sm.factor=.18;sm.iterations=2;bpy.ops.object.modifier_apply(modifier=sm.name)
 de=ob.modifiers.new('减少冗余三角面','DECIMATE');de.decimate_type='COLLAPSE';de.ratio=.08;de.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=de.name)
 ob.data.calc_loop_triangles();v=np.empty((len(ob.data.vertices),3));ob.data.vertices.foreach_get('co',v.ravel());f=np.array([t.vertices[:] for t in ob.data.loop_triangles],dtype='int32')
 np.savez_compressed(O/p.name,vertices=v,faces=f);print('REDUCED',p.stem,len(f),round(time.time()-t,1),flush=True)
 bpy.data.objects.remove(ob,do_unlink=True)
 for m in list(bpy.data.meshes):
  if m.users==0:bpy.data.meshes.remove(m)
