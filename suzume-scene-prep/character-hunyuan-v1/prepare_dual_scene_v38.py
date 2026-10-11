"""Preserve the film scene and restore an independently editable poster environment."""
from pathlib import Path
import bpy, json, hashlib, numpy as np
R=Path(__file__).parent;O=R/'poster-v38';O.mkdir(exist_ok=True)
V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
movie=R/'movie-collar-v37/Suzume_scene_movie_collar_v37.blend'
poster=V/'suzume-full-scene-through-v12.blend'
def mesh_hash(obj):
    a=np.empty(len(obj.data.vertices)*3,np.float32);obj.data.vertices.foreach_get('co',a)
    m=np.array(obj.matrix_world,dtype='<f4')
    return hashlib.sha256(a.tobytes()+m.tobytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(movie))
film=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=film;film.frame_set(72);bpy.context.view_layer.update()
before={o.name:mesh_hash(o) for o in film.objects if o.type=='MESH'}
original_objects=set(bpy.data.objects);original_materials=set(bpy.data.materials)
with bpy.data.libraries.load(str(poster),link=False) as (src,dst):
    assert 'Daytime circular hotel' in src.scenes
    dst.scenes=['Daytime circular hotel']
s=dst.scenes[0];s.name='Official poster courtyard v38';bpy.context.window.scene=s;s.frame_set(1)
assert not (set(s.objects)&set(film.objects))
muted=[]
for o in set(bpy.data.objects)-original_objects:
    for mod in o.modifiers:
        if mod.type=='NODES' and mod.node_group:
            for n in mod.node_group.nodes:
                if n.bl_idname=='GeometryNodeRealizeInstances':n.mute=True;muted.append(o.name)
s.camera.name='Official poster reference camera v38'
s.render.use_border=False;s.render.use_crop_to_border=False
s.render.resolution_x=424;s.render.resolution_y=600;s.render.resolution_percentage=100
s.cycles.samples=16;s.cycles.use_denoising=True
s['reference_variant']='Official closed-door teaser poster'
s['reference_image']=str(V/'reference-official.jpg')
s['source_geometry_revision']=12;s['one_to_one_complete']=False
bpy.context.view_layer.update()
data={};clouds=[]
for o in s.objects:
    if o.type!='MESH' or 'cloud' not in o.name.lower():continue
    attr=o.data.color_attributes.get('surface_color')
    if not attr:continue
    a=np.empty((len(o.data.vertices),3),np.float32);o.data.vertices.foreach_get('co',a.ravel());M=np.array(o.matrix_world);world=a@M[:3,:3].T+M[:3,3]
    colors=np.empty((len(attr.data),4),np.float32);attr.data.foreach_get('color',colors.ravel())
    key='cloud'+str(len(clouds));data[key+'_world']=world;data[key+'_color']=colors
    clouds.append({'name':o.name,'key':key,'vertices':len(a),'triangles':len(o.data.polygons),'colorDomain':attr.domain,'materials':[m.name for m in o.data.materials],'bounds':[world.min(0).tolist(),world.max(0).tolist()]})
np.savez_compressed(O/'poster-cloud-source-v38.npz',**data)
camera=s.camera;camera.matrix_world.normalized()
camera_info={'matrixWorld':[list(row) for row in camera.matrix_world],'lens':camera.data.lens,'sensorHeight':camera.data.sensor_height,'aspect':2000/2824,'exposure':s.view_settings.exposure,'view':s.view_settings.view_transform,'look':s.view_settings.look}
bpy.context.window.scene=film;film.frame_set(72);bpy.context.view_layer.update()
assert before=={o.name:mesh_hash(o) for o in film.objects if o.type=='MESH'}
bpy.context.window.scene=s
path=O/'Suzume_dual_scene_restored_v38.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path))
audit={'revision':38,'movieSourceSha256':hashlib.sha256(movie.read_bytes()).hexdigest(),'posterSourceSha256':hashlib.sha256(poster.read_bytes()).hexdigest(),'posterScene':s.name,'movieScene':film.name,'movieMeshCount':len(before),'movieMeshesPreservedExactly':True,'disjointSceneObjects':True,'posterObjectCount':len(s.objects),'instanceRealizationDisabled':muted,'clouds':clouds,'posterCamera':camera_info,'posterMaterials':[m.name for m in set(bpy.data.materials)-original_materials],'movieMeshHashes':before,'oneToOneComplete':False}
(O/'restoration-v38.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
print(json.dumps({k:audit[k] for k in ['posterScene','movieMeshCount','movieMeshesPreservedExactly','posterObjectCount','posterCamera']},indent=2),flush=True)
