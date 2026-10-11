"""Replace the movie steelwork with closed I-sections and isotropic corrosion."""
from pathlib import Path
import bpy,bmesh,json,math,hashlib,sys,numpy as np
R=Path(__file__).parent;O=R/'movie-steel-v25'
D=json.loads((O/'steel-geometry-v25.json').read_text(encoding='utf-8'))
bpy.ops.wm.open_mainfile(filepath=str(R/'movie-projection-v24/Suzume_scene_movie_projection_v24.blend'))
s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72);bpy.context.view_layer.update()
def fingerprint(o,evaluated=False):
    e=o.evaluated_get(bpy.context.evaluated_depsgraph_get()) if evaluated else o;mesh=e.to_mesh() if evaluated else o.data
    a=np.empty((len(mesh.vertices),3),np.float32);mesh.vertices.foreach_get('co',a.ravel());M=np.array(o.matrix_world);a=a@M[:3,:3].T+M[:3,3]
    if evaluated:e.to_mesh_clear()
    return hashlib.sha256(np.round(a,6).astype('<f4').tobytes()).hexdigest()
unchanged={o.name:fingerprint(o) for o in s.objects if o.type=='MESH' and not o.name.startswith('Broken radial dome steelwork solid mesh')}
removed=[]
for o in list(s.objects):
    if o.name.startswith('Broken radial dome steelwork solid mesh'):removed.append({'name':o.name,'faces':len(o.data.polygons)});bpy.data.objects.remove(o,do_unlink=True)
assert removed
def color(value):
    rgb=np.array([(value>>16)&255,(value>>8)&255,value&255])/255
    rgb=np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4);return (*rgb,1)
def steel_material(name,edge=False):
    m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=color(0x766048);nodes=m.node_tree.nodes;links=m.node_tree.links;nodes.clear()
    geo=nodes.new('ShaderNodeNewGeometry');geo.name='World position for isotropic corrosion'
    noise=nodes.new('ShaderNodeTexNoise');noise.name='Broad rust islands';noise.inputs['Scale'].default_value=3.5;noise.inputs['Detail'].default_value=4;noise.inputs['Roughness'].default_value=.7;links.new(geo.outputs['Position'],noise.inputs['Vector'])
    ramp=nodes.new('ShaderNodeValToRGB');ramp.name='Steel and oxide colors';ramp.color_ramp.elements.remove(ramp.color_ramp.elements[1])
    palette=[(.20,0x3b403c),(.40,0x655d4d),(.58,0x8a7756),(.78,0xa1774b)] if not edge else [(.20,0x41433b),(.40,0x6f6450),(.58,0x958265),(.78,0xa17a51)]
    for i,(pos,hexcode) in enumerate(palette):
        e=ramp.color_ramp.elements[0] if i==0 else ramp.color_ramp.elements.new(pos);e.position=pos;e.color=color(hexcode)
    links.new(noise.outputs['Fac'],ramp.inputs['Fac'])
    fine=nodes.new('ShaderNodeTexNoise');fine.name='Fine pitted metal';fine.inputs['Scale'].default_value=85;fine.inputs['Detail'].default_value=2;links.new(geo.outputs['Position'],fine.inputs['Vector'])
    bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.18;bump.inputs['Distance'].default_value=.006;links.new(fine.outputs['Fac'],bump.inputs['Height'])
    bs=nodes.new('ShaderNodeBsdfPrincipled');bs.inputs['Roughness'].default_value=.90;bs.inputs['Metallic'].default_value=.12;bs.inputs['Specular IOR Level'].default_value=.25;links.new(ramp.outputs['Color'],bs.inputs['Base Color']);links.new(bump.outputs['Normal'],bs.inputs['Normal'])
    out=nodes.new('ShaderNodeOutputMaterial');links.new(bs.outputs['BSDF'],out.inputs['Surface']);m['corrosion_space']='World coordinates, isotropic; no inherited streak image'
    return m
materials={'steel':steel_material('Film corroded I-section steel v25'),'edge':steel_material('Film exposed steel connections v25',True)}
m=bpy.data.materials.new('Film grounded concrete footings v25');m.use_nodes=True;m.diffuse_color=color(0x77766d);bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=m.diffuse_color;bs.inputs['Roughness'].default_value=.95;materials['concrete']=m
for role,hexcode in {'vine':0x536238,'leaf0':0x58752b,'leaf1':0x70953c,'leaf2':0xa1b359}.items():
    m=bpy.data.materials.new('Attached steel ivy '+role+' v25');m.use_nodes=True;m.diffuse_color=color(hexcode);bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=m.diffuse_color;bs.inputs['Roughness'].default_value=.9;materials[role]=m
col=bpy.data.collections.new('Movie steelwork v25 — complete radial structure');s.collection.children.link(col);parts=[];watertight=[]
for rec in D['meshes']:
    a=np.array(rec['positions']).reshape(-1,3)[:,[0,2,1]]*[1,-1,1];mesh=bpy.data.meshes.new(rec['name']+' geometry v25');mesh.from_pydata(a.tolist(),[],np.arange(len(a)).reshape(-1,3).tolist());mesh.update()
    if rec['uv']:
        layer=mesh.uv_layers.new(name='UVMap');uv=np.array(rec['uv'],np.float32).reshape(-1,2);ids=np.array([l.vertex_index for l in mesh.loops]);layer.data.foreach_set('uv',uv[ids].ravel())
    normals=np.array(rec['normals']).reshape(-1,3)[:,[0,2,1]]*[1,-1,1];mesh.normals_split_custom_set_from_vertices(normals.tolist());mesh.materials.append(materials[rec['material']])
    ob=bpy.data.objects.new(rec['name']+' v25',mesh);col.objects.link(ob);ob['steel_kind']=rec['metadata']['kind'];ob['steel_index']=rec['metadata']['index'];parts.append(ob)
    if ob['steel_kind'] in ['column','rib','observed-bow','observed-hanger']:
        bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-5);bad=sum(not e.is_manifold for e in bm.edges);bm.free();assert bad==0,(ob.name,bad);watertight.append(ob.name)
bpy.context.view_layer.update()
for name,value in unchanged.items():assert fingerprint(bpy.data.objects[name])==value,name
oldlight=next(q for q in json.loads((R/'movie-projection-v24/integration-v24.json').read_text(encoding='utf-8'))['lights'] if q['name']=='Soft courtyard fill on the movie facade v22')
fill=bpy.data.objects[oldlight['name']];ratio=2.5;target=np.array(oldlight['target']);pos=target+ratio*(np.array(oldlight['position'])-target)
fill.location=pos;fill.data.size=oldlight['dimensions'][0]*ratio;fill.data.size_y=oldlight['dimensions'][1]*ratio;fill.data.energy=oldlight['powerWatts']*ratio*ratio
newlight={**oldlight,'position':pos.tolist(),'dimensions':[fill.data.size,fill.data.size_y],'powerWatts':fill.data.energy,'scaleAboutFacadeTarget':ratio,'purpose':'Reduce local overexposure at the relocated steel column while retaining emitter radiance and angular size at the wall target.'}
baseline=json.loads((R/'movie-projection-v24/verification-v24.json').read_text(encoding='utf-8'))['characters'];characters={}
for name,row in baseline.items():assert fingerprint(bpy.data.objects[name],True)==row['worldHash'];characters[name]=row
s['movie_steel_revision']=25;s.render.use_border=False;s.render.resolution_x=720;s.render.resolution_y=468;s.render.resolution_percentage=100;s.cycles.samples=24;s.cycles.use_denoising=True
audit={'revision':25,'removed':removed,'newParts':len(parts),'newTriangles':sum(len(o.data.polygons) for o in parts),'closedStructuralSections':len(watertight),'attachedIvyLeaves':sum(o['steel_kind']=='ivy-leaf' for o in parts),'rightFacadeFill':newlight,'unchangedOtherMeshCount':len(unchanged),'unchangedOtherMeshHashes':unchanged,'characters':characters,'oneToOneComplete':False,'visualReviewPending':True}
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Suzume_scene_movie_steel_v25.blend'));(O/'integration-v25.json').write_text(json.dumps(audit,indent=2),encoding='utf-8');print('STEEL_25_SAVED',len(parts),'WATERTIGHT',len(watertight),'PRESERVED',len(unchanged),flush=True)
if '--render' in sys.argv:
    s.render.filepath=str(O/'movie-front-v25.png');bpy.ops.render.render(write_still=True)
