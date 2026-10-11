import bpy, math, random, json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).parent;OUT=ROOT/'reconstruction_v5';OUT.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'reconstruction_v4/Suzume_v4_layout.blend'))
s=bpy.context.scene;cam=bpy.data.objects['Reference_camera_630x750'];s.camera=cam;s.render.resolution_x=630;s.render.resolution_y=750
random.seed(507)
def lin(rgb):return tuple(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in rgb)
def collection(name):
 c=bpy.data.collections.new(name);s.collection.children.link(c);return c
houses=collection('V5_Rebuilt_masonry');plants=collection('V5_Bank_vegetation');clouds=collection('V5_Volumetric_clouds');paving=collection('V5_Irregular_submerged_paving')
def mat(name,rgb,rough=.8):
 m=bpy.data.materials.new(name);m.diffuse_color=(*lin(rgb),1);m.use_nodes=True;p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Base Color'].default_value=m.diffuse_color;p.inputs['Roughness'].default_value=rough
 noise=m.node_tree.nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=9;noise.inputs['Detail'].default_value=4
 ramp=m.node_tree.nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(*(c*.58 for c in lin(rgb)),1);ramp.color_ramp.elements[1].color=(*lin(rgb),1)
 m.node_tree.links.new(noise.outputs['Fac'],ramp.inputs[0]);m.node_tree.links.new(ramp.outputs[0],p.inputs['Base Color']);return m
left=mat('V5 aged blue grey lime plaster',(.47,.57,.60));right=mat('V5 warm pale green plaster',(.74,.79,.59));stone=mat('V5 worn cornice',(.71,.75,.64));frame=mat('V5 faded painted frame',(.28,.43,.39));dark=mat('V5 unlit room',(.10,.18,.20));earth=mat('V5 bank stone',(.32,.42,.37))
for cname in ['04_Reference_facade','04_Ring_facade','V4_Reference_supported_layout','03_Shore']:
 c=bpy.data.collections.get(cname)
 if c:
  for o in list(c.objects):
   if cname=='V4_Reference_supported_layout' and o.name.startswith(('Raised arcade','Arcade grounded support','Distant')):continue
   bpy.data.objects.remove(o,do_unlink=True)
for o in list(bpy.data.collections['07_Vegetation'].objects):
 p=o.matrix_world.translation
 if abs(p.x)>1.0 or abs(p.y)>.6:bpy.data.objects.remove(o,do_unlink=True)
for o in list(bpy.data.collections['01_Basin'].objects):
 if o.name.startswith('Submerged flagstone'):bpy.data.objects.remove(o,do_unlink=True)
def unproject(x,y,depth):
 f=cam.data.view_frame(scene=s);xs=[v.x for v in f];ys=[v.y for v in f];d=cam.matrix_world.to_3x3()@Vector((min(xs)+(max(xs)-min(xs))*x/630,max(ys)-(max(ys)-min(ys))*y/750,f[0].z))
 return cam.location+d*((depth-cam.location.y)/d.y)
def ground(x,y,z=.04):
 a=unproject(x,y,0);b=unproject(x,y,1);return(z-a.z)/(b.z-a.z)
def mesh(name,verts,faces,material,coll=houses):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);o=bpy.data.objects.new(name,me);coll.objects.link(o);me.materials.append(material);return o
def box(name,rect,d,thick,m):
 a,b,c,e=rect;ps=[unproject(x,y,d) for x,y in [(a,b),(c,b),(c,e),(a,e)]]
 return mesh(name,[tuple(p) for p in ps]+[tuple(p+Vector((0,thick,0))) for p in ps],[(3,2,1,0),(4,5,6,7),(1,5,4,0),(2,6,5,1),(3,7,6,2),(0,4,7,3)],m)
def rod(name,a,b,r,m,coll=houses):
 diff=b-a;vs=[(r*math.cos(i*math.pi/6),r*math.sin(i*math.pi/6),z) for z in [-diff.length/2,diff.length/2] for i in range(12)];o=mesh(name,vs,[tuple(reversed(range(12))),tuple(range(12,24))]+[(i,(i+1)%12,(i+1)%12+12,i+12) for i in range(12)],m,coll);o.location=(a+b)/2;o.rotation_euler=diff.to_track_quat('Z','Y').to_euler();return o
def arch(cx,spring,rise,half,top,bottom,d,m,name):
 # A genuine arched hole in a solid wall: filled masonry above the curve, empty opening below.
 ps=[(cx+half*math.cos(i*math.pi/24),spring-rise*math.sin(i*math.pi/24)) for i in range(25)]
 for (x,y),(xx,yy) in zip(ps,ps[1:]):
  front=[unproject(u,v,d) for u,v in [(x,top),(xx,top),(xx,yy),(x,y)]]
  mesh(name+' solid spandrel',[tuple(p) for p in front]+[tuple(p+Vector((0,.4,0))) for p in front],[(3,2,1,0),(4,5,6,7),(1,5,4,0),(2,6,5,1),(0,4,7,3)],m)
  rod(name+' stone arch edge',unproject(x,y,d-.03),unproject(xx,yy,d-.03),.028,stone)
 for x in [cx-half,cx+half]:box(name+' jamb',(x-.65,spring,x+.65,bottom),d-.03,.4,stone)
 return ps
# Rebuild lower facade as substantial walls with individual recessed window openings.
bays=[(-8,41,464,521),(41,86,465,524),(86,143,470,525),(143,190,474,526),(190,244,473,525),(244,290,478,526),(346,380,483,524),(380,425,478,523),(425,472,476,522),(472,519,474,521),(519,563,475,520)]
for i,(x0,x1,top,bottom) in enumerate(bays):
 d=ground((x0+x1)/2,bottom+1);m=left if x0<300 else right
 box('Masonry window head',(x0,top-12,x1,top),d,.7,m);box('Masonry base',(x0,bottom-7,x1,bottom+1),d,.7,m)
 for x in [x0,x1-4]:box('Load bearing wall pier',(x,top-12,x+4,bottom),d,.8,m)
 box('Interior rear wall',(x0+3,top,x1-3,bottom-7),d+1.2,.18,dark)
 # Large frame is recessed instead of pasted across the front of the wall.
 for x in [x0+5,x1-5]:box('Recessed outer window frame',(x,top+2,x+.7,bottom-8),d+.07,.09,frame)
 if i not in [3,6]:
  for k in range(1,6):
   x=x0+5+(x1-x0-10)*k/6;box('Fine window mullion',(x,top+3,x+.55,bottom-8),d+.08,.07,frame)
  for y in [top+6,top+13,bottom-11]:box('Fine window transom',(x0+5,y,x1-5,y+.65),d+.08,.07,frame)
 else:
  cx=(x0+x1)/2;half=(x1-x0)*.32
  arch(cx,top+21,12,half,top,bottom-7,d,m,'Main arched entrance')
  for x in [cx-half+2,cx,cx+half-2]:box('Entrance door glazing',(x,top+22,x+.6,bottom-8),d+.09,.09,frame)
 # Wall setbacks have a roof, floor and returns to form real room volumes.
 for x in [x0,x1-1]:box('Room return',(x,top-11,x+1,bottom),d,1.3,m)
 box('Room roof slab',(x0-1,top-14,x1+1,top-11),d-.12,1.6,stone)
 for row in range(3):
  box('Shore step',(x0,bottom-1+row*.6,x1,bottom+.3+row*.6),d-.18-row*.12,.4,earth)
 # Small, uneven sill planting; use shared curved leaf geometry.
 leafmesh=bpy.data.meshes.get('Curved pointed leaf shared geometry')
 if leafmesh:
  for j in range(60):
   o=bpy.data.objects.new('Shore leaf',leafmesh);plants.objects.link(o);o.location=unproject(random.uniform(x0,x1),bottom+random.uniform(-2,1),d-.3);o.scale=(.05,.05,random.uniform(.05,.12));o.rotation_euler=(random.uniform(-1,1),random.uniform(-1,1),random.random()*6.28)
# Upper arcades are cut into actual masonry bands, and their height follows the reference.
for x0,x1,y in [(-8,85,443),(88,143,451),(146,191,455),(194,259,453),(350,425,459),(425,493,454),(493,563,451)]:
 d=ground((x0+x1)/2,524)+.12;m=left if x0<300 else right
 box('Upper arcade sill',(x0,y+9,x1,y+12),d,.65,m);box('Upper arcade coping',(x0-1,y-6,x1+1,y-3),d-.06,.85,stone)
 count=max(2,round((x1-x0)/12));w=(x1-x0)/count
 for j in range(count):
  cx=x0+w*(j+.5);arch(cx,y+2,4.8,w*.32,y-3,y+9,d,m,'Upper arcade')
  box('Upper arcade wall pier',(cx+w*.32,y-3,cx+w*.5,y+9),d,.5,m)
for x0,y0,x1,y1 in [(0,410,75,438),(96,407,145,441),(155,417,190,446),(207,422,258,449),(455,432,484,452)]:
 d=ground((x0+x1)/2,524)+1.3;m=left if x0<300 else right
 box('Setback story sill',(x0,y1-7,x1,y1),d,1.4,m);box('Setback story lintel',(x0,y0,x1,y0+7),d,1.4,m);box('Setback roof',(x0-2,y0-3,x1+2,y0),d-.2,1.8,stone)
 for x in range(int(x0),int(x1)-4,15):box('Setback wall pier',(x,y0+5,x+5,y1-6),d,.7,m)
 box('Setback dark interior',(x0,y0+6,x1,y1-6),d+1.1,.15,dark)
# Continuous outer raised arcade and distant low building remain separately identified.
# Reuse the V4 continuous outer-gallery path rather than detaching its segments.
# Large irregular submerged stone shapes replace the regular square grid.
floor_mats=[mat('V5 paving '+str(i),rgb) for i,rgb in enumerate([(.33,.50,.48),(.41,.57,.53),(.26,.43,.43),(.44,.58,.57),(.31,.46,.47)])]
grid={(i,j):(i*1.3+random.uniform(-.22,.22),j*1.3+random.uniform(-.22,.22),-.105+random.uniform(-.005,.005)) for i in range(-12,13) for j in range(-12,13)}
for i in range(-12,12):
 for j in range(-12,12):
  if (i*1.3)**2+(j*1.3)**2>225:continue
  ps=[Vector(grid[k]) for k in [(i,j),(i+1,j),(i+1,j+1),(i,j+1)]];center=sum(ps,Vector())/4;ps=[center+(p-center)*.982 for p in ps]
  mesh('Irregular submerged paving',[tuple(p) for p in ps],[(0,1,2,3)],random.choice(floor_mats),paving)
# Clear, lightly rippled water; noise in world units removes the comb-like stripes.
water=bpy.data.materials['Clear turquoise water'];n=water.node_tree.nodes;n.clear();lk=water.node_tree.links
out=n.new('ShaderNodeOutputMaterial');p=n.new('ShaderNodeBsdfPrincipled');p.inputs['Base Color'].default_value=(.84,.98,.97,1);p.inputs['Roughness'].default_value=.025;p.inputs['Transmission Weight'].default_value=1;p.inputs['IOR'].default_value=1.333
coord=n.new('ShaderNodeTexCoord');scale=n.new('ShaderNodeVectorMath');scale.operation='MULTIPLY';scale.inputs[1].default_value=(1,5,1);noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=2.5;noise.inputs['Detail'].default_value=3
lk.new(coord.outputs['Object'],scale.inputs[0]);lk.new(scale.outputs[0],noise.inputs[0]);bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.15;bump.inputs['Distance'].default_value=.003;lk.new(noise.outputs['Fac'],bump.inputs['Height']);lk.new(bump.outputs[0],p.inputs['Normal'])
clear=n.new('ShaderNodeBsdfTransparent');clear.inputs[0].default_value=(.75,.95,.92,1);mix=n.new('ShaderNodeMixShader');mix.inputs[0].default_value=.20;lk.new(p.outputs[0],mix.inputs[1]);lk.new(clear.outputs[0],mix.inputs[2]);lk.new(mix.outputs[0],out.inputs[0])
# Sky is a plain blue environment; actual volume meshes create cloud depth and reflections.
world=bpy.data.worlds.new('V5 clear blue atmosphere');world.use_nodes=True;s.world=world;bg=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs['Color'].default_value=(*lin((.008,.49,.77)),1);bg.inputs['Strength'].default_value=.8
wn=world.node_tree.nodes;wl=world.node_tree.links;ambient=wn.new('ShaderNodeBackground');ambient.inputs[0].default_value=(.6,.7,.8,1);ambient.inputs[1].default_value=.6;path=wn.new('ShaderNodeLightPath');mx=wn.new('ShaderNodeMath');mx.operation='MAXIMUM';wl.new(path.outputs['Is Camera Ray'],mx.inputs[0]);wl.new(path.outputs['Is Glossy Ray'],mx.inputs[1]);skyMix=wn.new('ShaderNodeMixShader');wl.new(mx.outputs[0],skyMix.inputs[0]);wl.new(ambient.outputs[0],skyMix.inputs[1]);wl.new(bg.outputs[0],skyMix.inputs[2]);wl.new(skyMix.outputs[0],next(n for n in wn if n.type=='OUTPUT_WORLD').inputs[0])
cloudmat=bpy.data.materials.new('V5 softly bounded cloud volume');cloudmat.use_nodes=True;n=cloudmat.node_tree.nodes;n.clear();lk=cloudmat.node_tree.links
out=n.new('ShaderNodeOutputMaterial');vol=n.new('ShaderNodeVolumePrincipled');vol.inputs['Color'].default_value=(.98,.99,1,1);vol.inputs['Anisotropy'].default_value=.15;vol.inputs['Emission Color'].default_value=(.86,.93,1,1);vol.inputs['Emission Strength'].default_value=.001
co=n.new('ShaderNodeTexCoord');dist=n.new('ShaderNodeVectorMath');dist.operation='DISTANCE';dist.inputs[1].default_value=(.5,.5,.5);lk.new(co.outputs['Generated'],dist.inputs[0]);fade=n.new('ShaderNodeMapRange');fade.inputs['From Min'].default_value=.42;fade.inputs['From Max'].default_value=.50;fade.inputs['To Min'].default_value=.6;fade.inputs['To Max'].default_value=0;fade.clamp=True;lk.new(dist.outputs['Value'],fade.inputs['Value'])
tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=5;tex.inputs['Detail'].default_value=4;lk.new(co.outputs['Generated'],tex.inputs[0]);density=n.new('ShaderNodeMath');density.operation='MULTIPLY';density.inputs[0].default_value=.30;lk.new(tex.outputs['Fac'],density.inputs[1]);lk.new(density.outputs[0],vol.inputs['Density']);lk.new(vol.outputs[0],out.inputs['Volume'])
for cx,cy,r,count in [(65,83,12,22),(549,236,12,28),(145,260,6,10),(278,375,3,7),(419,399,3,7)]:
 cluster=[]
 for j in range(count):
  x=cx+random.gauss(0,r*3);y=cy+random.gauss(0,r*(3 if cx>500 else 1.5));center=unproject(x,y,90+random.uniform(-9,9))
  bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,radius=1,location=center);o=bpy.context.object;o.name='Cumulus volume lobe';o.scale=(r*random.uniform(.45,.8),r*random.uniform(.4,.7),r*random.uniform(.4,.7))
  for c in list(o.users_collection):c.objects.unlink(o)
  clouds.objects.link(o);o.data.materials.append(cloudmat);cluster.append(o)
 # Union the lobes before shading: overlapping volume shells caused the plastic bubble look.
 bpy.ops.object.select_all(action='DESELECT')
 for o in cluster:o.select_set(True)
 bpy.context.view_layer.objects.active=cluster[0];bpy.ops.object.join();o=bpy.context.object;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 rem=o.modifiers.new('Continuous cloud union','REMESH');rem.mode='VOXEL';rem.voxel_size=max(.18,r*.045);bpy.ops.object.modifier_apply(modifier=rem.name)
 texgeo=bpy.data.textures.new('Cloud edge turbulence',type='CLOUDS');texgeo.noise_scale=max(.4,r*.15);dis=o.modifiers.new('Irregular cloud boundary','DISPLACE');dis.texture=texgeo;dis.strength=r*.12;dis.texture_coords='GLOBAL';bpy.ops.object.modifier_apply(modifier=dis.name)
s.cycles.samples=48;s.cycles.use_denoising=True;s.cycles.volume_bounces=3;s.view_settings.exposure=.3
s['reconstruction_status']='V5 rebuilt visible masonry, water, paving and volume clouds; not a verified full 1:1 scene.'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Suzume_v5.blend'))
s.render.filepath=str(OUT/'front_v5.png');bpy.ops.render.render(write_still=True)
# GLB is the garden geometry; volume clouds are a Blender environment and cannot be preserved in GLB.
for o in bpy.context.selected_objects:o.select_set(False)
for o in s.objects:
 if o.type=='MESH' and o.name not in clouds.objects:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(OUT/'Suzume_v5.glb'),export_format='GLB',use_selection=True,export_extras=True)
(OUT/'status.json').write_text(json.dumps({'rebuilt':['visible masonry','arched wall openings','irregular submerged paving','water shader','volumetric clouds'],'clouds_in_glb':False,'unverified':['depths','rear layout','full 1:1 accuracy'],'source':'official_front.jpg'},indent=2),encoding='utf-8')
print('V5_DONE')
