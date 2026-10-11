"""Attach fixed reference pigments to existing physical plaster/stone faces."""
from pathlib import Path
import bpy, sys, json, math, hashlib, numpy as np
from mathutils import Vector
R=Path(__file__).parent;O=R/'movie-surfaces-v28';sys.path.insert(0,str(R))
from projection_geometry_v24 import bay_spec,center
q=json.loads((O/'surface-spec-v28.json').read_text(encoding='utf-8'));P=q['projection']
bpy.ops.wm.open_mainfile(filepath=str(R/'movie-lighting-v27/Suzume_scene_movie_lighting_v27.blend'))
s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72);bpy.context.view_layer.update()
baseline=json.loads((R/'movie-lighting-v27/integration-v27.json').read_text(encoding='utf-8'))

def fingerprint(o,evaluated=False):
    e=o.evaluated_get(bpy.context.evaluated_depsgraph_get()) if evaluated else o;m=e.to_mesh() if evaluated else o.data
    a=np.empty((len(m.vertices),3),np.float32);m.vertices.foreach_get('co',a.ravel());M=np.array(o.matrix_world);a=a@M[:3,:3].T+M[:3,3]
    if evaluated:e.to_mesh_clear()
    return hashlib.sha256(np.round(a,6).astype('<f4').tobytes()).hexdigest()

def topology(o):
    indices=np.empty(len(o.data.loops),np.int32);o.data.loops.foreach_get('vertex_index',indices)
    counts=np.empty(len(o.data.polygons),np.int32);o.data.polygons.foreach_get('loop_total',counts)
    return hashlib.sha256(indices.astype('<i4').tobytes()+counts.astype('<i4').tobytes()).hexdigest()

beforeTopology={o.name:topology(o) for o in s.objects if o.type=='MESH'}
source=bpy.data.images.load(str(O/'reference-opening.jpg'),check_existing=False);source.name='Film source v28 — unchanged';source.colorspace_settings.name='Non-Color';source.pack()
mask=bpy.data.images.load(str(O/'surface-validity-mask-v28.png'),check_existing=False);mask.name='Film foreground exclusion v28';mask.colorspace_settings.name='Non-Color';mask.pack()
pixels=np.load(O/'inverse-agx-lut-v28.npy');N=q['lutSize']
lut=bpy.data.images.new('Signed inverse AgX data v28',width=N*N,height=N,alpha=True,float_buffer=True)
lut.colorspace_settings.name='Non-Color';lut.pixels.foreach_set(pixels.ravel());lut.update()
lut.filepath_raw=str(O/'inverse-agx-lut-v28.exr');lut.file_format='OPEN_EXR';lut.save();lut.pack()

g=bpy.data.node_groups.new('Film v28 fixed world pigments','ShaderNodeTree')
g.interface.new_socket(name='Original Surface',in_out='INPUT',socket_type='NodeSocketShader')
g.interface.new_socket(name='Surface',in_out='OUTPUT',socket_type='NodeSocketShader')
nodes=g.nodes;links=g.links;inp=nodes.new('NodeGroupInput');out=nodes.new('NodeGroupOutput')
def feed(value,socket):
    if isinstance(value,(float,int,np.floating)):socket.default_value=float(value)
    else:links.new(value,socket)
def op(kind,a,b=None,label=None):
    n=nodes.new('ShaderNodeMath');n.operation=kind;n.label=label or kind;feed(a,n.inputs[0])
    if b is not None:feed(b,n.inputs[1])
    return n.outputs[0]
def xyz(a,b,c):
    n=nodes.new('ShaderNodeCombineXYZ')
    for val,socket in zip([a,b,c],n.inputs):feed(val,socket)
    return n.outputs[0]
def texture(im,uv,extension='CLIP'):
    n=nodes.new('ShaderNodeTexImage');n.image=im;n.interpolation='Linear';n.extension=extension;links.new(uv,n.inputs['Vector']);return n.outputs['Color']
geo=nodes.new('ShaderNodeNewGeometry');split=nodes.new('ShaderNodeSeparateXYZ');links.new(geo.outputs['Position'],split.inputs[0])
x=op('SUBTRACT',split.outputs['X'],P['cameraX']);y=op('ADD',split.outputs['Y'],P['distance']);z=op('SUBTRACT',split.outputs['Z'],P['cameraZ'])
c=math.cos(P['pitch']);sn=math.sin(P['pitch']);f=1656*P['lensMm']/36
depth=op('SUBTRACT',op('MULTIPLY',y,c),op('MULTIPLY',z,sn))
u=op('ADD',.5,op('MULTIPLY',op('DIVIDE',x,depth),f/2552))
v=op('ADD',.5,op('MULTIPLY',op('DIVIDE',op('ADD',op('MULTIPLY',y,sn),op('MULTIPLY',z,c)),depth),f/1656))
uv=xyz(u,v,0);ref=texture(source,uv);valid=texture(mask,uv)
rgb=nodes.new('ShaderNodeSeparateColor');rgb.mode='RGB';links.new(ref,rgb.inputs['Color'])
tile=op('MULTIPLY',rgb.outputs['Blue'],N-1);tile0=op('FLOOR',tile);tile1=op('MINIMUM',op('ADD',tile0,1),N-1);frac=op('SUBTRACT',tile,tile0)
xx=op('ADD',op('MULTIPLY',rgb.outputs['Red'],N-1),.5);yy=op('DIVIDE',op('ADD',op('MULTIPLY',rgb.outputs['Green'],N-1),.5),N)
def lutUV(t):return xyz(op('DIVIDE',op('ADD',op('MULTIPLY',t,N),xx),N*N),yy,0)
a=texture(lut,lutUV(tile0),'EXTEND');b=texture(lut,lutUV(tile1),'EXTEND')
mix=nodes.new('ShaderNodeMixRGB');mix.blend_type='MIX';mix.use_clamp=False;links.new(frac,mix.inputs[0]);links.new(a,mix.inputs[1]);links.new(b,mix.inputs[2])
em=nodes.new('ShaderNodeEmission');em.inputs['Strength'].default_value=1;links.new(mix.outputs[0],em.inputs['Color'])
path=nodes.new('ShaderNodeLightPath');visible=op('MAXIMUM',path.outputs['Is Camera Ray'],path.outputs['Is Glossy Ray'])
factor=op('MULTIPLY',valid,visible);blend=nodes.new('ShaderNodeMixShader');links.new(factor,blend.inputs[0]);links.new(inp.outputs['Original Surface'],blend.inputs[1]);links.new(em.outputs[0],blend.inputs[2]);links.new(blend.outputs[0],out.inputs['Surface'])
g['fixed_reference_camera']=json.dumps(P);g['reference_illumination_baked']=True;g['surface_geometry_unchanged']=True
copies={}
def painted(mat):
    if mat.name in copies:return copies[mat.name]
    new=mat.copy();new.name=mat.name+' — fixed film pigments v28';new.use_nodes=True
    nd=new.node_tree.nodes;ln=new.node_tree.links;output=next(n for n in nd if n.type=='OUTPUT_MATERIAL' and n.is_active_output)
    original=output.inputs['Surface'].links[0].from_socket;node=nd.new('ShaderNodeGroup');node.node_tree=g
    ln.new(original,node.inputs['Original Surface']);ln.new(node.outputs['Surface'],output.inputs['Surface']);new['film_surface_revision']=28;new['original_material']=mat.name;copies[mat.name]=new;return new

camera=np.array([P['cameraX'],-P['distance'],P['cameraZ']]);records=[];materials={}
col=bpy.data.collections['Movie courtyard projection v24 — complete solid rooms']
for ob in col.all_objects:
    if ob.type!='MESH':continue
    index=int(ob['movie_bay']);mat=ob.data.materials[0];materials[mat.name]=materials.get(mat.name,0)+1
    allowed=any(mat.name.startswith('Movie bay material '+key+' v23') for key in q['nativeLeftMaterials']) or mat.name.startswith(('Movie pale plaster v22','Movie warm stone trim v22'))
    if not allowed:continue
    spec=bay_spec(index);radial=np.array([math.sin(spec['angle']),math.cos(spec['angle'])]);M=np.array(ob.matrix_world);normalMatrix=np.linalg.inv(M[:3,:3]).T
    chosen=[]
    for poly in ob.data.polygons:
        pos=M[:3,:3]@np.array(poly.center)+M[:3,3];normal=normalMatrix@np.array(poly.normal);normal/=max(np.linalg.norm(normal),1e-12)
        dist=spec['chordRadius']-np.dot(pos[:2]-center[:2],radial);eye=camera-pos;eye/=max(np.linalg.norm(eye),1e-12)
        if q['eligibleFrontDepth'][0]<=dist<=q['eligibleFrontDepth'][1] and q['eligibleHeight'][0]<=pos[2]<=q['eligibleHeight'][1] and np.dot(normal,eye)>=q['facingMinimum']:chosen.append(poly.index)
    if chosen:
        idx=len(ob.data.materials);ob.data.materials.append(painted(mat))
        for i in chosen:ob.data.polygons[i].material_index=idx
        ob['film_surface_revision']=28;records.append({'object':ob.name,'bay':index,'originalMaterial':mat.name,'paintedMaterialIndex':idx,'polygons':chosen})
assert records,'No eligible physical surfaces found'
for name,value in baseline['allDayMeshHashes'].items():assert fingerprint(bpy.data.objects[name])==value,name
for name,value in beforeTopology.items():assert topology(bpy.data.objects[name])==value,name
for name,row in baseline['characters'].items():assert fingerprint(bpy.data.objects[name],True)==row['worldHash'],name
s['movie_surface_revision']=28;s.render.use_border=False;s.render.resolution_x=720;s.render.resolution_y=468;s.render.resolution_percentage=100;s.cycles.samples=24;s.cycles.use_denoising=True
audit={'revision':28,'allDayMeshHashes':baseline['allDayMeshHashes'],'topologyHashes':beforeTopology,'characters':baseline['characters'],'camera':baseline['camera'],'lightingUnchangedFrom':27,'sourceSha256':q['sourceSha256'],'selectedObjects':records,'selectedPolygonCount':sum(len(r['polygons']) for r in records),'allFacadeMaterialNames':materials,'paintedMaterialCount':len(copies),'fixedWorldProjection':True,'newSurfaceGeometryCount':0,'oneToOneComplete':False}
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Suzume_scene_movie_surfaces_v28.blend'));(O/'integration-v28.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8');print('SURFACES_28_SAVED',len(records),audit['selectedPolygonCount'],list(copies),flush=True)
if '--trial' in sys.argv:
    s.render.resolution_x=540;s.render.resolution_y=351;s.cycles.samples=12;s.render.filepath=str(O/'trial-front-v28.png');bpy.ops.render.render(write_still=True)
elif '--render' in sys.argv:
    s.render.filepath=str(O/'movie-front-v28.png');bpy.ops.render.render(write_still=True)
