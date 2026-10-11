"""Correct native display conversion on existing poster surface pigments."""
from pathlib import Path
import bpy,json,hashlib,numpy as np,sys
R=Path(__file__).parent;O=R/'poster-v38'
bpy.ops.wm.open_mainfile(filepath=str(O/'Suzume_dual_scene_restored_v38.blend'))
s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1)
source=json.loads((O/'restoration-v38.json').read_text())
lut=bpy.data.images['Signed inverse AgX data v28'];N=65
assert list(lut.size)==[N*N,N] and lut.packed_file
assert abs(s.view_settings.exposure-.8)<1e-6
g=bpy.data.node_groups.new('Poster source color to native AgX v38','ShaderNodeTree')
g.interface.new_socket(name='Source linear RGB',in_out='INPUT',socket_type='NodeSocketVector')
g.interface.new_socket(name='Native scene RGB',in_out='OUTPUT',socket_type='NodeSocketVector')
nodes=g.nodes;links=g.links;inp=nodes.new('NodeGroupInput');out=nodes.new('NodeGroupOutput')
def feed(value,socket):
    if isinstance(value,(int,float)):socket.default_value=value
    else:links.new(value,socket)
def op(kind,a,b=None):
    n=nodes.new('ShaderNodeMath');n.operation=kind;feed(a,n.inputs[0])
    if b is not None:feed(b,n.inputs[1])
    return n.outputs[0]
def xyz(a,b,c):
    n=nodes.new('ShaderNodeCombineXYZ')
    for v,p in zip([a,b,c],n.inputs):feed(v,p)
    return n.outputs[0]
def tex(uv):
    n=nodes.new('ShaderNodeTexImage');n.image=lut;n.interpolation='Linear';n.extension='EXTEND';links.new(uv,n.inputs['Vector']);return n.outputs['Color']
split=nodes.new('ShaderNodeSeparateXYZ');links.new(inp.outputs[0],split.inputs[0])
def srgb(c):
    c=op('MAXIMUM',c,0);bright=op('GREATER_THAN',c,.0031308)
    lo=op('MULTIPLY',c,12.92);hi=op('SUBTRACT',op('MULTIPLY',op('POWER',c,1/2.4),1.055),.055)
    return op('MINIMUM',op('ADD',lo,op('MULTIPLY',bright,op('SUBTRACT',hi,lo))),1)
r,gg,b=[srgb(split.outputs[i]) for i in range(3)]
tile=op('MULTIPLY',b,N-1);t0=op('FLOOR',tile);t1=op('MINIMUM',op('ADD',t0,1),N-1);f=op('SUBTRACT',tile,t0)
xx=op('ADD',op('MULTIPLY',r,N-1),.5);yy=op('DIVIDE',op('ADD',op('MULTIPLY',gg,N-1),.5),N)
uv=lambda t:xyz(op('DIVIDE',op('ADD',op('MULTIPLY',t,N),xx),N*N),yy,0)
mix=nodes.new('ShaderNodeMixRGB');mix.blend_type='MIX';mix.use_clamp=False;links.new(f,mix.inputs[0]);links.new(tex(uv(t0)),mix.inputs[1]);links.new(tex(uv(t1)),mix.inputs[2]);links.new(mix.outputs[0],out.inputs[0])
g['purpose']='Restore existing reference-painted colors under native AgX; no source image changes or new projected geometry.'

def camera_glossy(nodes,links):
    path=nodes.new('ShaderNodeLightPath');factor=nodes.new('ShaderNodeMath');factor.operation='MAXIMUM'
    links.new(path.outputs['Is Camera Ray'],factor.inputs[0]);links.new(path.outputs['Is Glossy Ray'],factor.inputs[1]);return factor.outputs[0]
records=[];mats=set(m for o in s.objects if o.type=='MESH' for m in o.data.materials if m)
film=bpy.data.scenes['Daytime circular hotel'];film_mats=set(m for o in film.objects if o.type=='MESH' for m in o.data.materials if m)
assert not (mats&film_mats)
for mat in mats:
    if not mat.use_nodes:continue
    nd=mat.node_tree.nodes;ln=mat.node_tree.links
    output=next((n for n in nd if n.type=='OUTPUT_MATERIAL' and n.is_active_output),None)
    if not output or not output.inputs['Surface'].is_linked:continue
    original=output.inputs['Surface'].links[0].from_socket;em=original.node
    if em.type!='EMISSION':continue
    group=nd.new('ShaderNodeGroup');group.node_tree=g
    color=em.inputs['Color']
    if color.is_linked:ln.new(color.links[0].from_socket,group.inputs[0])
    else:group.inputs[0].default_value=color.default_value[:3]
    corrected=nd.new('ShaderNodeEmission');corrected.name='Poster display-calibrated pigments v38';corrected.inputs['Strength'].default_value=1;ln.new(group.outputs[0],corrected.inputs['Color'])
    blend=nd.new('ShaderNodeMixShader');ln.new(camera_glossy(nd,ln),blend.inputs[0]);ln.new(original,blend.inputs[1]);ln.new(corrected.outputs[0],blend.inputs[2]);ln.new(blend.outputs[0],output.inputs['Surface'])
    mat['poster_display_revision']=38;records.append(mat.name)
nd=s.world.node_tree.nodes;ln=s.world.node_tree.links;output=nd['World Output'];original=output.inputs['Surface'].links[0].from_socket;env=nd['Environment Texture']
group=nd.new('ShaderNodeGroup');group.node_tree=g;ln.new(env.outputs['Color'],group.inputs[0])
bg=nd.new('ShaderNodeBackground');bg.name='Poster visible sky v38';bg.inputs['Strength'].default_value=1;ln.new(group.outputs[0],bg.inputs['Color'])
blend=nd.new('ShaderNodeMixShader');ln.new(camera_glossy(nd,ln),blend.inputs[0]);ln.new(original,blend.inputs[1]);ln.new(bg.outputs[0],blend.inputs[2]);ln.new(blend.outputs[0],output.inputs['Surface'])
s.world['poster_display_revision']=38
# All movie meshes remain byte-identical to the independently saved v37.
bpy.context.window.scene=film;film.frame_set(72);bpy.context.view_layer.update()
for name,expected in source['movieMeshHashes'].items():
    obj=bpy.data.objects[name];a=np.empty(len(obj.data.vertices)*3,np.float32);obj.data.vertices.foreach_get('co',a);M=np.array(obj.matrix_world,dtype='<f4')
    assert hashlib.sha256(a.tobytes()+M.tobytes()).hexdigest()==expected,name
bpy.context.window.scene=s;s.frame_set(1);s.render.resolution_x=424;s.render.resolution_y=600;s.cycles.samples=20
s['poster_display_revision']=38
native=O/'Suzume_dual_scene_v38.blend';bpy.ops.wm.save_as_mainfile(filepath=str(native))
audit={'revision':38,'nativeFile':native.name,'nativeSha256':hashlib.sha256(native.read_bytes()).hexdigest(),'posterMaterialsCorrected':records,'posterWorldCorrected':True,'unchangedOriginalImages':True,'newMeshCount':0,'movieGeometryPreservedExactly':True,'movieAndPosterMaterialsDisjoint':True,'originalIndirectLightingPreserved':True,'sourceCloudMeshes':len(source['clouds']),'oneToOneComplete':False}
(O/'integration-v38.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
print('POSTER_38_COLORS_SAVED',len(records),flush=True)
if '--render' in sys.argv:
    s.render.filepath=str(O/'poster-front-v38.png');bpy.ops.render.render(write_still=True);print('POSTER_38_FRONT_DONE',flush=True)
