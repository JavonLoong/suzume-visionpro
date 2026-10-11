"""Blender 5 CLI export. Never writes the source blend. All dimensions are metres."""
import bpy, json, math, hashlib, random, sys
from pathlib import Path
from mathutils import Vector, Matrix, Euler
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
RES=ROOT/'VisionProPortal'/'VisionProPortal'/'Resources'
OUT=ROOT/'validation'
for p in (RES,OUT): p.mkdir(parents=True,exist_ok=True)
SOURCE=Path(bpy.data.filepath)
night=bpy.data.scenes['Night meadow through the door']
poster=bpy.data.scenes['Official poster courtyard v38']
bpy.context.window.scene=poster
bpy.context.view_layer.update()
ap=poster.objects['Spatial doorway portal aperture.001']
corners=[ap.matrix_world@v.co for v in ap.data.vertices]
lo=Vector([min(v[i] for v in corners) for i in range(3)])
hi=Vector([max(v[i] for v in corners) for i in range(3)])
height=hi.z-lo.z
scale=2.1/height
origin=Vector(((lo.x+hi.x)/2,(lo.y+hi.y)/2,lo.z))
# Keep Z-up for working meshes/bakes. Blender USD exporter converts to Y-up/-Z forward.
normalise=Matrix.Scale(scale,4)@Matrix.Translation(-origin)
manifest={'source':str(SOURCE),'sourceSHA256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
 'sourceScene':night.name,'aperture':{'sourceWidth':hi.x-lo.x,'sourceHeight':height,'sourceThreshold':list(origin),
 'width':(hi.x-lo.x)*scale,'height':2.1,'uniformScale':scale,'origin':'threshold centre','upAxis':'Y','viewIntoWorld':'-Z'},
 'vegetation':[], 'files':{}, 'limitations':['Distant procedural clouds and sky are baked to a panorama; ground, flowers, grass, stars and door remain geometry.',
 'Low volumetric mist and clipped/rigged character fragments are excluded.', 'Manual alignment only. No device build, tracking or performance validation on this Windows host.']}

def activate(scene):
    bpy.context.window.scene=scene
    bpy.context.view_layer.update()

def configure_render(scene,w,h):
    scene.render.engine='CYCLES'
    scene.cycles.samples=16
    scene.cycles.use_denoising=True
    scene.cycles.max_bounces=4
    scene.render.resolution_x=w;scene.render.resolution_y=h;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    scene.view_settings.view_transform='Standard'
    scene.view_settings.look='None'
    scene.view_settings.exposure=0

def bake_sky():
    path=RES/'NightSky.png'
    receipt=OUT/'sky_clean_v2.json'
    if path.exists() and receipt.exists(): return path
    activate(night)
    # A separate scene prevents source visibility drivers from re-enabling character fragments.
    sky_scene=bpy.data.scenes.new('SkyBakeOnly')
    sky_scene.world=night.world.copy() if night.world else None
    for src in night.objects:
        if not (src.name.startswith('Spatial twilight cloud volume') or src.name=='Native enclosing night sky' or src.type=='LIGHT'): continue
        ob=src.copy();ob.data=src.data.copy();ob.animation_data_clear()
        ob.parent=None;ob.matrix_world=src.matrix_world.copy();ob.hide_render=False
        sky_scene.collection.objects.link(ob)
    data=bpy.data.cameras.new('PanoramaExportCamera')
    cam=bpy.data.objects.new('PanoramaExportCamera',data);sky_scene.collection.objects.link(cam)
    cam.location=origin+Vector((0,0,1.6/scale))
    cam.rotation_euler=(math.pi/2,0,0)
    data.type='PANO';data.panorama_type='EQUIRECTANGULAR';data.clip_end=2000
    sky_scene.camera=cam
    configure_render(sky_scene,2048,1024)
    sky_scene.render.filepath=str(path)
    activate(sky_scene)
    print('RENDER_SOURCE_SKY',flush=True)
    bpy.ops.render.render(write_still=True)
    receipt.write_text(json.dumps({'objects':[o.name for o in sky_scene.objects]}),encoding='utf-8')
    return path

def pbr(name,color=(.25,.3,.35,1),image=None,emission=0,rough=.8):
    mat=bpy.data.materials.new(name);mat.use_nodes=True
    bs=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    bs.inputs['Base Color'].default_value=color
    bs.inputs['Roughness'].default_value=rough
    bs.inputs['Emission Color'].default_value=color
    bs.inputs['Emission Strength'].default_value=emission
    if image:
        tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image
        mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
        if emission: mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Emission Color'])
    return mat

def clone_mesh(source,scene,name):
    obj=bpy.data.objects.new(name,source.data.copy());scene.collection.objects.link(obj)
    obj.matrix_world=source.matrix_world.copy()
    for i,mat in enumerate(obj.data.materials):
        if mat: obj.data.materials[i]=mat.copy()
    obj.hide_render=False;obj.hide_viewport=False
    return obj

def bake_base_color(ob,scene,size=1024):
    """Atlas only the source base colour, preserving UV input before creating new UVs."""
    print('BAKE_BASE_COLOR',ob.name,flush=True)
    activate(scene)
    for x in scene.objects: x.select_set(False)
    ob.select_set(True);bpy.context.view_layer.objects.active=ob
    if ob.data.uv_layers:
        old=ob.data.uv_layers.active
        old.name='OriginalUV'
    else: old=None
    for mat in ob.data.materials:
        if not mat or not mat.use_nodes: continue
        nt=mat.node_tree
        if old:
            uv=nt.nodes.new('ShaderNodeUVMap');uv.uv_map='OriginalUV'
            for node in list(nt.nodes):
                if node.type=='TEX_IMAGE' and not node.inputs['Vector'].is_linked:
                    nt.links.new(uv.outputs['UV'],node.inputs['Vector'])
        bs=next((n for n in nt.nodes if n.type=='BSDF_PRINCIPLED'),None)
        emission=nt.nodes.new('ShaderNodeEmission')
        if bs:
            socket=bs.inputs['Base Color']
            if socket.is_linked: nt.links.new(socket.links[0].from_socket,emission.inputs['Color'])
            else: emission.inputs['Color'].default_value=socket.default_value
        out=next(n for n in nt.nodes if n.type=='OUTPUT_MATERIAL')
        nt.links.new(emission.outputs[0],out.inputs['Surface'])
    atlas=ob.data.uv_layers.new(name='AtlasUV');ob.data.uv_layers.active=atlas
    # Planar mapping suits the continuous terrain; compact door pieces get a smart atlas.
    if 'Meadow' in ob.name:
        pts=[ob.matrix_world@v.co for v in ob.data.vertices]
        x0=min(p.x for p in pts);x1=max(p.x for p in pts)
        y0=min(p.y for p in pts);y1=max(p.y for p in pts)
        for poly in ob.data.polygons:
            for li in poly.loop_indices:
                p=pts[ob.data.loops[li].vertex_index]
                atlas.data[li].uv=((p.x-x0)/(x1-x0),(p.y-y0)/(y1-y0))
    else:
        bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=1.15,island_margin=.012)
        bpy.ops.object.mode_set(mode='OBJECT')
    atlas.active_render=True
    image=bpy.data.images.new(ob.name+'_BaseColor',width=size,height=size,alpha=False)
    for mat in ob.data.materials:
        if not mat: continue
        node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=image
        mat.node_tree.nodes.active=node
    configure_render(scene,size,size);scene.cycles.samples=1
    scene.render.bake.margin=4;scene.render.bake.use_clear=True
    bpy.ops.object.bake(type='EMIT')
    scene.render.engine='BLENDER_WORKBENCH'
    file=RES/(ob.name+'_BaseColor.png')
    image.filepath_raw=str(file);image.file_format='PNG';image.save()
    # A single atlas material and UV set avoids overlapping source material UV islands.
    ob.data.materials.clear();ob.data.materials.append(pbr(ob.name+'_PBR',image=image))
    for poly in ob.data.polygons: poly.material_index=0
    ob.data.uv_layers.active=ob.data.uv_layers['AtlasUV']
    ob.data.uv_layers.active.active_render=True

def flatten_transform(ob):
    ob.data.transform(normalise@ob.matrix_world)
    ob.matrix_world=Matrix.Identity(4)

def select_indices(source,count,indices=None):
    if indices is not None: return indices
    positions=[source.matrix_world@v.co for v in source.data.vertices]
    candidates=[i for i,p in enumerate(positions) if p.y>origin.y+.15]
    ordered=sorted(candidates,key=lambda i:positions[i].x**2+(positions[i].y-origin.y)**2)
    near=ordered[:min(700,count)]
    rng=random.Random(56)
    return sorted(near+rng.sample(ordered[len(near):],min(count-len(near),len(ordered)-len(near))))

def vegetation(name,count,scene,indices=None):
    src=night.objects[name]
    mod=next(m for m in src.modifiers if m.type=='NODES')
    proto=next(n.inputs['Object'].default_value for n in mod.node_group.nodes if n.type=='OBJECT_INFO')
    ids=select_indices(src,count,indices)
    v0=np.array([list(v.co) for v in proto.data.vertices],dtype=np.float32)
    faces0=[tuple(p.vertices) for p in proto.data.polygons]
    vertices=[];faces=[];rot=src.data.attributes['instance_rotation'].data;scl=src.data.attributes['instance_scale'].data
    xf=normalise@src.matrix_world
    for j,i in enumerate(ids):
        local=Matrix.LocRotScale(src.data.vertices[i].co,Euler(rot[i].vector).to_quaternion(),Vector(scl[i].vector))
        m=np.array(xf@local)
        verts=v0@m[:3,:3].T+m[:3,3]
        vertices.extend(verts.tolist());offset=j*len(v0)
        faces.extend(tuple(k+offset for k in f) for f in faces0)
    mesh=bpy.data.meshes.new(name+'_PortableMesh');mesh.from_pydata(vertices,[],faces);mesh.update()
    ob=bpy.data.objects.new(name.replace(' ','_'),mesh);scene.collection.objects.link(ob)
    if 'instance_color' in src.data.attributes:
        colors=src.data.attributes['instance_color'].data
        size=math.ceil(math.sqrt(len(ids)))
        image=bpy.data.images.new('FlowerPalette',size,size,alpha=False)
        pixels=np.ones((size*size,4),dtype=np.float32)
        for j,i in enumerate(ids): pixels[j]=colors[i].color
        image.pixels.foreach_set(pixels.ravel());image.filepath_raw=str(RES/'FlowerPalette.png');image.file_format='PNG';image.save()
        uv=mesh.uv_layers.new(name='st')
        for poly in mesh.polygons:
            j=poly.vertices[0]//len(v0)
            for li in poly.loop_indices: uv.data[li].uv=((j%size+.5)/size,(j//size+.5)/size)
        mat=pbr('FlowerPalette_PBR',image=image,emission=.16)
        next(n for n in mat.node_tree.nodes if n.type=='TEX_IMAGE').interpolation='Closest'
    else:
        original=next(n for n in proto.data.materials[0].node_tree.nodes if n.type=='BSDF_PRINCIPLED')
        mat=pbr(name+'_PBR',tuple(original.inputs['Base Color'].default_value))
    mesh.materials.append(mat)
    manifest['vegetation'].append({'source':name,'sourceInstances':len(src.data.vertices),'exportedInstances':len(ids),'vertices':len(vertices),'selection':'700 nearest, remainder deterministic seed 56; source side behind doorway only'})
    return ids

def make_sky(scene,path):
    verts=[];faces=[];uvs=[];nx=128;ny=64;r=330
    for j in range(ny+1):
        v=j/ny;theta=math.pi*(1-v)
        for i in range(nx+1):
            u=i/nx;phi=math.pi-2*math.pi*u
            # Same ray convention as Cycles equirectangular with camera Rx(pi/2).
            verts.append((-r*math.sin(theta)*math.sin(phi),r*math.sin(theta)*math.cos(phi),r*math.cos(theta)+1.6))
            uvs.append((u,v))
    for j in range(ny):
        for i in range(nx):
            a=j*(nx+1)+i;faces.append((a,a+nx+1,a+nx+2,a+1))
    mesh=bpy.data.meshes.new('DistantSkyMesh');mesh.from_pydata(verts,[],faces)
    uv=mesh.uv_layers.new(name='st')
    for p in mesh.polygons:
        for li in p.loop_indices: uv.data[li].uv=uvs[mesh.loops[li].vertex_index]
    ob=bpy.data.objects.new('DistantSky',mesh);scene.collection.objects.link(ob)
    # Use an emission material; the app also replaces this with an unlit material.
    mat=pbr('DistantSky_Emission',image=bpy.data.images.load(str(path)),emission=1)
    mesh.materials.append(mat)
    for p in mesh.polygons: p.use_smooth=True

def export(scene,name):
    activate(scene)
    path=RES/(name+'.usdz')
    print('EXPORT',name,flush=True)
    bpy.ops.wm.usd_export(filepath=str(path),selected_objects_only=False,export_animation=False,
      export_textures_mode='NEW',export_materials=True,generate_preview_surface=True,generate_materialx_network=False,
      export_armatures=False,export_shapekeys=False,export_lights=False,export_cameras=False,
      export_volumes=False,export_curves=False,export_points=False,triangulate_meshes=True,
      convert_orientation=True,export_global_forward_selection='NEGATIVE_Z',export_global_up_selection='Y',
      convert_scene_units='METERS',meters_per_unit=1.0,root_prim_path='/Suzume',relative_paths=True,
      usdz_downscale_size='KEEP')
    triangles=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in scene.objects if o.type=='MESH')
    manifest['files'][name+'.usdz']={'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'triangles':triangles,'objects':len(scene.objects)}

sky=bake_sky()
world=bpy.data.scenes.new('VisionPro_DreamWorld')
for source,name in [('Rolling meadow ground','NearMeadow'),('Continuous distant meadow v31','DistantMeadow')]:
    activate(night)
    ob=clone_mesh(night.objects[source],world,name)
    bake_base_color(ob,world,2048 if name=='NearMeadow' else 1024)
    flatten_transform(ob)
activate(night)
ids=vegetation('Individual meadow flowers',2500,world)
vegetation('Modeled flower stems',2500,world,ids)
vegetation('Spatial grass blades',5000,world)
stars=clone_mesh(night.objects['Spatial luminous stars'],world,'SpatialStars')
stars.data.materials.clear();stars.data.materials.append(pbr('Starlight',(.48,.62,1,1),emission=2.6))
flatten_transform(stars)
make_sky(world,sky)
exports=[(world,'DreamWorld')]

activate(poster)
root=poster.objects['Complete six-panel white door and frame.001']
for label,predicate in [('DoorFrame',lambda o:o.parent==root),('DoorLeaf',lambda o:o.parent and o.parent.name=='Animated door leaf and hinges.001')]:
    scene=bpy.data.scenes.new('VisionPro_'+label)
    for idx,src in enumerate([o for o in root.children_recursive if o.type=='MESH' and predicate(o)]):
        ob=clone_mesh(src,scene,label+'_'+str(idx))
        # Door source materials use existing UV atlases; retain them without a second Cycles scene.
        for slot,mat in enumerate(list(ob.data.materials)):
            if not mat: continue
            bs=next((n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
            tex=next((n for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image),None)
            color=tuple(bs.inputs['Base Color'].default_value) if bs else (.75,.78,.72,1)
            ob.data.materials[slot]=pbr(mat.name+'_Portable',color,image=tex.image if tex else None)
        flatten_transform(ob)
    exports.append((scene,label))

# Complete Cycles baking before USD/OpenImageIO texture export in this process.
for scene,label in exports: export(scene,label)

(RES/'AssetManifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf-8')
(OUT/'export_manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf-8')
print('EXPORT_COMPLETE',json.dumps(manifest['files']),flush=True)
