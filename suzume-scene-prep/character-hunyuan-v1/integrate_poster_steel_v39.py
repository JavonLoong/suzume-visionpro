from pathlib import Path
import bpy,json,numpy as np,hashlib,sys
R=Path(__file__).parent;O=R/'poster-steel-v39';source=R/'poster-v38/Suzume_dual_scene_v38.blend'
D=json.loads((O/'steel-geometry-v39.json').read_text());old=json.loads((O/'source-steel-v39.json').read_text());maskdata=np.load(O/'steel-removal-v39.npz')
bpy.ops.wm.open_mainfile(filepath=str(source));s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1);bpy.context.view_layer.update()
def fingerprint(o):
    a=np.empty(len(o.data.vertices)*3,np.float32);o.data.vertices.foreach_get('co',a);faces=np.empty(len(o.data.loops),np.int32);o.data.loops.foreach_get('vertex_index',faces)
    return hashlib.sha256(a.tobytes()+faces.tobytes()+np.array(o.matrix_world,dtype='<f4').tobytes()).hexdigest()
changed_names={q['name'] for q in old if maskdata[q['key']].any()}
unchanged={o.name:fingerprint(o) for o in s.objects if o.type=='MESH' and o.name not in changed_names}
changes=[]
for row in old:
    remove=maskdata[row['key']]
    if not remove.any():continue
    o=s.objects[row['name']];mesh=o.data
    local=np.empty((len(mesh.vertices),3),np.float32);mesh.vertices.foreach_get('co',local.ravel())
    ids=np.empty(len(mesh.loops),np.int32);mesh.loops.foreach_get('vertex_index',ids);faces=ids.reshape(-1,3);chosen=faces[~remove].ravel()
    loop_keep=np.repeat(~remove,3);normals=np.empty((len(mesh.corner_normals),3),np.float32);mesh.corner_normals.foreach_get('vector',normals.ravel());assert len(normals)==len(loop_keep)
    new=bpy.data.meshes.new(mesh.name+' — selected members removed v39');new.from_pydata(local[chosen].tolist(),[],np.arange(len(chosen)).reshape(-1,3).tolist());new.update()
    for material in mesh.materials:new.materials.append(material)
    for layer in mesh.uv_layers:
        uv=np.empty((len(layer.data),2),np.float32);layer.data.foreach_get('uv',uv.ravel());target=new.uv_layers.new(name=layer.name);target.data.foreach_set('uv',uv[loop_keep].ravel())
    new.normals_split_custom_set(normals[loop_keep].tolist());o.data=new
    changes.append({'object':o.name,'removedTriangles':int(remove.sum()),'retainedTriangles':int((~remove).sum()),'unchangedRetainedCoordinates':True})
def linear(code):
    rgb=np.array([(code>>16)&255,(code>>8)&255,code&255])/255
    return np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4)
materials=[]
for label,code in [('Warm weathered steel',0x9b835d),('Worn pale flange edges',0xd3c6a3),('Dark recessed web',0x796648),('Grounded aged concrete',0x746f58)]:
    m=bpy.data.materials.new('Poster '+label+' v39');m.use_nodes=True;nodes=m.node_tree.nodes;links=m.node_tree.links;bs=nodes.get('Principled BSDF');base=linear(code)
    if 'concrete' not in label:base=np.minimum(base*np.array([2.1,1.28,.85]),.97)
    m.diffuse_color=(*base,1)
    geo=nodes.new('ShaderNodeNewGeometry');noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=5;noise.inputs['Detail'].default_value=3;noise.inputs['Roughness'].default_value=.72;links.new(geo.outputs['Position'],noise.inputs['Vector'])
    ramp=nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.25;ramp.color_ramp.elements[0].color=(*(.57*base),1);ramp.color_ramp.elements[1].position=.70;ramp.color_ramp.elements[1].color=(*np.minimum(base*1.18,1),1);links.new(noise.outputs['Fac'],ramp.inputs[0]);links.new(ramp.outputs[0],bs.inputs['Base Color'])
    bs.inputs['Roughness'].default_value=.82;bs.inputs['Metallic'].default_value=0 if 'concrete' in label else .08
    fine=nodes.new('ShaderNodeTexNoise');fine.inputs['Scale'].default_value=100;fine.inputs['Detail'].default_value=2;links.new(geo.outputs['Position'],fine.inputs['Vector'])
    bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.12;bump.inputs['Distance'].default_value=.002;links.new(fine.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs['Normal'],bs.inputs['Normal']);materials.append(m)
col=bpy.data.collections.new('Poster observed right steelwork v39');s.collection.children.link(col)
for rec in D['members']:
    mesh=bpy.data.meshes.new(rec['name']+' closed geometry v39');mesh.from_pydata(rec['verticesNative'],[],rec['triangles']);mesh.update()
    for mat in materials:mesh.materials.append(mat)
    for p,idx in zip(mesh.polygons,rec['materialIndices']):p.material_index=idx
    ob=bpy.data.objects.new(rec['name']+' v39',mesh);col.objects.link(ob);ob['poster_steel_kind']=rec['kind'];ob['reference_depth_inferred']=True
bpy.context.view_layer.update()
for name,value in unchanged.items():assert fingerprint(bpy.data.objects[name])==value,name
s['poster_steel_revision']=39;s.render.use_border=False;s.render.use_crop_to_border=False;s.render.resolution_x=708;s.render.resolution_y=1000;s.render.resolution_percentage=100;s.cycles.samples=28;s.cycles.use_denoising=True
native=O/'Suzume_dual_scene_steel_v39.blend';bpy.ops.wm.save_as_mainfile(filepath=str(native))
report={'revision':39,'sourceNativeSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'nativeSha256':hashlib.sha256(native.read_bytes()).hexdigest(),'posterScene':s.name,'changedOriginalMeshes':changes,'unchangedPosterMeshHashes':unchanged,'addedMembers':len(D['members']),'addedTriangles':sum(len(q['triangles']) for q in D['members']),'allAddedMembersClosed':True,'movieAndNightScenesUntouched':True,'outerRibSeatedInsideExistingRoof':True,'oneToOneComplete':False}
(O/'integration-v39.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print('POSTER_39_SAVED',len(D['members']),flush=True)
if '--trial' in sys.argv:
    s.render.resolution_x=424;s.render.resolution_y=600;s.cycles.samples=16;s.render.filepath=str(O/'poster-trial-v39.png');bpy.ops.render.render(write_still=True);print('POSTER_39_TRIAL_DONE',flush=True)
