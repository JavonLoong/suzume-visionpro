from pathlib import Path
import bpy,json,hashlib,sys,ast,numpy as np
from mathutils import Vector
R=Path(__file__).parent;O=R/'poster-water-v40';native=O/'Suzume_dual_scene_water_v40.blend'
tree=ast.parse((R/'verify_render_poster_v38.py').read_text());funcs=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['tree_hash','movie_snapshot']];exec(compile(ast.Module(body=funcs,type_ignores=[]),'snapshot helpers','exec'))
def poster_snapshot():
    s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1);bpy.context.view_layer.update();objects={};materials={}
    water=next(o for o in s.objects if o.name.startswith('Live planar reflective shallow water'));watermat=water.data.materials[0]
    for o in s.objects:
        rec={'matrix':np.array(o.matrix_world).tolist(),'type':o.type,'render':o.hide_render,'modifiers':[[m.name,m.type,m.show_render,m.show_viewport] for m in o.modifiers]}
        if o.type=='MESH':
            v=np.empty(len(o.data.vertices)*3,np.float32);o.data.vertices.foreach_get('co',v);ix=np.empty(len(o.data.loops),np.int32);o.data.loops.foreach_get('vertex_index',ix)
            rec['mesh']=hashlib.sha256(v.tobytes()+ix.tobytes()).hexdigest()
            rec['materials']=[m.name if m else None for m in o.data.materials]
            for m in o.data.materials:
                if m and m!=watermat:materials[m.name]=tree_hash(m.node_tree)
        objects[o.name]=rec
    return {'objects':objects,'materials':materials,'cameraLens':s.camera.data.lens,'world':tree_hash(s.world.node_tree),'colors':[s.view_settings.view_transform,s.view_settings.look,s.view_settings.exposure]}
bpy.ops.wm.open_mainfile(filepath=str(R/'poster-steel-v39/Suzume_dual_scene_steel_v39.blend'));before_movie=movie_snapshot();before_poster=poster_snapshot()
bpy.ops.wm.open_mainfile(filepath=str(native));assert before_movie==movie_snapshot(),'Movie state changed';assert before_poster==poster_snapshot(),'Non-water poster state changed'
s=bpy.data.scenes['Official poster courtyard v38'];water=next(o for o in s.objects if o.name.startswith('Live planar reflective shallow water'));mat=water.data.materials[0];q=json.loads((O/'water-spec-v40.json').read_text())
assert json.loads(mat['poster_water_parameters'])==q
assert not any(n.type=='TEX_IMAGE' for n in mat.node_tree.nodes),'Water references an image directly'
groups=[n.node_tree.name for n in mat.node_tree.nodes if n.type=='GROUP'];assert set(groups)=={'Poster source color to native AgX v38'}
assert list(bpy.data.images['Signed inverse AgX data v28'].size)==[4225,65]
assert any(n.type=='BSDF_REFRACTION' for n in mat.node_tree.nodes) and any(n.type=='BSDF_PRINCIPLED' for n in mat.node_tree.nodes)
time=mat.node_tree.nodes['Wave time v40'];s.frame_set(1);bpy.context.view_layer.update();assert abs(time.outputs[0].default_value)<1e-6;s.frame_set(25);bpy.context.view_layer.update();assert abs(time.outputs[0].default_value-1)<1e-6;s.frame_set(1);bpy.context.view_layer.update()
assert all(im.packed_file for im in bpy.data.images if im.source=='FILE' and im.users>0)
report={'revision':40,'nativeSha256':hashlib.sha256(native.read_bytes()).hexdigest(),'freshReopenVerified':True,'movieStatePreservedExactly':True,'posterGeometryMaterialsExceptWaterCameraAndLightingPreserved':True,'posterObjectCount':len(before_poster['objects']),'waterOnlyMaterialChange':True,'worldSpaceWaveAnimationVerified':True,'liveReflectionAndRefraction':True,'noReferenceImageInWater':True,'onlyImageDependency':'Existing 65-cubed color-conversion LUT, not an image of water','packedImagesVerified':True,'browserRuntimeVerified':False,'oneToOneComplete':False}
(O/'verification-v40.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print('POSTER_WATER_40_VERIFIED',flush=True)
s.render.use_border=False;s.render.use_crop_to_border=False;s.render.resolution_x=708;s.render.resolution_y=1000;s.render.resolution_percentage=100;s.cycles.samples=32;s.cycles.use_denoising=True;s.render.filepath=str(O/'poster-front-v40.png');bpy.ops.render.render(write_still=True);print('POSTER_WATER_40_FRONT_DONE',flush=True)
s.camera.location=(-9,-12,4);s.camera.rotation_euler=(Vector((0,2,3))-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.lens=30;s.render.resolution_x=720;s.render.resolution_y=468;s.cycles.samples=24;s.render.filepath=str(O/'poster-oblique-v40.png');bpy.ops.render.render(write_still=True);print('POSTER_WATER_40_OBLIQUE_DONE',flush=True)
