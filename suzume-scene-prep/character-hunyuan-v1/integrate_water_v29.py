"""Save the reviewed shallow-water optics and submerged stone materials."""
from pathlib import Path
import bpy,json,hashlib,sys,numpy as np
R=Path(__file__).parent;O=R/'movie-water-v29';sys.path.insert(0,str(R));from water_setup_v29 import apply_water
q=json.loads((O/'water-spec-v29.json').read_text(encoding='utf-8'))
bpy.ops.wm.open_mainfile(filepath=str(R/'movie-surfaces-v28/Suzume_scene_movie_surfaces_v28.blend'))
s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72);bpy.context.view_layer.update()
baseline=json.loads((R/'movie-surfaces-v28/integration-v28.json').read_text(encoding='utf-8'))
def fingerprint(ob,evaluated=False):
    e=ob.evaluated_get(bpy.context.evaluated_depsgraph_get()) if evaluated else ob;m=e.to_mesh() if evaluated else ob.data
    a=np.empty((len(m.vertices),3),np.float32);m.vertices.foreach_get('co',a.ravel());M=np.array(ob.matrix_world);a=a@M[:3,:3].T+M[:3,3]
    if evaluated:e.to_mesh_clear()
    return hashlib.sha256(np.round(a,6).astype('<f4').tobytes()).hexdigest()
mat=apply_water(s,q)
for name,value in baseline['allDayMeshHashes'].items():assert fingerprint(bpy.data.objects[name])==value,name
for name,row in baseline['characters'].items():assert fingerprint(bpy.data.objects[name],True)==row['worldHash'],name
assert baseline['camera']=={'matrix':[list(row) for row in s.camera.matrix_world],'lens':s.camera.data.lens}
s['movie_water_revision']=29;s['one_to_one_complete']=False
s.render.use_border=False;s.render.resolution_x=720;s.render.resolution_y=468;s.render.resolution_percentage=100;s.cycles.samples=32;s.cycles.use_denoising=True
audit={'revision':29,'parameters':q,'allDayMeshHashes':baseline['allDayMeshHashes'],'topologyHashes':baseline['topologyHashes'],'characters':baseline['characters'],'camera':baseline['camera'],'lightingUnchangedFrom':27,'wallSurfaceRevisionPreserved':28,'newGeometryCount':0,'submergedAlgaeMaterials':[m.name for m in bpy.data.materials if m.get('submerged_algae_revision')==29],'referenceImageUsedInWater':False,'liveRayTracedReflectionAndRefraction':True,'oneToOneComplete':False}
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Suzume_scene_movie_water_v29.blend'));(O/'integration-v29.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8');print('WATER_29_SAVED',json.dumps({'geometryPreserved':len(audit['allDayMeshHashes']),'algaeMaterials':len(audit['submergedAlgaeMaterials'])}),flush=True)
