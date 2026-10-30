"""Headless Blender: source-derived printable modules, millimetre coordinates."""
import bpy,sys,math,json,time,numpy as np
from pathlib import Path
from mathutils import Matrix
ROOT=Path(__file__).resolve().parents[1];PREP=ROOT/'analysis'/'prepared';OUT=ROOT/'analysis'/'solid';OUT.mkdir(exist_ok=True)
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
jobs=args or ['wall']
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
def obj(name,v,f):
 me=bpy.data.meshes.new(name);me.from_pydata(v,[],f);me.update()
 ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob);return ob
def sector_plate(a,b,ri,ro,z0,z1):
 n=max(16,round((b-a)*140));angles=np.linspace(a,b,n+1);v=[]
 for z in [z0,z1]:
  for r in [ri,ro]:v.extend([(r*math.cos(t),r*math.sin(t),z) for t in angles])
 k=n+1;f=[]
 for j in range(n):
  f.extend([(j,j+1,k+j+1,k+j),(2*k+j,3*k+j,3*k+j+1,2*k+j+1),(j,2*k+j,2*k+j+1,j+1),(k+j,k+j+1,3*k+j+1,3*k+j)])
 f.extend([(0,k,3*k,2*k),(n,2*k+n,3*k+n,k+n)])
 return np.array(v),np.array(f)
for cat in jobs:
 d=np.load(PREP/(cat+'.npz'));v=d['vertices'];f=d['faces'];cent=v[f].mean(axis=1)
 n=8 if cat in ['wall','steel'] else (4 if cat=='ground' else 1)
 for i in range(n):
  name=f'{cat}_{i+1:02d}';target=OUT/(name+'.npz')
  if target.exists():print('SKIP',name,flush=True);continue
  start=time.time()
  # Include full triangles near each cut; final exact Boolean clipping follows remesh.
  if n>1:
   a=i*2*math.pi/n;b=(i+1)*2*math.pi/n
   theta=np.arctan2(cent[:,1],cent[:,0])%(2*math.pi)
   mid=(a+b)/2;delta=(theta-mid+math.pi)%(2*math.pi)-math.pi
   mask=np.abs(delta)<(b-a)/2+.08
   ff=f[mask];inds,inv=np.unique(ff,return_inverse=True);vv=v[inds];ff=inv.reshape(-1,3)
  else:vv=v;ff=f
  ob=obj(name,vv,ff)
  bpy.context.view_layer.objects.active=ob;ob.select_set(True)
  # Expand physical surfaces by 0.25 mm, retaining source silhouettes and holes.
  disp=ob.modifiers.new('打印加厚_0.25毫米','DISPLACE');disp.strength=.25 if cat!='steel' else .35;disp.mid_level=0
  bpy.ops.object.modifier_apply(modifier=disp.name)
  if cat in ['wall','steel']:
   band=sector_plate(a-.03,b+.03,151.5 if cat=='wall' else 122,196.5 if cat=='wall' else 145,5,7.4)
   support=obj(name+'_装配底托',*band);support.select_set(True)
   bpy.ops.object.join()
  ob.data.remesh_voxel_size=.28 if cat in ['wall','steel'] else (.3 if cat=='ground' else .12)
  ob.data.remesh_voxel_adaptivity=0
  print('REMESH',name,len(ob.data.polygons),flush=True)
  bpy.ops.object.voxel_remesh()
  print('VOXEL_DONE',name,len(ob.data.polygons),round(time.time()-start,1),flush=True)
  ob.data.calc_loop_triangles()
  vertices=np.empty((len(ob.data.vertices),3));ob.data.vertices.foreach_get('co',vertices.ravel())
  faces=np.array([p.vertices[:] for p in ob.data.loop_triangles],dtype=np.int32)
  np.savez_compressed(target,vertices=vertices,faces=faces)
  print('DONE',name,len(faces),round(time.time()-start,1),'s',flush=True)
  bpy.data.objects.remove(ob,do_unlink=True)
  for me in list(bpy.data.meshes):
   if me.users==0:bpy.data.meshes.remove(me)
print('REMESH_COMPLETE',flush=True)
