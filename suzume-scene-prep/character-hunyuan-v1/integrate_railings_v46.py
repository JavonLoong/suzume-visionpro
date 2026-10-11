from pathlib import Path
import ast,hashlib,json,sys
import bpy,bmesh,numpy as np
from mathutils import Vector,Matrix,Euler
from mathutils.bvhtree import BVHTree
R=Path(__file__).parent;O=R/'poster-railings-v46';source=R/'poster-rooftops-v45/Suzume_dual_scene_rooftops_v45.blend';native=O/'Suzume_dual_scene_railings_v46.blend'
D=json.loads((O/'railing-geometry-v46.json').read_text());S=json.loads((O/'source-railings-v46.json').read_text());masks=np.load(O/'railing-removal-v46.npz');old=[q for q in S['objects'] if masks[q['key']].any()];ivy_name='Individual three-dimensional ivy leaves.001';changed={q['name'] for q in old}|{q['name'] for q in D['members']}|{ivy_name}
assert hashlib.sha256(source.read_bytes()).hexdigest()==D['sourceNativeSha256']
if '--final' not in sys.argv:
    for filename,names in [('verify_render_poster_v38.py',['tree_hash','movie_snapshot']),('verify_render_horizon_v42.py',['scene_snapshot'])]:
        tree=ast.parse((R/filename).read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'snapshot helpers','exec'))
    bpy.ops.wm.open_mainfile(filepath=str(source));movie_before=movie_snapshot();poster_before=scene_snapshot('Official poster courtyard v38');night_before=scene_snapshot('Night meadow through the door');groups_before={g.name:tree_hash(g) for g in bpy.data.node_groups}
    s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1);retained={};changes=[]
    for row in old:
        ob=s.objects[row['name']];m=ob.data;remove=masks[row['key']];assert len(remove)==len(m.polygons) and all(len(p.vertices)==3 for p in m.polygons)
        v=np.empty((len(m.vertices),3),'f4');m.vertices.foreach_get('co',v.ravel());ix=np.empty(len(m.loops),np.int32);m.loops.foreach_get('vertex_index',ix);faces=ix.reshape(-1,3);keep=np.repeat(~remove,3);chosen=faces[~remove].ravel();normals=np.empty((len(m.corner_normals),3),'f4');m.corner_normals.foreach_get('vector',normals.ravel())
        mesh=bpy.data.meshes.new(m.name+' rail replaced v46');points=v[chosen];mesh.from_pydata(points.tolist(),[],np.arange(len(points)).reshape(-1,3).tolist());mesh.update()
        for mat in m.materials:mesh.materials.append(mat)
        for layer in m.uv_layers:
            uv=np.empty((len(layer.data),2),'f4');layer.data.foreach_get('uv',uv.ravel());target=mesh.uv_layers.new(name=layer.name);target.data.foreach_set('uv',uv[keep].ravel())
        assert len(m.color_attributes)==0
        mesh.normals_split_custom_set(normals[keep].tolist());ob.data=mesh;retained[ob.name]=hashlib.sha256(points.tobytes()).hexdigest();changes.append({'name':ob.name,'removedTriangles':int(remove.sum()),'retainedTriangles':int((~remove).sum())})
    mat=bpy.data.materials.new('Poster pale weathered guardrail v46');mat.use_nodes=True;a=np.array([233,223,201])/255;base=np.minimum(np.where(a<=.04045,a/12.92,((a+.055)/1.055)**2.4)*[1.18,1.03,.85],.95);mat.diffuse_color=(*base,1)
    n=mat.node_tree.nodes;l=mat.node_tree.links;bs=n.get('Principled BSDF');bs.inputs['Roughness'].default_value=.86;bs.inputs['Metallic'].default_value=.06
    geo=n.new('ShaderNodeNewGeometry');noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=18;noise.inputs['Detail'].default_value=3;l.new(geo.outputs['Position'],noise.inputs['Vector']);ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.23;ramp.color_ramp.elements[0].color=(*(base*.54),1);ramp.color_ramp.elements[1].position=.72;ramp.color_ramp.elements[1].color=(*np.minimum(base*1.05,1),1);l.new(noise.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs[0],bs.inputs['Base Color'])
    col=bpy.data.collections.new('Poster observed dense balcony railing v46');s.collection.children.link(col)
    for q in D['members']:
        mesh=bpy.data.meshes.new(q['name']+' solid sections');mesh.from_pydata(q['verticesNative'],[],q['triangles']);mesh.update();mesh.materials.append(mat);ob=bpy.data.objects.new(q['name'],mesh);col.objects.link(ob);ob['poster_railing_revision']=46;ob['unobserved_detail_inferred']=True
    # Restore instance colors by realizing this small leaf set only. Other
    # large forest/night instancers retain their existing memory policy.
    ivy=s.objects[ivy_name];ivy.data=ivy.data.copy();points=np.array([v.co[:] for v in ivy.data.vertices]);rotations=np.empty((len(points),3),'f4');ivy.data.attributes['instance_rotation'].data.foreach_get('vector',rotations.ravel());scales=np.empty((len(points),3),'f4');ivy.data.attributes['instance_scale'].data.foreach_get('vector',scales.ravel());original_scales=scales.copy();world=points@np.array(ivy.matrix_world)[:3,:3].T+np.array(ivy.matrix_world)[:3,3];angles=np.arctan2(world[:,0],world[:,1]);radii=np.linalg.norm(world[:,:2],axis=1);select=(world[:,2]>5.7)&(world[:,2]<7.05)&(radii>21.5)&(radii<24.5)&(angles>-.9)&(angles<-.19)
    scales[select]*=.32;ivy.data.attributes['instance_scale'].data.foreach_set('vector',scales.ravel());mod=next(m for m in ivy.modifiers if m.type=='NODES');mod.node_group.use_fake_user=True;mod.node_group=mod.node_group.copy();mod.node_group.name='Poster ivy colors realized v46';ivy_group=mod.node_group.name;mod.node_group.nodes['Realize Instances'].mute=False
    edits=[]
    for i in np.flatnonzero(select):
        before=Matrix.LocRotScale(Vector(points[i]),Euler(rotations[i],'XYZ').to_quaternion(),Vector(original_scales[i]));after=Matrix.LocRotScale(Vector(points[i]),Euler(rotations[i],'XYZ').to_quaternion(),Vector(scales[i]));edits.append({'index':int(i),'beforeColumnMajorThree':np.array(before).T.ravel().tolist(),'afterColumnMajorThree':np.array(after).T.ravel().tolist()})
    color_before=np.empty((len(points),4),'f4');ivy.data.color_attributes['instance_color'].data.foreach_get('color',color_before.ravel())
    s['poster_railing_revision']=46;s.render.use_border=False;s.render.use_crop_to_border=False;s.render.resolution_x=708;s.render.resolution_y=1000;s.render.resolution_percentage=100;s.cycles.samples=28;s.cycles.use_denoising=True
    bpy.ops.wm.save_as_mainfile(filepath=str(native));sha=hashlib.sha256(native.read_bytes()).hexdigest();newmat=mat.name
    bpy.ops.wm.open_mainfile(filepath=str(native));assert movie_before==movie_snapshot();assert night_before==scene_snapshot('Night meadow through the door');after=scene_snapshot('Official poster courtyard v38');after['materials'].pop(newmat);assert poster_before==after;assert groups_before=={g.name:tree_hash(g) for g in bpy.data.node_groups if g.name!=ivy_group}
    s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1);bpy.context.view_layer.update();closed=[]
    for name,want in retained.items():
        m=s.objects[name].data;v=np.empty((len(m.vertices),3),'f4');m.vertices.foreach_get('co',v.ravel());assert hashlib.sha256(v.tobytes()).hexdigest()==want
    rv=[];rf=[];offset=0
    for row in S['objects']:
        ob=s.objects[row['name']];m=ob.data;v=np.array([ob.matrix_world@p.co for p in m.vertices]);faces=np.array([list(p.vertices) for p in m.polygons]);rv.extend(v.tolist());rf.extend((faces+offset).tolist());offset+=len(v)
    roof=BVHTree.FromPolygons(rv,rf,all_triangles=True);support=[]
    for rec in D['supportPoints']:
        p=np.array(rec['point']);hit=roof.ray_cast(Vector((p[0],p[1],6.8)),Vector((0,0,-1)),.5)[0];assert hit is not None and hit.z>=p[2],(rec,hit);support.append({'bay':rec['bay'],'bottom':p.tolist(),'roofTopZ':float(hit.z)})
    for q in D['members']:
        m=s.objects[q['name']].data;v=np.empty((len(m.vertices),3),'f4');m.vertices.foreach_get('co',v.ravel());error=float(np.max(abs(v-np.array(q['verticesNative']))));assert error<2e-6
        bm=bmesh.new();bm.from_mesh(m);bad=sum(not e.is_manifold for e in bm.edges);volume=bm.calc_volume();bm.free();assert bad==0 and volume>0
        closed.append({'name':q['name'],'triangles':len(m.polygons),'closedParts':q['closedParts'],'uprights':q['uprights'],'nonManifoldEdges':bad,'signedVolume':volume,'maximumVertexErrorMeters':error})
    joints=[]
    for left,right in zip(D['members'][:-1],D['members'][1:]):
        a=BVHTree.FromPolygons(left['verticesNative'],left['triangles'],all_triangles=True);b=BVHTree.FromPolygons(right['verticesNative'],right['triangles'],all_triangles=True);pairs=a.overlap(b);assert pairs,(left['name'],right['name']);joints.append({'a':left['name'],'b':right['name'],'intersectingTrianglePairs':len(pairs)})
    ivy=s.objects[ivy_name];actual=np.empty_like(scales);ivy.data.attributes['instance_scale'].data.foreach_get('vector',actual.ravel());assert np.array_equal(actual,scales);assert np.array_equal(actual[~select],original_scales[~select]);colors=np.empty_like(color_before);ivy.data.color_attributes['instance_color'].data.foreach_get('color',colors.ravel());assert np.array_equal(colors,color_before)
    evaluated=ivy.evaluated_get(bpy.context.evaluated_depsgraph_get());leafmesh=evaluated.to_mesh();assert len(leafmesh.vertices)==len(points)*10;assert 'instance_color' in leafmesh.color_attributes;ca=leafmesh.color_attributes['instance_color'];evaluated_colors=np.empty((len(ca.data),4),'f4');ca.data.foreach_get('color',evaluated_colors.ravel());assert np.all(evaluated_colors[:,:3].max(1)>0);ivy_report={'sourceInstances':len(points),'resizedLeftRoofLeaves':int(select.sum()),'roofLeafScaleFactor':.32,'otherLeafScalesPreservedExactly':True,'leafColorsPreservedExactly':True,'realizedVertices':len(leafmesh.vertices),'realizedTriangles':len(leafmesh.polygons),'realizedColorsNonzero':True,'nodeGroupIsolatedFromMovie':True};evaluated.to_mesh_clear()
    (O/'ivy-scale-v46.json').write_text(json.dumps({'revision':46,'nativeSha256':sha,'sourceInstanceCount':len(points),'edits':edits},separators=(',',':')))
    report={'revision':46,'sourceNativeSha256':D['sourceNativeSha256'],'nativeSha256':sha,'freshReopenVerified':True,'movieStatePreservedExactly':True,'nightScenePreservedExactly':True,'otherPosterObjectsMaterialsCameraLightingPreserved':True,'sharedNodeGroupsPreserved':True,'retainedOriginalFacadeCoordinatesPreserved':True,'changedOriginalMeshes':changes,'addedAssemblies':closed,'roofSupportProbes':support,'adjacentBayJoints':joints,'ivyRepair':ivy_report,'posterObjectCount':len(s.objects),'browserRuntimeVerified':False,'oneToOneComplete':False}
    (O/'verification-v46.json').write_text(json.dumps(report,indent=2));print('RAIL_46_NATIVE_VERIFIED',sha,flush=True)
    s.render.resolution_x=2124;s.render.resolution_y=3000;s.cycles.samples=28;s.render.use_border=True;s.render.use_crop_to_border=True;s.render.border_min_x=0;s.render.border_max_x=300/708;s.render.border_min_y=.415;s.render.border_max_y=.505;s.render.filepath=str(O/'railing-trial-v46.png');bpy.ops.render.render(write_still=True);print('RAIL_46_TRIAL_DONE',flush=True)
else:
    report=json.loads((O/'verification-v46.json').read_text());assert hashlib.sha256(native.read_bytes()).hexdigest()==report['nativeSha256'];bpy.ops.wm.open_mainfile(filepath=str(native));s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1)
    s.render.use_border=False;s.render.use_crop_to_border=False;s.render.resolution_x=708;s.render.resolution_y=1000;s.render.resolution_percentage=100;s.cycles.samples=28;s.cycles.use_denoising=True;s.render.filepath=str(O/'poster-front-v46.png');bpy.ops.render.render(write_still=True);print('RAIL_46_FRONT_DONE',flush=True)
    s.camera.location=(-9,-12,4);s.camera.rotation_euler=(Vector((0,2,3))-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.lens=30;s.render.resolution_x=720;s.render.resolution_y=468;s.cycles.samples=24;s.render.filepath=str(O/'poster-oblique-v46.png');bpy.ops.render.render(write_still=True);print('RAIL_46_OBLIQUE_DONE',flush=True)
