from pathlib import Path
import numpy as np,pymeshlab as pm,time,trimesh
R=Path(__file__).resolve().parents[1];n='W05_环形建筑';t=time.time()
d=np.load(R/'analysis/reduced'/(n+'.npz'));ms=pm.MeshSet();ms.add_mesh(pm.Mesh(d['vertices'],d['faces']))
ms.generate_resampled_uniform_mesh(cellsize=pm.PureValue(.3),offset=pm.PureValue(0),mergeclosevert=True,discretize=False,multisample=True,absdist=False)
m=ms.current_mesh();print('RESAMPLED',m.vertex_number(),m.face_number(),round(time.time()-t,1),flush=True)
ms.meshing_decimation_quadric_edge_collapse(targetfacenum=220000,preservenormal=True,preservetopology=True,qualitythr=.5)
m=ms.current_mesh();v=m.vertex_matrix().copy();f=m.face_matrix().copy();ms.compute_selection_by_self_intersections_per_face()
mesh=trimesh.Trimesh(v,f,process=True)
print('CHECK',mesh.is_watertight,mesh.volume,ms.current_mesh().selected_face_number(),round(time.time()-t,1),flush=True)
np.savez_compressed(R/'analysis/W05_resampled.npz',vertices=mesh.vertices,faces=mesh.faces)
