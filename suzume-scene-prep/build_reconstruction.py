import bpy, math, random, json
from mathutils import Vector
from pathlib import Path
random.seed(26)
OUT=Path(__file__).parent/'reconstruction'; OUT.mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
scene.unit_settings.system='METRIC'
scene['status']='Reference-based reconstruction study; not verified 1:1. Hunyuan downloads unavailable.'
scene['scale_assumption']='Door height 2.10 metres; courtyard radius 15 metres; both adjustable assumptions.'
def material(name,color,rough=.7,metal=0,noise=False):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
 n=m.node_tree.nodes;p=next(nod for nod in n if nod.type=='BSDF_PRINCIPLED');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
 if noise:
  tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=7;tex.inputs['Detail'].default_value=5
  ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.22;ramp.color_ramp.elements[0].color=tuple(c*.33 for c in color)+(1,);ramp.color_ramp.elements[1].position=.78;ramp.color_ramp.elements[1].color=(*color,1)
  m.node_tree.links.new(tex.outputs['Fac'],ramp.inputs[0]);m.node_tree.links.new(ramp.outputs[0],p.inputs['Base Color'])
  bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.22;bump.inputs['Distance'].default_value=.035;m.node_tree.links.new(tex.outputs['Fac'],bump.inputs['Height']);m.node_tree.links.new(bump.outputs[0],p.inputs['Normal'])
 return m
wall=material('Weathered warm concrete',(.48,.52,.43),noise=True)
trim=material('Pale stone trim',(.69,.72,.59),noise=True)
green=material('Oxidized green window frames',(.14,.32,.27),.65,.25,True)
rust=material('Broken steel rust',(.33,.24,.12),.65,.55,True)
paint=material('Door worn ivory paint',(.86,.87,.72),noise=True)
wood=material('Exposed wood',(.25,.15,.065),noise=True)
brick=material('Old brick',(.46,.24,.12),noise=True)
floor=material('Submerged stone',(.24,.34,.31),noise=True)
leaf=material('Vegetation',(.16,.29,.055),noise=True)
dark=material('Dark recess',(.035,.075,.067))
water=material('Clear turquoise water',(.045,.32,.38),.09,.2)
p=next(nod for nod in water.node_tree.nodes if nod.type=='BSDF_PRINCIPLED');p.inputs['Transmission Weight'].default_value=.65;p.inputs['IOR'].default_value=1.333
t=water.node_tree.nodes.new('ShaderNodeTexNoise');t.inputs['Scale'].default_value=12;t.inputs['Detail'].default_value=2
bump=water.node_tree.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.17;bump.inputs['Distance'].default_value=.025
water.node_tree.links.new(t.outputs['Fac'],bump.inputs['Height']);water.node_tree.links.new(bump.outputs[0],p.inputs['Normal'])
collections={}
def col(name):
 if name not in collections:
  c=bpy.data.collections.new(name);scene.collection.children.link(c);collections[name]=c
 return collections[name]
def move(obj,group):
 for c in list(obj.users_collection):c.objects.unlink(obj)
 col(group).objects.link(obj)
def cube(name,pos,size,mat,group,rz=0,bevel=0):
 verts=[(x*size[0]/2,y*size[1]/2,z*size[2]/2) for x,y,z in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]]
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],[(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)])
 o=bpy.data.objects.new(name,mesh);col(group).objects.link(o);o.location=pos;o.rotation_euler.z=rz;o.data.materials.append(mat)
 if bevel:
  m=o.modifiers.new('Soft worn edges','BEVEL');m.width=bevel;m.segments=2
 return o
def rod(name,a,b,r,mat,group):
 d=Vector(b)-Vector(a);v=[(r*math.cos(i*math.pi/4),r*math.sin(i*math.pi/4),z) for z in [-d.length/2,d.length/2] for i in range(8)]
 faces=[tuple(reversed(range(8))),tuple(range(8,16))]+[(i,(i+1)%8,(i+1)%8+8,i+8) for i in range(8)]
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(v,[],faces);o=bpy.data.objects.new(name,mesh);col(group).objects.link(o);o.location=(Vector(a)+Vector(b))/2;o.rotation_euler=d.to_track_quat('Z','Y').to_euler();o.data.materials.append(mat);return o
def polar(r,a,z):return(r*math.sin(a),r*math.cos(a),z)
def arc(name,r,a0,a1,z0,z1,mat,group,sections=12,radius=.035):
 pts=[polar(r,a0+(a1-a0)*i/sections,z0+(z1-z0)*i/sections) for i in range(sections+1)]
 for i in range(sections):rod(name,pts[i],pts[i+1],radius,mat,group)
def sphere(name,pos,scale,mat,group):
 mesh=bpy.data.meshes.new(name);mesh.from_pydata([(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)],[],[(0,2,4),(2,1,4),(1,3,4),(3,0,4),(2,0,5),(1,2,5),(3,1,5),(0,3,5)]);o=bpy.data.objects.new(name,mesh);col(group).objects.link(o);o.location=pos;o.scale=scale;o.data.materials.append(mat);return o
# Pool and submerged floor are separate editable objects.
bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=15.6,depth=.35,location=(0,0,-.34));o=bpy.context.object;o.name='Pool basin';o.data.materials.append(floor);move(o,'01_Basin')
for x in range(-15,16):
 for y in range(-15,16):
  if x*x+y*y<225:
   cube('Submerged flagstone',(x,y,-.135+random.uniform(-.012,.012)),(.98,.98,.08),floor,'01_Basin')
bpy.ops.mesh.primitive_cylinder_add(vertices=128,radius=15.45,depth=.04,location=(0,0,.0));o=bpy.context.object;o.name='Water surface - independent';o.data.materials.append(water);move(o,'02_Water')
for i in range(96):
 a=2*math.pi*i/96
 for j in range(3):cube('Circular shore steps',polar(15.5+j*.33,a,.07+j*.13),(.99,.34,.16),trim,'03_Shore',-a)
# Repeated open facade bays. Rear unseen layout is explicitly a design inference.
for i in range(32):
 a=2*math.pi*i/32;w=3.18;r=17.0
 def part(name,dx,z,sx,sz,mat,depth=.2):
  p=Vector(polar(r,a,z))+Vector((math.cos(a)*dx,-math.sin(a)*dx,0))
  return cube(name,p,(sx,depth,sz),mat,'04_Ring_facade',-a,.015)
 part('Bay plinth',0,.52,w,.38,wall,.6)
 part('Floor cornice',0,3.1,w,.22,trim,.6)
 part('Roof cornice',0,4.32,w,.23,trim,.6)
 part('Roof parapet',0,4.6,w,.38,wall,.35)
 for dx in [-w/2,w/2]:part('Concrete pier',dx,2.1,.22,3.7,wall,.4)
 # Deep dark interior is recessed, not a painted window plane.
 cube('Interior back wall',polar(19,a,2.2),(w,.15,3.4),dark,'04_Ring_facade',-a)
 for dx in [-1.3,-.65,0,.65,1.3]:part('Green mullion',dx,1.85,.045,2.45,green,.08)
 for z in [.72,1.4,2.8]:part('Window transom',0,z,2.75,.055,green,.08)
 # Upper arcade with actual open arch ribs.
 for cx in [-1.05,0,1.05]:
  for side in [-1,1]:part('Arcade jamb',cx+side*.42,3.53,.075,.65,trim,.15)
  for k in range(10):
   th0=math.pi*k/10;th1=math.pi*(k+1)/10
   def archpt(th):
    dx=cx+.42*math.cos(th);return Vector(polar(r,a,3.85+.32*math.sin(th)))+Vector((math.cos(a)*dx,-math.sin(a)*dx,0))
   rod('Open arcade arch',archpt(th0),archpt(th1),.048,trim,'04_Ring_facade')
 # Roof slabs are narrow rings, allowing a real open courtyard.
 cube('Roof slab',polar(18,a,4.38),(w,2.5,.15),wall,'04_Ring_facade',-a)
 for j in range(4):
  aa=a+random.uniform(-.08,.08);sphere('Roof moss',polar(16.95,aa,4.82),(random.uniform(.15,.5),.18,.1),leaf,'07_Vegetation')
# Tall broken perimeter supports, no intact domes or gazebo volumes.
for i in range(16):
 a=2*math.pi*i/16;rr=12.4;top=random.uniform(6.8,9.2)
 p0=polar(rr,a,.12);p1=polar(rr-.22,a,top*.6);p2=polar(rr-.85,a+.02,top)
 rod('Tall weathered column lower',p0,p1,.065,rust,'05_Broken_frame');rod('Tall weathered column upper',p1,p2,.055,rust,'05_Broken_frame')
 rod('Column flange',polar(rr+.1,a,.13),polar(rr-.65,a,top-.2),.024,trim,'05_Broken_frame')
 for z in [3.0,4.15,5.6,7.05]:
  if z<top and random.random()>.25:arc('Incomplete horizontal rib',rr-.2,a,a+math.pi/8*random.uniform(.45,1),z,z+random.uniform(-.12,.12),rust,'05_Broken_frame',4,.036)
 if i%3!=0:
  rod('Broken inward canopy spar',polar(rr-.4,a,top-.5),polar(rr-random.uniform(2,3.8),a,top+random.uniform(.4,1.3)),.045,rust,'05_Broken_frame')
 if i%2==0:rod('Diagonal knee brace',polar(rr,a,2.1),polar(rr-.15,a+.10,3.15),.03,rust,'05_Broken_frame')
# Central door and irregular brick footing. Origin follows threshold centre.
for i in range(24):
 x=random.uniform(-.75,.75);y=random.uniform(-.34,.35);z=random.choice([.075,.13,.2])
 cube('Loose brick footing',(x,y,z),(.24,.12,.11),brick,'06_Door',random.uniform(-.15,.15),.012)
base=.22
cube('Door timber core',(0,0,base+1.02),(.84,.065,2.04),wood,'06_Door',bevel=.01)
for x in [-.475,.475]:cube('White frame jamb',(x,0,base+1.06),(.075,.14,2.12),paint,'06_Door',bevel=.008)
cube('White frame head',(0,0,base+2.13),(1.02,.15,.095),paint,'06_Door',bevel=.01)
for x in [-.395,0,.395]:cube('Door stile',(x,-.041,base+1.02),(.065,.035,2.04),paint,'06_Door',bevel=.005)
for z in [.04,.79,1.65,2.0]:cube('Door cross rail',(0,-.045,base+z),(.84,.04,.075),paint,'06_Door',bevel=.006)
for x in [-.20,.20]:
 for low,hi in [(.095,.745),(.84,1.60),(1.70,1.95)]:
  z=base+(low+hi)/2;hh=hi-low
  cube('Recessed panel',(x,-.045,z),(.31,.015,hh),paint,'06_Door',bevel=.009)
  for xx in [x-.168,x+.168]:cube('Panel moulding',(xx,-.06,z),(.018,.025,hh+.02),trim,'06_Door',bevel=.004)
  for zz in [base+low,base+hi]:cube('Panel moulding',(x,-.06,zz),(.35,.025,.018),trim,'06_Door',bevel=.004)
for i in range(30):
 x=random.choice([-.37,.37])+random.uniform(-.025,.025);z=base+random.uniform(.04,1.95)
 cube('Paint loss',(x,-.067,z),(random.uniform(.008,.025),.004,random.uniform(.02,.1)),wood,'06_Door')
sphere('Door metal knob',(.345,-.13,base+1.04),(.028,.03,.028),rust,'06_Door')
# Small ivy, weeds and debris; all independently grouped.
for i in range(240):
 a=random.uniform(0,2*math.pi);r=random.uniform(15.25,16.2);p=polar(r,a,.34)
 for j in range(3):
  end=(p[0]+random.uniform(-.1,.1),p[1]+random.uniform(-.1,.1),p[2]+random.uniform(.1,.43));rod('Grass blade',p,end,.008,leaf,'07_Vegetation')
for i in range(45):
 z=base+i*.045;x=-.48+.04*math.sin(i*.8);sphere('Door ivy',(x,-.10,z),(.05,.018,.036),leaf,'07_Vegetation')
for i in range(70):
 a=random.uniform(0,2*math.pi);r=random.uniform(14,15.6);sphere('Shore rubble',polar(r,a,.11),(random.uniform(.04,.2),random.uniform(.05,.18),random.uniform(.04,.15)),wall,'08_Debris')
# Lighting and two saved camera views.
world=bpy.data.worlds.new('Blue daylight');scene.world=world;world.use_nodes=True;n=world.node_tree.nodes;n.clear()
out=n.new('ShaderNodeOutputWorld');bg=n.new('ShaderNodeBackground');coord=n.new('ShaderNodeTexCoord');cloud=n.new('ShaderNodeTexNoise');cloud.inputs['Scale'].default_value=3.8;cloud.inputs['Detail'].default_value=6;cloud.inputs['Roughness'].default_value=.65
cr=n.new('ShaderNodeValToRGB');cr.color_ramp.elements[0].position=.49;cr.color_ramp.elements[0].color=(.045,.27,.52,1);cr.color_ramp.elements[1].position=.67;cr.color_ramp.elements[1].color=(.83,.9,1,1)
world.node_tree.links.new(coord.outputs['Normal'],cloud.inputs['Vector']);world.node_tree.links.new(cloud.outputs['Fac'],cr.inputs[0]);world.node_tree.links.new(cr.outputs[0],bg.inputs[0]);bg.inputs['Strength'].default_value=.5;world.node_tree.links.new(bg.outputs[0],out.inputs[0])
bpy.ops.object.light_add(type='SUN',location=(0,-10,15));sun=bpy.context.object;sun.name='Afternoon sun';sun.data.energy=2.0;sun.data.angle=.12;sun.rotation_euler=(.45,-.4,-.5)
def camera(name,pos,target,lens):
 bpy.ops.object.camera_add(location=pos);o=bpy.context.object;o.name=name;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();o.data.lens=lens;o.data.clip_end=300;return o
front=camera('01_Film_front_study',(0,-10.5,1.5),(0,1,2.9),23)
overview=camera('02_Assembly_overview',(26,-30,24),(0,0,2),38)
scene.camera=front;scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.render.resolution_x=1200;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Suzume_reference_reconstruction.blend'))
bpy.ops.export_scene.gltf(filepath=str(OUT/'Suzume_reference_reconstruction.glb'),export_format='GLB',export_cameras=True,export_extras=True)
scene.render.filepath=str(OUT/'front_view.png');bpy.ops.render.render(write_still=True)
scene.camera=overview;scene.render.resolution_x=1400;scene.render.resolution_y=1000;scene.render.filepath=str(OUT/'assembly_view.png');bpy.ops.render.render(write_still=True)
stats={'objects':len(scene.objects),'collections':list(collections),'doorHeightAssumptionM':2.1,'poolRadiusAssumptionM':15.45,'downloadedHunyuanMeshes':0,'status':'Reference reconstruction study, not finished 1:1 or construction drawings','missing':['Verified rear geometry','Measured dimensions','Imported Hunyuan assets','Camera fitting against multiple film frames']}
(OUT/'model_status.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2),encoding='utf-8')
print('RECONSTRUCTION_COMPLETE',stats)


