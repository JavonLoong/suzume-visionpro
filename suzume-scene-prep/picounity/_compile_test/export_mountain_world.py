"""Restore the original high terrain; retain the current sky, flowers and textures."""
import bpy, json, sys, math
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(r'D:\虚拟C盘\JavonLoongSkill\suzume-scene-prep')
PROJECT=ROOT/'picounity'
SOURCE=ROOT/'character-hunyuan-v1/poster-right-bow-v56/Suzume_dual_scene_right_bow_v56.blend'
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
src=bpy.data.objects['Rolling meadow ground.001']
normalise=Matrix.Scale(2.1/3.4,4) @ Matrix.Translation(Vector((0,-.0719999149441719,-.21999990940093994)))
xf=normalise @ src.matrix_world
verts=[xf @ v.co for v in src.data.vertices]
faces=[tuple(p.vertices) for p in src.data.polygons]
hills=BVHTree.FromPolygons(verts,faces)
def sample(tree,x,y):
    hit=tree.ray_cast(Vector((x,y,1000)),Vector((0,0,-1)))
    return hit[0].z if hit[0] else None
samples={str((x,y)):sample(hills,x,y) for x,y in [(0,0),(0,2.7),(0,10),(0,30),(12,20)]}
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(PROJECT/'Assets/Models/DreamWorld.fbx'))
ground=next(o for o in bpy.context.scene.objects if o.type=='MESH' and ('Geometry_C7FAF2CB' in o.name or 'NearMeadow' in o.name))
oldVerts=[ground.matrix_world @ v.co for v in ground.data.vertices]
oldTree=BVHTree.FromPolygons(oldVerts,[tuple(p.vertices) for p in ground.data.polygons])
# Shift each existing plant onto the old mountain surface; never flatten the source terrain.
cache={}
def delta(x,y):
    key=(round(x,2),round(y,2))
    if key not in cache:
        a=sample(hills,*key); b=sample(oldTree,*key)
        cache[key]=(a-b) if a is not None and b is not None else 0
    return cache[key]
adjusted=[]
for ob in bpy.context.scene.objects:
    if ob.type!='MESH' or not any(n in ob.name for n in ('Individual_meadow','Modeled_flower','Spatial_grass')):continue
    xf=ob.matrix_world.copy(); inv=xf.inverted()
    for v in ob.data.vertices:
        w=xf@v.co; w.z+=delta(w.x,w.y); v.co=inv@w
    ob.data.update();adjusted.append(ob.name)
newMesh=bpy.data.meshes.new('OriginalMountainTerrain')
newMesh.from_pydata(verts,[],faces);newMesh.update()
uv=newMesh.uv_layers.new(name='UVMap')
for poly in newMesh.polygons:
    poly.use_smooth=True
    for li in poly.loop_indices:
        v=newMesh.vertices[newMesh.loops[li].vertex_index].co
        uv.data[li].uv=((v.x+123.529411)/247.058822,(v.y+123.573883)/247.058822)
for mat in ground.data.materials:newMesh.materials.append(mat)
ground.data=newMesh;ground.matrix_world=Matrix.Identity(4);ground.name='NearMeadow_OriginalMountain'
out=PROJECT/'Assets/Resources/Worlds/MountainWorld.fbx';out.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.fbx(filepath=str(out),use_selection=True,object_types={'MESH'},use_mesh_modifiers=True,mesh_smooth_type='FACE',use_tspace=True,path_mode='AUTO',axis_forward='-Z',axis_up='Y',bake_space_transform=True,add_leaf_bones=False)
report={'source':str(SOURCE),'sourceObject':'Rolling meadow ground.001','groundHeightSamples':samples,'plantsAdjusted':adjusted,'output':str(out),'bytes':out.stat().st_size}
(PROJECT/'_compile_test/mountain-export.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
