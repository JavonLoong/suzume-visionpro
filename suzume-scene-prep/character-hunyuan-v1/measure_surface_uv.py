import bpy,numpy as np
from pathlib import Path
R=Path(__file__).parent
bpy.ops.wm.open_mainfile(filepath=str(R/'Suzume_Hunyuan31_rigged.blend'))
ob=bpy.data.objects['Suzume Hunyuan textured surface'];m=ob.data
indices=np.empty(len(m.loops),np.int32);m.loops.foreach_get('vertex_index',indices)
uv=np.empty((len(m.loops),2),np.float32);m.uv_layers.active.data.foreach_get('uv',uv.ravel())
vertex_uv=np.empty((len(m.vertices),2),np.float32);vertex_uv[indices]=uv
np.save(R/'character-vertex-uv.npy',vertex_uv)
print('UV_MEASURED',len(vertex_uv))
