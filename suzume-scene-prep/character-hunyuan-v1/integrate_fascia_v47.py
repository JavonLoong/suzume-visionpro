from pathlib import Path
import ast,hashlib,json,sys
import bpy,bmesh,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

R=Path(__file__).parent;O=R/'poster-fascia-v47';source=R/'poster-railings-v46/Suzume_dual_scene_railings_v46.blend';native=O/'Suzume_dual_scene_fascia_v47.blend'
D=json.loads((O/'fascia-geometry-v47.json').read_text());changed={q['name'] for q in D['members']}
if '--final' not in sys.argv:
    assert hashlib.sha256(source.read_bytes()).hexdigest()==D['sourceNativeSha256']
    for filename,names in [('verify_render_poster_v38.py',['tree_hash','movie_snapshot']),('verify_render_horizon_v42.py',['scene_snapshot'])]:
        tree=ast.parse((R/filename).read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'snapshot helpers','exec'))
    bpy.ops.wm.open_mainfile(filepath=str(source));movie_before=movie_snapshot();poster_before=scene_snapshot('Official poster courtyard v38');night_before=scene_snapshot('Night meadow through the door');groups_before={g.name:tree_hash(g) for g in bpy.data.node_groups}
    s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1)
    materials=[]
    for q in D['materials']:
        mat=bpy.data.materials.new(q['name']);mat.use_nodes=True;base=np.array(q['linearRGB']);mat.diffuse_color=(*base,1)
        n=mat.node_tree.nodes;l=mat.node_tree.links;bs=n.get('Principled BSDF');bs.inputs['Roughness'].default_value=q['roughness'];bs.inputs['Metallic'].default_value=0
        geo=n.new('ShaderNodeNewGeometry');noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=8;noise.inputs['Detail'].default_value=3;l.new(geo.outputs['Position'],noise.inputs['Vector']);ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.20;ramp.color_ramp.elements[0].color=(*(base*.83),1);ramp.color_ramp.elements[1].position=.80;ramp.color_ramp.elements[1].color=(*np.minimum(base*1.10,1),1);l.new(noise.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs[0],bs.inputs['Base Color']);materials.append(mat)
    col=bpy.data.collections.new('Poster left molded roof fascia v47');s.collection.children.link(col)
    for q in D['members']:
        mesh=bpy.data.meshes.new(q['name']+' closed section');mesh.from_pydata(q['verticesNative'],[],q['triangles']);mesh.update()
        for mat in materials:mesh.materials.append(mat)
        mesh.polygons.foreach_set('material_index',q['materialIndices']);ob=bpy.data.objects.new(q['name'],mesh);col.objects.link(ob);ob['poster_fascia_revision']=47;ob['hidden_section_inferred']=True
    s['poster_fascia_revision']=47;s.render.use_border=False;s.render.use_crop_to_border=False;s.render.resolution_x=708;s.render.resolution_y=1000;s.render.resolution_percentage=100;s.cycles.samples=28;s.cycles.use_denoising=True
    bpy.ops.wm.save_as_mainfile(filepath=str(native));sha=hashlib.sha256(native.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(native));assert movie_before==movie_snapshot();assert night_before==scene_snapshot('Night meadow through the door');after=scene_snapshot('Official poster courtyard v38')
    for q in D['materials']:after['materials'].pop(q['name'])
    assert poster_before==after;assert groups_before=={g.name:tree_hash(g) for g in bpy.data.node_groups}
    s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1);bpy.context.view_layer.update();closed=[];trees=[]
    slab=s.objects['Circular ruined hotel with exterior entrance solid mesh.021'];slabtree=BVHTree.FromPolygons([slab.matrix_world@v.co for v in slab.data.vertices],[p.vertices[:] for p in slab.data.polygons],all_triangles=True)
    for q in D['members']:
        m=s.objects[q['name']].data;v=np.array([p.co[:] for p in m.vertices]);faces=[p.vertices[:] for p in m.polygons];error=float(np.max(abs(v-np.array(q['verticesNative']))));assert error<2e-6
        bm=bmesh.new();bm.from_mesh(m);bad=sum(not e.is_manifold for e in bm.edges);volume=bm.calc_volume();bm.free();assert bad==0 and volume>0
        tree=BVHTree.FromPolygons(v,faces,all_triangles=True);trees.append(tree);pairs=tree.overlap(slabtree);assert pairs,(q['name'],'detached from original roof slab')
        closed.append({'name':q['name'],'triangles':len(faces),'nonManifoldEdges':bad,'signedVolume':volume,'maximumVertexErrorMeters':error,'slabIntersectingTrianglePairs':len(pairs)})
    joints=[]
    for i in range(len(trees)-1):
        pairs=trees[i].overlap(trees[i+1]);assert pairs;joints.append({'a':D['members'][i]['name'],'b':D['members'][i+1]['name'],'intersectingTrianglePairs':len(pairs)})
    report={'revision':47,'sourceNativeSha256':D['sourceNativeSha256'],'nativeSha256':sha,'freshReopenVerified':True,'movieStatePreservedExactly':True,'nightScenePreservedExactly':True,'allOriginalPosterObjectsMaterialsCameraLightingPreserved':True,'sharedNodeGroupsPreserved':True,'addedAssemblies':closed,'adjacentBayJoints':joints,'browserRuntimeVerified':False,'oneToOneComplete':False}
    (O/'verification-v47.json').write_text(json.dumps(report,indent=2));print('FASCIA_47_NATIVE_VERIFIED',sha,flush=True)
    s.render.resolution_x=2124;s.render.resolution_y=3000;s.cycles.samples=28;s.render.use_border=True;s.render.use_crop_to_border=True;s.render.border_min_x=0;s.render.border_max_x=300/708;s.render.border_min_y=.415;s.render.border_max_y=.505;s.render.filepath=str(O/'fascia-detail-v47.png');bpy.ops.render.render(write_still=True);print('FASCIA_47_DETAIL_DONE',flush=True)
else:
    report=json.loads((O/'verification-v47.json').read_text());assert hashlib.sha256(native.read_bytes()).hexdigest()==report['nativeSha256'];bpy.ops.wm.open_mainfile(filepath=str(native));s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1)
    s.render.use_border=False;s.render.use_crop_to_border=False;s.render.resolution_x=708;s.render.resolution_y=1000;s.render.resolution_percentage=100;s.cycles.samples=28;s.cycles.use_denoising=True;s.render.filepath=str(O/'poster-front-v47.png');bpy.ops.render.render(write_still=True);print('FASCIA_47_FRONT_DONE',flush=True)
    s.camera.location=(-9,-12,4);s.camera.rotation_euler=(Vector((0,2,3))-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.lens=30;s.render.resolution_x=720;s.render.resolution_y=468;s.cycles.samples=24;s.render.filepath=str(O/'poster-oblique-v47.png');bpy.ops.render.render(write_still=True);print('FASCIA_47_OBLIQUE_DONE',flush=True)
