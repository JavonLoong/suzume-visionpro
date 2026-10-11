from pathlib import Path
import ast,hashlib,json,sys
import bpy,bmesh,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

R=Path(__file__).parent;O=R/'poster-rooftops-v45'
source=R/'poster-left-steel-v44/Suzume_dual_scene_left_steel_v44.blend'
native=O/'Suzume_dual_scene_rooftops_v45.blend'
D=json.loads((O/'rooftop-geometry-v45.json').read_text());S=json.loads((O/'source-rooftops-v45.json').read_text());masks=np.load(O/'rooftop-removal-v45.npz')
old=[q for q in S['objects'] if masks[q['key']].any()];changed={q['name'] for q in old}|{q['name'] for q in D['members']}
assert hashlib.sha256(source.read_bytes()).hexdigest()==D['sourceNativeSha256']
if '--final' not in sys.argv:
    for filename,names in [('verify_render_poster_v38.py',['tree_hash','movie_snapshot']),('verify_render_horizon_v42.py',['scene_snapshot'])]:
        tree=ast.parse((R/filename).read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'snapshot helpers','exec'))
    bpy.ops.wm.open_mainfile(filepath=str(source));movie_before=movie_snapshot();poster_before=scene_snapshot('Official poster courtyard v38');night_before=scene_snapshot('Night meadow through the door');groups_before={g.name:tree_hash(g) for g in bpy.data.node_groups}
    s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1);retained={};changes=[]
    for row in old:
        ob=s.objects[row['name']];m=ob.data;remove=masks[row['key']];assert len(remove)==len(m.polygons) and all(len(p.vertices)==3 for p in m.polygons)
        v=np.empty((len(m.vertices),3),'f4');m.vertices.foreach_get('co',v.ravel());ix=np.empty(len(m.loops),np.int32);m.loops.foreach_get('vertex_index',ix);faces=ix.reshape(-1,3);keep=np.repeat(~remove,3);chosen=faces[~remove].ravel();normals=np.empty((len(m.corner_normals),3),'f4');m.corner_normals.foreach_get('vector',normals.ravel())
        mesh=bpy.data.meshes.new(m.name+' equipment replaced v45');points=v[chosen];mesh.from_pydata(points.tolist(),[],np.arange(len(points)).reshape(-1,3).tolist());mesh.update()
        for mat in m.materials:mesh.materials.append(mat)
        for layer in m.uv_layers:
            uv=np.empty((len(layer.data),2),'f4');layer.data.foreach_get('uv',uv.ravel());target=mesh.uv_layers.new(name=layer.name);target.data.foreach_set('uv',uv[keep].ravel())
        for attr in m.color_attributes:
            assert attr.domain in ['POINT','CORNER'];colors=np.empty((len(attr.data),4),'f4');attr.data.foreach_get('color',colors.ravel());target=mesh.color_attributes.new(name=attr.name,type=attr.data_type,domain=attr.domain);target.data.foreach_set('color',(colors[chosen] if attr.domain=='POINT' else colors[keep]).ravel())
        mesh.normals_split_custom_set(normals[keep].tolist());ob.data=mesh;retained[ob.name]=hashlib.sha256(points.tobytes()).hexdigest();changes.append({'name':ob.name,'removedTriangles':int(remove.sum()),'retainedTriangles':int((~remove).sum()),'retainedColorAttributes':[a.name for a in mesh.color_attributes]})
    mats=[]
    def linear(code):
        a=np.array([(code>>16)&255,(code>>8)&255,code&255])/255;return np.where(a<=.04045,a/12.92,((a+.055)/1.055)**2.4)
    for i,(label,code) in enumerate([('blue grey metal casing',0x879299),('pale edge and rim',0xb7bec2),('dark pipe and ladder',0x505657),('right house grey casing',0x879299)]):
        mat=bpy.data.materials.new('Poster rooftop '+label+' v45');mat.use_nodes=True;base=linear(code)*np.array([2.1,1.24,.93] if i==0 else [1.3,1.07,.9] if i==1 else [.756,.6944,.651] if i==3 else [1,1,1]);mat.diffuse_color=(*base,1);n=mat.node_tree.nodes;l=mat.node_tree.links;bs=n.get('Principled BSDF');bs.inputs['Roughness'].default_value=.82;bs.inputs['Metallic'].default_value=.12
        geo=n.new('ShaderNodeNewGeometry');noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=3.7;noise.inputs['Detail'].default_value=3;l.new(geo.outputs['Position'],noise.inputs['Vector']);ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.18;ramp.color_ramp.elements[0].color=(*(base*.70),1);ramp.color_ramp.elements[1].position=.82;ramp.color_ramp.elements[1].color=(*(base*1.10),1);l.new(noise.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs[0],bs.inputs['Base Color'])
        fine=n.new('ShaderNodeTexNoise');fine.inputs['Scale'].default_value=58;l.new(geo.outputs['Position'],fine.inputs['Vector']);bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.08;bump.inputs['Distance'].default_value=.002;l.new(fine.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],bs.inputs['Normal']);mats.append(mat)
    col=bpy.data.collections.new('Poster observed rooftop equipment v45');s.collection.children.link(col)
    for q in D['members']:
        mesh=bpy.data.meshes.new(q['name']+' solid assemblies');mesh.from_pydata(q['verticesNative'],[],q['triangles']);mesh.update()
        for mat in mats:mesh.materials.append(mat)
        mesh.polygons.foreach_set('material_index',np.array(q['materialIndices'],np.int32))
        # Smooth each curved tube or tank while preserving sharp edges of boxes.
        for p in mesh.polygons:p.use_smooth=False
        ob=bpy.data.objects.new(q['name'],mesh);col.objects.link(ob);ob['poster_rooftop_revision']=45;ob['unobserved_depth_inferred']=True
    s['poster_rooftop_revision']=45;s.render.use_border=False;s.render.use_crop_to_border=False;s.render.resolution_x=708;s.render.resolution_y=1000;s.render.resolution_percentage=100;s.cycles.samples=28;s.cycles.use_denoising=True
    bpy.ops.wm.save_as_mainfile(filepath=str(native));sha=hashlib.sha256(native.read_bytes()).hexdigest();material_names={m.name for m in mats}
    bpy.ops.wm.open_mainfile(filepath=str(native));assert movie_before==movie_snapshot();assert night_before==scene_snapshot('Night meadow through the door');after=scene_snapshot('Official poster courtyard v38');after['materials']={k:v for k,v in after['materials'].items() if k not in material_names};assert poster_before==after;assert groups_before=={g.name:tree_hash(g) for g in bpy.data.node_groups}
    s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1);bpy.context.view_layer.update();closed=[]
    for name,want in retained.items():
        m=s.objects[name].data;v=np.empty((len(m.vertices),3),'f4');m.vertices.foreach_get('co',v.ravel());assert hashlib.sha256(v.tobytes()).hexdigest()==want
    roof_vertices=[];roof_faces=[];offset=0
    for row in S['objects']:
        ob=s.objects[row['name']];m=ob.data;v=np.array([ob.matrix_world@p.co for p in m.vertices]);faces=np.array([list(p.vertices) for p in m.polygons]);roof_vertices.extend(v.tolist());roof_faces.extend((faces+offset).tolist());offset+=len(v)
    roof=BVHTree.FromPolygons(roof_vertices,roof_faces,all_triangles=True)
    for q in D['members']:
        m=s.objects[q['name']].data;v=np.empty((len(m.vertices),3),'f4');m.vertices.foreach_get('co',v.ravel());error=float(np.max(abs(v-np.array(q['verticesNative']))));assert error<2e-6
        bm=bmesh.new();bm.from_mesh(m);bad=sum(not e.is_manifold for e in bm.edges);volume=bm.calc_volume();bm.free();assert bad==0 and volume>0
        low=v[v[:,2]<6.54];probes=[]
        for p in low[::max(1,len(low)//8)]:
            hit=roof.ray_cast(Vector((float(p[0]),float(p[1]),6.70)),Vector((0,0,-1)),.6)[0];assert hit is not None and hit.z>=p[2]-.015,(q['name'],p,hit);probes.append({'bottom':p.tolist(),'roofTopZ':float(hit.z)})
        closed.append({'name':q['name'],'triangles':len(m.polygons),'parts':q['parts'],'nonManifoldEdges':bad,'signedVolume':volume,'maximumVertexErrorMeters':error,'roofSupportProbes':probes})
    report={'revision':45,'sourceNativeSha256':D['sourceNativeSha256'],'nativeSha256':sha,'freshReopenVerified':True,'movieStatePreservedExactly':True,'nightScenePreservedExactly':True,'otherPosterObjectsMaterialsCameraLightingPreserved':True,'sharedNodeGroupsPreserved':True,'retainedOriginalFacadeCoordinatesPreserved':True,'changedOriginalMeshes':changes,'addedAssemblies':closed,'roofSupportsVerified':True,'posterObjectCount':len(s.objects),'browserRuntimeVerified':False,'oneToOneComplete':False}
    (O/'verification-v45.json').write_text(json.dumps(report,indent=2));print('ROOF_45_NATIVE_VERIFIED',sha,flush=True)
    s.render.resolution_x=2124;s.render.resolution_y=3000;s.cycles.samples=24;s.render.use_border=True;s.render.use_crop_to_border=True;s.render.border_min_x=0;s.render.border_max_x=300/708;s.render.border_min_y=.415;s.render.border_max_y=.505;s.render.filepath=str(O/'rooftop-trial-v45.png');bpy.ops.render.render(write_still=True);print('ROOF_45_TRIAL_DONE',flush=True)
else:
    report=json.loads((O/'verification-v45.json').read_text());assert hashlib.sha256(native.read_bytes()).hexdigest()==report['nativeSha256'];bpy.ops.wm.open_mainfile(filepath=str(native));s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1)
    s.render.use_border=False;s.render.use_crop_to_border=False;s.render.resolution_x=708;s.render.resolution_y=1000;s.render.resolution_percentage=100;s.cycles.samples=28;s.cycles.use_denoising=True;s.render.filepath=str(O/'poster-front-v45.png');bpy.ops.render.render(write_still=True);print('ROOF_45_FRONT_DONE',flush=True)
    s.camera.location=(-9,-12,4);s.camera.rotation_euler=(Vector((0,2,3))-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.lens=30;s.render.resolution_x=720;s.render.resolution_y=468;s.cycles.samples=24;s.render.filepath=str(O/'poster-oblique-v45.png');bpy.ops.render.render(write_still=True);print('ROOF_45_OBLIQUE_DONE',flush=True)
