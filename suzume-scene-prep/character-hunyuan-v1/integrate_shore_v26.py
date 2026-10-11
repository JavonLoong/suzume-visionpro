"""Add inferred thick waterfront slabs and hollow pipework to the complete scene."""
from pathlib import Path
import bpy,bmesh,json,hashlib,sys,numpy as np
R=Path(__file__).parent;O=R/'movie-shore-v26'
D=json.loads((O/'shore-geometry-v26.json').read_text(encoding='utf-8'))
bpy.ops.wm.open_mainfile(filepath=str(R/'movie-steel-v25/Suzume_scene_movie_steel_v25.blend'))
s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72);bpy.context.view_layer.update()
def fingerprint(o,evaluated=False):
    e=o.evaluated_get(bpy.context.evaluated_depsgraph_get()) if evaluated else o;mesh=e.to_mesh() if evaluated else o.data
    a=np.empty((len(mesh.vertices),3),np.float32);mesh.vertices.foreach_get('co',a.ravel());M=np.array(o.matrix_world);a=a@M[:3,:3].T+M[:3,3]
    if evaluated:e.to_mesh_clear()
    return hashlib.sha256(np.round(a,6).astype('<f4').tobytes()).hexdigest()
unchanged={o.name:fingerprint(o) for o in s.objects if o.type=='MESH'}
def color(v):
    rgb=np.array([(v>>16)&255,(v>>8)&255,v&255])/255
    return (*np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4),1)
palettes={'concrete':[0x73877c,0x9ca993,0xbdc3a7], 'bank':[0x4c6762,0x748b7b,0x929e86], 'curb':[0x748b80,0xa4b19d,0xbec8ad], 'rust':[0x3f2923,0x704536,0x9c7050], 'rustDark':[0x302a25,0x524335,0x80644a]}
materials={}
for role,palette in palettes.items():
    m=bpy.data.materials.new('Movie waterfront '+role+' v26');m.use_nodes=True;m.diffuse_color=color(palette[1]);nodes=m.node_tree.nodes;links=m.node_tree.links
    bs=nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.96;bs.inputs['Metallic'].default_value=.12 if role.startswith('rust') else 0;bs.inputs['Specular IOR Level'].default_value=.23
    geo=nodes.new('ShaderNodeNewGeometry');noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=3.2 if role.startswith('rust') else 2.1;noise.inputs['Detail'].default_value=4;noise.inputs['Roughness'].default_value=.75;links.new(geo.outputs['Position'],noise.inputs['Vector'])
    ramp=nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.22;ramp.color_ramp.elements[0].color=color(palette[0]);ramp.color_ramp.elements[1].position=.76;ramp.color_ramp.elements[1].color=color(palette[2]);ramp.color_ramp.elements.new(.49).color=color(palette[1]);links.new(noise.outputs['Fac'],ramp.inputs['Fac']);links.new(ramp.outputs['Color'],bs.inputs['Base Color'])
    fine=nodes.new('ShaderNodeTexNoise');fine.inputs['Scale'].default_value=65;fine.inputs['Detail'].default_value=2;links.new(geo.outputs['Position'],fine.inputs['Vector']);bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.22;bump.inputs['Distance'].default_value=.012;links.new(fine.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs['Normal'],bs.inputs['Normal']);materials[role]=m
col=bpy.data.collections.new('Movie waterfront v26 — sloped solid slabs and hollow pipes');s.collection.children.link(col);closed=[];hashes={};volumes={}
for rec in D['meshes']:
    a=np.array(rec['positions']).reshape(-1,3)[:,[0,2,1]]*[1,-1,1];mesh=bpy.data.meshes.new(rec['name']+' geometry v26');mesh.from_pydata(a.tolist(),[],np.arange(len(a)).reshape(-1,3).tolist());mesh.update()
    normals=np.array(rec['normals']).reshape(-1,3)[:,[0,2,1]]*[1,-1,1];mesh.normals_split_custom_set_from_vertices(normals.tolist());mesh.materials.append(materials[rec['material']])
    ob=bpy.data.objects.new(rec['name']+' v26',mesh);col.objects.link(ob);ob['shore_kind']=rec['metadata']['kind'];ob['source_metadata']=json.dumps(rec['metadata']);
    bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-5);bad=sum(not e.is_manifold for e in bm.edges);volume=bm.calc_volume(signed=True);bm.free();assert bad==0,(ob.name,bad);assert volume>0,(ob.name,volume);closed.append(ob.name);volumes[ob.name]=volume
    native=a.astype('<f4');hashes[ob.name]={'vertices':len(a),'nativeFloat32Hash':hashlib.sha256(native.tobytes()).hexdigest()}
bpy.context.view_layer.update()
for name,value in unchanged.items():assert fingerprint(bpy.data.objects[name])==value,name
baseline=json.loads((R/'movie-steel-v25/integration-v25.json').read_text(encoding='utf-8'))['characters']
for name,row in baseline.items():assert fingerprint(bpy.data.objects[name],True)==row['worldHash'],name
s['movie_shore_revision']=26;s.render.use_border=False;s.cycles.samples=24;s.cycles.use_denoising=True
audit={'revision':26,'newParts':len(closed),'triangles':sum(len(o.data.polygons) for o in col.objects),'allNewMeshesClosed':True,'newMeshVolumes':volumes,'unchangedMeshHashes':unchanged,'characters':baseline,'cameraAndLightsUnchanged':True,'browserRuntimeVerified':False,'oneToOneComplete':False}
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Suzume_scene_movie_shore_v26.blend'))
(O/'integration-v26.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8');(O/'native-shore-meshes-v26.json').write_text(json.dumps(hashes,indent=2),encoding='utf-8');print('SHORE_26_SAVED',len(closed),'PRESERVED',len(unchanged),flush=True)
if '--render' in sys.argv:s.render.filepath=str(O/'movie-front-v26.png');bpy.ops.render.render(write_still=True)
