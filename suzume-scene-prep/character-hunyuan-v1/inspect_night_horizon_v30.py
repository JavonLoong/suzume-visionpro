"""Read the saved terrain edge to guide the next geometry pass; no scene mutation."""
from pathlib import Path
import bpy,numpy as np,json
R=Path(__file__).parent;O=R/'movie-night-v30'
bpy.ops.wm.open_mainfile(filepath=str(O/'Suzume_scene_movie_night_v30.blend'))
s=bpy.data.scenes['Night meadow through the door'];bpy.context.window.scene=s;bpy.context.view_layer.update()
ob=bpy.data.objects['Rolling meadow ground'];v=np.empty((len(ob.data.vertices),3),np.float32);ob.data.vertices.foreach_get('co',v.ravel());M=np.array(ob.matrix_world);v=v@M[:3,:3].T+M[:3,3]
edge=v[v[:,1]>v[:,1].max()-.1];rows=[]
for depth in [0,25,50,100,150,200]:
    band=v[(abs(v[:,0])<30)&(abs(v[:,1]-depth)<1.1)];rows.append({'depth':depth,'count':len(band),'heightRange':[float(band[:,2].min()),float(band[:,2].max())] if len(band) else None})
result={'source':'Suzume_scene_movie_night_v30.blend','object':ob.name,'vertices':len(v),'worldBounds':[v.min(0).tolist(),v.max(0).tolist()],'farEdgeHeightRange':[float(edge[:,2].min()),float(edge[:,2].max())],'crossSectionsNearCenter':rows,'materials':[m.name for m in ob.data.materials],'sceneModified':False,'interpretation':'The far boundary is a real edge of the finite ground mesh. Additional distant terrain and low haze require inferred geometry; preserve the near-door ground and plant positions.'}
(O/'native-horizon-inspection-v30.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=True),flush=True)
