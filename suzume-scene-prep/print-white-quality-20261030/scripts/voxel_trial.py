import time,sys,json,numpy as np,trimesh,pymeshlab as pm
from pathlib import Path
R=Path(__file__).resolve().parents[1];n=sys.argv[1] if len(sys.argv)>1 else 'W02_环形建筑';t=time.time()
q=np.load(R/'analysis/reduced'/(n+'.npz'));m=trimesh.Trimesh(q['vertices'],q['faces'],process=True)
v=m.voxelized(.28).fill();print('VOXEL',n,v.shape,round(time.time()-t,1),flush=True)
mc=v.marching_cubes;mc.apply_transform(v.transform)
print('MARCH',len(mc.faces),mc.volume,round(time.time()-t,1),flush=True)
ms=pm.MeshSet();ms.add_mesh(pm.Mesh(mc.vertices,mc.faces));ms.meshing_decimation_quadric_edge_collapse(targetfacenum=180000 if n[0]=='W' else 100000,preservenormal=True,preservetopology=True,qualitythr=.5)
x=ms.current_mesh();verts=x.vertex_matrix().copy();faces=x.face_matrix().copy();ms.compute_selection_by_self_intersections_per_face()
print('DECIMATE_SELF',ms.current_mesh().selected_face_number(),len(faces),round(time.time()-t,1),flush=True)
o=R/'analysis/voxel_fixed';o.mkdir(exist_ok=True);np.savez_compressed(o/(n+'.npz'),vertices=verts,faces=faces)
