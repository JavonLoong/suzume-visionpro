from pathlib import Path
import ast,json,hashlib,sys,numpy as np,bpy,bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).parent;O=R/'poster-left-steel-v44';source=R/'poster-lower-clouds-v43/Suzume_dual_scene_lower_clouds_v43.blend';native=O/'Suzume_dual_scene_left_steel_v44.blend'
D=json.loads((O/'steel-geometry-v44.json').read_text());old=json.loads((O/'source-steel-v44.json').read_text())['objects'];maskdata=np.load(O/'steel-removal-v44.npz');newnames={q['name'] for q in D['members']};changed=newnames|{q['name'] for q in old}
assert hashlib.sha256(source.read_bytes()).hexdigest()==D['sourceNativeSha256']
if '--final' not in sys.argv:
    for filename,names in [('verify_render_poster_v38.py',['tree_hash','movie_snapshot']),('verify_render_horizon_v42.py',['scene_snapshot'])]:
        tree=ast.parse((R/filename).read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'snapshot helpers','exec'))
    bpy.ops.wm.open_mainfile(filepath=str(source));movie_before=movie_snapshot();poster_before=scene_snapshot('Official poster courtyard v38');night_before=scene_snapshot('Night meadow through the door');groups_before={g.name:tree_hash(g) for g in bpy.data.node_groups}
    s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1);retained={};changes=[]
    for row in old:
        ob=s.objects[row['name']];m=ob.data;remove=maskdata[row['key']];v=np.empty((len(m.vertices),3),'f4');m.vertices.foreach_get('co',v.ravel());ix=np.empty(len(m.loops),np.int32);m.loops.foreach_get('vertex_index',ix);faces=ix.reshape(-1,3);keep=np.repeat(~remove,3);chosen=faces[~remove].ravel();normals=np.empty((len(m.corner_normals),3),'f4');m.corner_normals.foreach_get('vector',normals.ravel())
        mesh=bpy.data.meshes.new(m.name+' left replaced v44');points=v[chosen];mesh.from_pydata(points.tolist(),[],np.arange(len(points)).reshape(-1,3).tolist());mesh.update()
        for material in m.materials:mesh.materials.append(material)
        for layer in m.uv_layers:
            uv=np.empty((len(layer.data),2),'f4');layer.data.foreach_get('uv',uv.ravel());target=mesh.uv_layers.new(name=layer.name);target.data.foreach_set('uv',uv[keep].ravel())
        mesh.normals_split_custom_set(normals[keep].tolist());ob.data=mesh;retained[ob.name]=hashlib.sha256(points.tobytes()).hexdigest();changes.append({'name':ob.name,'removedTriangles':int(remove.sum()),'retainedTriangles':int((~remove).sum())})
    def linear(code):
        a=np.array([(code>>16)&255,(code>>8)&255,code&255])/255;return np.where(a<=.04045,a/12.92,((a+.055)/1.055)**2.4)
    materials=[]
    for index,(label,code,multiplier) in enumerate([('weathered grey brown steel',0xaca38c,[2.1,1.35,.80]),('pale exposed paint edge',0xe9dfc9,[1.18,1.03,.85]),('recessed dark web',0x797567,[1.95,1.25,.83]),('grounded concrete',0x746f58,[1,1,1])]):
        m=bpy.data.materials.new('Poster left '+label+' v44');m.use_nodes=True;base=np.minimum(linear(code)*multiplier,.97);m.diffuse_color=(*base,1);nodes=m.node_tree.nodes;links=m.node_tree.links;bs=nodes.get('Principled BSDF')
        geo=nodes.new('ShaderNodeNewGeometry');noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=7;noise.inputs['Detail'].default_value=4;noise.inputs['Roughness'].default_value=.72;links.new(geo.outputs['Position'],noise.inputs['Vector']);ramp=nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.22;ramp.color_ramp.elements[0].color=(*(.60*base),1);ramp.color_ramp.elements[1].position=.72;ramp.color_ramp.elements[1].color=(*np.minimum(base*1.12,1),1);links.new(noise.outputs['Fac'],ramp.inputs[0]);links.new(ramp.outputs[0],bs.inputs['Base Color']);bs.inputs['Roughness'].default_value=.80;bs.inputs['Metallic'].default_value=0 if index==3 else .07
        fine=nodes.new('ShaderNodeTexNoise');fine.inputs['Scale'].default_value=105;fine.inputs['Detail'].default_value=2;links.new(geo.outputs['Position'],fine.inputs['Vector']);bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.12;bump.inputs['Distance'].default_value=.002;links.new(fine.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs['Normal'],bs.inputs['Normal']);materials.append(m)
    collection=bpy.data.collections.new('Poster observed left steelwork v44');s.collection.children.link(collection)
    for rec in D['members']:
        mesh=bpy.data.meshes.new(rec['name']+' closed mesh');mesh.from_pydata(rec['verticesNative'],[],rec['triangles']);mesh.update()
        for mat in materials:mesh.materials.append(mat)
        mesh.polygons.foreach_set('material_index',np.array(rec['materialIndices'],np.int32));ob=bpy.data.objects.new(rec['name'],mesh);collection.objects.link(ob);ob['poster_steel_revision']=44;ob['unobserved_depth_inferred']=True
    s['poster_left_steel_revision']=44;s.render.use_border=False;s.render.use_crop_to_border=False;s.render.resolution_x=708;s.render.resolution_y=1000;s.render.resolution_percentage=100;s.cycles.samples=28;s.cycles.use_denoising=True;bpy.ops.wm.save_as_mainfile(filepath=str(native));sha=hashlib.sha256(native.read_bytes()).hexdigest();material_names={m.name for m in materials}
    bpy.ops.wm.open_mainfile(filepath=str(native));assert movie_before==movie_snapshot();assert night_before==scene_snapshot('Night meadow through the door');poster_after=scene_snapshot('Official poster courtyard v38');poster_after['materials']={k:v for k,v in poster_after['materials'].items() if k not in material_names};assert poster_before==poster_after;assert groups_before=={g.name:tree_hash(g) for g in bpy.data.node_groups}
    s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1);bpy.context.view_layer.update();closed=[]
    for name,expected in retained.items():
        m=s.objects[name].data;v=np.empty((len(m.vertices),3),'f4');m.vertices.foreach_get('co',v.ravel());assert hashlib.sha256(v.tobytes()).hexdigest()==expected
    for q in D['members']:
        m=s.objects[q['name']].data;v=np.empty((len(m.vertices),3),'f4');m.vertices.foreach_get('co',v.ravel());error=float(np.max(abs(v-np.array(q['verticesNative']))));assert error<2e-6
        bm=bmesh.new();bm.from_mesh(m);bad=sum(not edge.is_manifold for edge in bm.edges);volume=bm.calc_volume();bm.free();assert bad==0 and volume>0,(q['name'],bad,volume);closed.append({'name':q['name'],'triangles':len(m.polygons),'nonManifoldEdges':bad,'signedVolume':volume,'maximumVertexErrorMeters':error})
    # Verify solid overlaps at all intended supports, not just projected crossings.
    members={q['name']:q for q in D['members']};vertices={n:np.array(q['verticesNative']) for n,q in members.items()};bounds={n:[v.min(0),v.max(0)] for n,v in vertices.items()};trees={n:BVHTree.FromPolygons(q['verticesNative'],q['triangles'],all_triangles=True) for n,q in members.items()};direction=Vector((.237,.579,.780)).normalized()
    def inside(name,p):
        origin=Vector(p);hits=0
        for _ in range(50):
            point,normal,index,distance=trees[name].ray_cast(origin,direction,100)
            if point is None:break
            hits+=1;origin=point+direction*1e-5
        return bool(hits%2)
    def intersects(a,b):
        for source_name,target in [(a,b),(b,a)]:
            lo,hi=bounds[target];pts=vertices[source_name];pts=pts[np.all((pts>lo-1e-5)&(pts<hi+1e-5),axis=1)]
            for point in pts:
                if inside(target,point):return {'verified':True,'insidePoint':point.tolist(),'source':source_name,'inside':target}
            # Thin intersecting webs can overlap without either solid having
            # a corner inside the other. Confirm an interior point of both.
            line=np.array(members[source_name]['centerlineNative']);samples=np.concatenate([line[:-1]*(1-t)+line[1:]*t for t in [.2,.4,.6,.8]])
            samples=samples[np.all((samples>lo-1e-5)&(samples<hi+1e-5),axis=1)]
            for point in samples:
                if inside(source_name,point) and inside(target,point):return {'verified':True,'sharedInteriorPoint':point.tolist(),'source':source_name,'inside':target}
        return {'verified':False}
    prefix=lambda n:'Poster left '+n+' v44'
    pairs=[]
    for post in ['outer splayed I-column','middle bowed I-column','back I-column']:
        pairs += [(prefix(post),prefix(post+' footing'))]
        for beam in ['long upper tie','long lower tie']:pairs.append((prefix(post),prefix(beam)))
    pairs += [(prefix('outer splayed I-column'),prefix('upper broken tie')),(prefix('middle bowed I-column'),prefix('first broken bowed beam')),(prefix('middle bowed I-column'),prefix('second broken bowed beam')),(prefix('back I-column'),prefix('second broken bowed beam'))]
    for q in D['members']:
        for link in q.get('weldExtensions',[]):pairs.append((q['name'],link['target']))
    connection_rows=[{'a':a,'b':b,**intersects(a,b)} for a,b in dict.fromkeys(pairs)];(O/'connections-v44.json').write_text(json.dumps({'revision':44,'checks':connection_rows,'allCheckedConnectionsIntersect':all(q['verified'] for q in connection_rows)},indent=2),encoding='utf-8')
    assert all(q['verified'] for q in connection_rows),[(q['a'],q['b']) for q in connection_rows if not q['verified']]
    report={'revision':44,'sourceNativeSha256':D['sourceNativeSha256'],'nativeSha256':sha,'freshReopenVerified':True,'movieStatePreservedExactly':True,'nightScenePreservedExactly':True,'otherPosterObjectsMaterialsCameraLightingPreserved':True,'sharedNodeGroupsPreserved':True,'retainedOriginalSteelCoordinatesPreserved':True,'changedOriginalMeshes':changes,'addedMembers':closed,'checkedPhysicalJoints':len(connection_rows),'allCheckedJointsOverlap':True,'posterObjectCount':len(s.objects),'browserRuntimeVerified':False,'oneToOneComplete':False};(O/'verification-v44.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print('LEFT_STEEL_44_NATIVE_VERIFIED',sha,flush=True)
    s.render.resolution_x=1416;s.render.resolution_y=2000;s.cycles.samples=24;s.render.use_border=True;s.render.use_crop_to_border=True;s.render.border_min_x=0;s.render.border_max_x=300/708;s.render.border_min_y=.275;s.render.border_max_y=.66;s.render.filepath=str(O/'left-steel-trial-v44.png');bpy.ops.render.render(write_still=True);print('LEFT_STEEL_44_TRIAL_DONE',flush=True)
else:
    report=json.loads((O/'verification-v44.json').read_text());assert hashlib.sha256(native.read_bytes()).hexdigest()==report['nativeSha256'];bpy.ops.wm.open_mainfile(filepath=str(native));s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1)
    s.render.use_border=False;s.render.use_crop_to_border=False;s.render.resolution_x=708;s.render.resolution_y=1000;s.render.resolution_percentage=100;s.cycles.samples=28;s.cycles.use_denoising=True;s.render.filepath=str(O/'poster-front-v44.png');bpy.ops.render.render(write_still=True);print('LEFT_STEEL_44_FRONT_DONE',flush=True)
    s.camera.location=(-9,-12,4);s.camera.rotation_euler=(Vector((0,2,3))-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.lens=30;s.render.resolution_x=720;s.render.resolution_y=468;s.cycles.samples=24;s.render.filepath=str(O/'poster-oblique-v44.png');bpy.ops.render.render(write_still=True);print('LEFT_STEEL_44_OBLIQUE_DONE',flush=True)
