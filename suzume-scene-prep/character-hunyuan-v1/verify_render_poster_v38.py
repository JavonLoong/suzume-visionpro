from pathlib import Path
import bpy,json,hashlib,numpy as np,math,bmesh
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
R=Path(__file__).parent;O=R/'poster-v38'
V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
native=O/'Suzume_dual_scene_v38.blend'
def tree_hash(tree):
    if not tree:return None
    rows=[]
    for n in tree.nodes:
        row={'name':n.name,'type':n.bl_idname,'mute':n.mute,'inputs':[]}
        for key in ['operation','blend_type','attribute_name','interpolation','extension']:
            if hasattr(n,key):row[key]=getattr(n,key)
        if hasattr(n,'image'):row['image']=n.image.name if n.image else None
        if hasattr(n,'node_tree'):row['group']=n.node_tree.name if n.node_tree else None
        for p in n.inputs:
            if hasattr(p,'default_value'):
                value=p.default_value
                try:value=list(value)
                except TypeError:pass
                if isinstance(value,(str,float,int,bool,list)) or value is None:row['inputs'].append([p.name,value])
        rows.append(row)
    value={'nodes':rows,'links':[[l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier] for l in tree.links]}
    return hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()
def movie_snapshot():
    s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72);bpy.context.view_layer.update()
    meshes={};materials={};modifiers={}
    for o in s.objects:
        if o.type!='MESH':continue
        a=np.empty(len(o.data.vertices)*3,np.float32);o.data.vertices.foreach_get('co',a)
        indices=np.empty(len(o.data.loops),np.int32);o.data.loops.foreach_get('vertex_index',indices)
        meshes[o.name]=hashlib.sha256(a.tobytes()+indices.tobytes()+np.array(o.matrix_world,dtype='<f4').tobytes()).hexdigest()
        for m in o.data.materials:
            if m:materials[m.name]=tree_hash(m.node_tree)
        modifiers[o.name]=[[m.name,m.type,m.show_render,m.show_viewport] for m in o.modifiers]
    camera=s.camera
    return {'meshes':meshes,'materials':materials,'modifiers':modifiers,'world':tree_hash(s.world.node_tree),'camera':[camera.name,*list(camera.location),*list(camera.rotation_euler),camera.data.lens],'renderColors':[s.view_settings.view_transform,s.view_settings.look,s.view_settings.exposure]}
bpy.ops.wm.open_mainfile(filepath=str(R/'movie-collar-v37/Suzume_scene_movie_collar_v37.blend'));before=movie_snapshot()
bpy.ops.wm.open_mainfile(filepath=str(native));after=movie_snapshot();assert before==after,'Movie scene changed during poster integration.'
movie=bpy.data.scenes['Daytime circular hotel'];s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1);bpy.context.view_layer.update()
assert not set(s.objects)&set(movie.objects)
materials=set(m for o in s.objects if o.type=='MESH' for m in o.data.materials if m)
film_materials=set(m for o in movie.objects if o.type=='MESH' for m in o.data.materials if m)
assert not materials&film_materials
clouds=[]
for o in s.objects:
    if o.type!='MESH' or 'cloud' not in o.name.lower() or not o.data.color_attributes.get('surface_color'):continue
    bm=bmesh.new();bm.from_mesh(o.data);bad=sum(not e.is_manifold for e in bm.edges);volume=abs(bm.calc_volume());bm.free()
    assert bad==0 and volume>0,(o.name,bad,volume)
    clouds.append({'name':o.name,'nonManifoldEdges':bad,'localVolume':volume,'vertices':len(o.data.vertices)})
assert len(clouds)==47
camera=s.camera;s.render.resolution_x=2000;s.render.resolution_y=2824;s.render.resolution_percentage=100
steel=[]
for o in s.objects:
    if o.type=='MESH' and o.name.startswith('Broken radial dome steelwork solid mesh'):
        a=np.empty((len(o.data.vertices),3),np.float32);o.data.vertices.foreach_get('co',a.ravel());M=np.array(o.matrix_world);steel.append(a@M[:3,:3].T+M[:3,3])
steel=np.concatenate(steel);tips=[]
for q in json.loads((V/'dome-calibration-v7.json').read_text())['measured_tips']:
    a=q['angle'];t=q['end_parameter'];p=np.array([math.sin(a)*20.3*math.cos(t),math.cos(a)*20.3*math.cos(t),5.75+12*math.sin(t)])
    distances=np.linalg.norm(steel-p,axis=1);nearest=steel[int(np.argmin(distances))]
    uv=world_to_camera_view(s,camera,Vector(p));pixel=np.array([uv.x*2000,(1-uv.y)*2824]);target=np.array(q['reference'])/[1336,1888]*[2000,2824]
    tips.append({'name':q['name'],'referencePixel':target.tolist(),'projectedCenterline':pixel.tolist(),'pixelError':float(np.linalg.norm(pixel-target)),'nearestActualSteelVertexMeters':float(distances.min())})
assert max(q['nearestActualSteelVertexMeters'] for q in tips)<.25
assert max(q['pixelError'] for q in tips)<2
assert all(im.packed_file for im in bpy.data.images if im.source=='FILE' and im.users>0), 'An externally referenced image was not packed.'
audit={'revision':38,'nativeSha256':hashlib.sha256(native.read_bytes()).hexdigest(),'freshReopenVerified':True,'movieGeometryTopologyMaterialsModifiersWorldAndCameraPreserved':True,'movieMeshCount':len(before['meshes']),'movieMaterialCount':len(before['materials']),'independentSceneObjectsAndMaterials':True,'closedCloudMeshes':clouds,'steelTipChecks':tips,'referenceMeasurementUncertaintyPixels':6,'packedSourceImagesVerified':True,'scope':'Scene separation, unchanged movie state, real cloud volumes and five poster steel tips only. Does not establish overall visual equivalence.','browserRuntimeVerified':False,'oneToOneComplete':False}
(O/'verification-v38.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
print('POSTER_38_FRESH_VERIFIED',len(clouds),'closed clouds',flush=True)
s.render.use_border=False;s.render.use_crop_to_border=False;s.render.resolution_x=708;s.render.resolution_y=1000;s.cycles.samples=28;s.cycles.use_denoising=True;s.render.filepath=str(O/'poster-front-final-v38.png')
bpy.ops.render.render(write_still=True);print('POSTER_38_FINAL_FRONT_DONE',flush=True)
camera.location=(-9,-12,4);camera.rotation_euler=(Vector((0,2,3))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.lens=30
s.render.resolution_x=720;s.render.resolution_y=468;s.cycles.samples=20;s.render.filepath=str(O/'poster-oblique-v38.png')
bpy.ops.render.render(write_still=True);print('POSTER_38_OBLIQUE_DONE',flush=True)
