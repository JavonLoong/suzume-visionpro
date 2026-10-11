"""Save the reviewed lighting configuration without changing the scene geometry."""
from pathlib import Path
import bpy,json,hashlib,sys,numpy as np
from mathutils import Vector
R=Path(__file__).parent;O=R/'movie-lighting-v27';sys.path.insert(0,str(R));from lighting_setup_v27 import apply_lighting
q=json.loads((O/'lighting-spec-v27.json').read_text(encoding='utf-8'))
bpy.ops.wm.open_mainfile(filepath=str(R/'movie-shore-v26/Suzume_scene_movie_shore_v26.blend'))
s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72);bpy.context.view_layer.update()
def fingerprint(o,evaluated=False):
    e=o.evaluated_get(bpy.context.evaluated_depsgraph_get()) if evaluated else o;mesh=e.to_mesh() if evaluated else o.data
    a=np.empty((len(mesh.vertices),3),np.float32);mesh.vertices.foreach_get('co',a.ravel());M=np.array(o.matrix_world);a=a@M[:3,:3].T+M[:3,3]
    if evaluated:e.to_mesh_clear()
    return hashlib.sha256(np.round(a,6).astype('<f4').tobytes()).hexdigest()
unchanged={o.name:fingerprint(o) for o in s.objects if o.type=='MESH'};camera={'matrix':[list(row) for row in s.camera.matrix_world],'lens':s.camera.data.lens}
apply_lighting(s,q)
for name,value in unchanged.items():assert fingerprint(bpy.data.objects[name])==value,name
characters=json.loads((R/'movie-shore-v26/integration-v26.json').read_text(encoding='utf-8'))['characters']
for name,row in characters.items():assert fingerprint(bpy.data.objects[name],True)==row['worldHash'],name
assert camera=={'matrix':[list(row) for row in s.camera.matrix_world],'lens':s.camera.data.lens}
lights=[]
for name in ['DirectionalLight','Soft courtyard fill on the movie facade v22','Cool courtyard fill on the left facade v23','Localized sunlight around the arched window v23']:
    o=bpy.data.objects[name];lights.append({'name':name,'type':o.data.type,'worldPosition':list(o.matrix_world.translation),'worldDirection':list(o.matrix_world.to_quaternion()@Vector((0,0,-1))),'power':o.data.energy,'color':list(o.data.color),'size':[getattr(o.data,'size',0),getattr(o.data,'size_y',0)]})
s['movie_lighting_revision']=27;s.render.use_border=False;s.render.resolution_x=720;s.render.resolution_y=468;s.render.resolution_percentage=100;s.cycles.samples=24;s.cycles.use_denoising=True
audit={'revision':27,'lighting':q,'lights':lights,'allDayMeshHashes':unchanged,'characters':characters,'camera':camera,'viewTransform':s.view_settings.view_transform,'exposure':s.view_settings.exposure,'nativeSkyDisplaySeparatedFromLighting':True,'oneToOneComplete':False}
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Suzume_scene_movie_lighting_v27.blend'));(O/'integration-v27.json').write_text(json.dumps(audit,indent=2),encoding='utf-8');print('LIGHTING_27_SAVED','PRESERVED_MESHES',len(unchanged),flush=True)
if '--render' in sys.argv:s.render.filepath=str(O/'movie-front-v27.png');bpy.ops.render.render(write_still=True)
