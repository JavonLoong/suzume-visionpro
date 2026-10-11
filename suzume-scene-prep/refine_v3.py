import bpy, math, random, json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).parent
exec((ROOT/'refine_v2.py').read_text(encoding='utf-8-sig').split('# Lighting: sun from upper right')[0])
OUT=ROOT/'reconstruction_v3';OUT.mkdir(exist_ok=True)
random.seed(3109)
def linear(rgb):
 return tuple(c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4 for c in rgb)
def recolor(mat,rgb,spread=.55,metal=None):
 c=linear(tuple(v/255 for v in rgb));mat.diffuse_color=(*c,1)
 p=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Base Color'].default_value=(*c,1)
 if metal is not None:p.inputs['Metallic'].default_value=metal
 for n in mat.node_tree.nodes:
  if n.type=='VALTORGB':
   n.color_ramp.elements[0].color=(*(v*spread for v in c),1);n.color_ramp.elements[-1].color=(*c,1)
  if n.type=='BUMP':n.inputs['Distance'].default_value=.004;n.inputs['Strength'].default_value=.3
 return mat
recolor(left,(104,132,153),.45);recolor(right,(183,198,153),.5)
recolor(edge,(207,215,174),.68);recolor(wall,(119,142,128),.4)
recolor(trim,(223,229,198),.72);recolor(paint,(246,246,235),.86)
recolor(green,(63,115,101),.45,.2);recolor(rust,(136,97,55),.35,.35)
recolor(wood,(114,82,45),.5);recolor(brick,(159,95,64),.5)
recolor(floor,(76,125,115),.5);recolor(leaf,(83,135,55),.4)
recolor(dark,(26,51,57));recolor(glass,(42,85,89),metal=.1)
steelpaint=material('Flaked ochre paint on structural steel',linear((.72,.64,.43)),.65,.15,True)
for ob in col('05_Reference_frame').objects:
 if 'pale flange' in ob.name:ob.data.materials.clear();ob.data.materials.append(steelpaint)
# Build fine, curved leaves in place of octahedral vegetation placeholders.
for ob in list(col('07_Vegetation').objects):
 if any(s in ob.name for s in ['moss','ivy','Roof']):bpy.data.objects.remove(ob,do_unlink=True)
leafmats=[material('Leaf '+str(i),linear(tuple(c/255 for c in rgb)),.86) for i,rgb in enumerate([(48,106,58),(71,128,57),(104,151,65),(148,178,81),(51,108,85)])]
leafmesh=bpy.data.meshes.new('Curved pointed leaf shared geometry')
leafmesh.from_pydata([(0,0,0),(-.45,0,.32),(-.28,.11,.68),(0,.17,1),(.28,.11,.68),(.45,0,.32),(0,.1,.45)],[],[(0,1,6),(1,2,6),(2,3,6),(3,4,6),(4,5,6),(5,0,6)])
for m in leafmats:leafmesh.materials.append(m)
def realleaf(pos,size=.1):
 ob=bpy.data.objects.new('Individual curved ivy leaf',leafmesh);col('07_Vegetation').objects.link(ob);ob.location=pos;ob.scale=(size,size,size);ob.rotation_euler=(random.uniform(-1.4,1.4),random.uniform(-.6,.6),random.uniform(-math.pi,math.pi));ob.material_slots[0].link='OBJECT';ob.material_slots[0].material=random.choice(leafmats);return ob
for j in range(2):
 pts=[Vector((-.50+.08*math.sin(i*.6+j),-.095-j*.012,.26+i*.042)) for i in range(48)]
 for a,b in zip(pts,pts[1:]):rod('Twining ivy stem',a,b,.004,leaf,'07_Vegetation')
 for p in pts:
  for k in range(1):realleaf(p+Vector((random.uniform(-.06,.06),-.02,0)),random.uniform(.04,.075))
# Vegetation follows the reference's uneven sill lines, not a continuous hedge.
for x0,x1,yy in [(-10,287,522),(350,640,521),(365,548,449)]:
 dep=grounded_depth((x0+x1)/2,522)
 for cluster in range(int((x1-x0)/7)):
  xx=random.uniform(x0,x1);height=random.uniform(1,6)
  for j in range(20):
   q=unproject(xx+random.gauss(0,2),yy+random.uniform(-height,2),dep+random.uniform(-.15,.15));realleaf(q,random.uniform(.045,.15))
# Fine masonry cracks and detached paint are actual geometry, so export retains detail.
crackmat=material('Recessed masonry joints',linear((.13,.22,.22)),.96)
peels=[material('Plaster peel '+str(i),linear(tuple(v/255 for v in rgb)),.94) for i,rgb in enumerate([(136,160,152),(176,188,162),(202,209,179),(73,106,101),(153,175,129)])]
for bi,(x0,x1,top,bottom,dep,mat) in enumerate(bays):
 dep=grounded_depth((x0+x1)/2,bottom+2)
 for x in [x0+1,x1-2]:
  for yy in range(top+5,bottom-6,7):screenbox('Pier masonry mortar joint',(x-1,yy,x+2,yy+.3),dep-.012,.008,crackmat)
 for k in range(45):
  xx=random.choice([x0+random.uniform(0,3),x1-random.uniform(1,4)]);yy=random.uniform(top-4,bottom-7)
  screenbox('Small irregular plaster scar',(xx,yy,xx+random.uniform(.18,1.2),yy+random.uniform(.3,2.5)),dep-.018,.004,random.choice(peels))
 # Projecting dentils under cornices and stone joints break up flat strips.
 for xx in range(int(x0+2),int(x1-2),3):screenbox('Cornice dentil',(xx,top-4,xx+1.3,top-2.5),dep-.14,.22,edge)
 for xx in range(int(x0+5),int(x1-2),9):screenbox('Plinth joint',(xx,bottom-7,xx+.3,bottom),dep-.015,.01,crackmat)
 # Deteriorated frame remnants and shard outlines inside selected panes.
 for k in range(3):
  xx=x0+(x1-x0)*(k+1)/4;yy=top+random.uniform(10,25)
  screenrod('Broken glazing perimeter',[(xx-2,yy),(xx,yy+3),(xx+1,yy-2)],dep-.07,.007,steelpaint,'04_Reference_facade')
# Bolted plates at the main steel joints, paint loss and protruding broken flanges.
for name,pts,dep,r in traces:
 for xx,yy in pts[1:-1]:
  p=unproject(xx,yy,dep)
  cube('Riveted steel joint plate',p,(r*3,.035,.20),rust,'05_Reference_frame')
  for sx in [-1,1]:
   for sz in [-1,1]:rod('Steel rivet head',p+Vector((sx*r,-.024,sz*.058)),p+Vector((sx*r,-.038,sz*.058)),.012,steelpaint,'05_Reference_frame')
 for k in range(20):
  seg=random.choice(list(zip(pts,pts[1:])));t=random.random();xx=seg[0][0]*(1-t)+seg[1][0]*t;yy=seg[0][1]*(1-t)+seg[1][1]*t
  q=unproject(xx,yy,dep);cube('Steel paint flake',q+Vector((0,-r*.9,0)),(r*.6,.006,random.uniform(.02,.08)),steelpaint,'05_Reference_frame')
# Door grain and scattered fine paint chips; no uniform noise relief.
cube('Door top fitting rail',(0,-.015,2.28),(.84,.065,.075),paint,'06_Door',bevel=.004)
for ob in list(col('06_Door').objects):
 if ob.name.startswith('Door metal knob'):bpy.data.objects.remove(ob,do_unlink=True)
bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,radius=.027,location=(.345,-.13,base+1.04));knob=bpy.context.object;knob.name='Round aged brass door knob';knob.data.materials.append(rust);move(knob,'06_Door')
for poly in knob.data.polygons:poly.use_smooth=True
for i in range(145):
 x=random.uniform(-.41,.41);z=random.uniform(.28,2.23)
 if abs(x)<.03 or abs(x)>.36 or any(abs(z-(base+t))<.035 for t in [.04,.79,1.65,2]):
  cube('Fine exposed grain',(x,-.069,z),(random.uniform(.001,.005),.002,random.uniform(.009,.042)),wood,'06_Door')
for i in range(16):
 x=random.uniform(-.9,.7);y=random.uniform(-.5,.1)
 cube('Broken brick fragment',(x,y,.055),(.09,.06,.05),brick,'06_Door',random.random()*3,.008)
# Reference palette: saturated cyan sky, shaded blue-green left facade and warm right facade.
world=bpy.data.worlds.new('V3 saturated daylight');scene.world=world;world.use_nodes=True;n=world.node_tree.nodes;n.clear();lk=world.node_tree.links
out=n.new('ShaderNodeOutputWorld');bg=n.new('ShaderNodeBackground');coord=n.new('ShaderNodeTexCoord');tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=12;tex.inputs['Detail'].default_value=7;tex.inputs['Roughness'].default_value=.65
ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.49;ramp.color_ramp.elements[0].color=(*linear((.005,.48,.76)),1);ramp.color_ramp.elements[1].position=.64;ramp.color_ramp.elements[1].color=(*linear((.98,.995,1)),1)
mid=ramp.color_ramp.elements.new(.56);mid.color=(*linear((.57,.77,.89)),1)
lk.new(coord.outputs['Normal'],tex.inputs['Vector'])
# Directional cloud masses are placed around the clear central sky from the reference.
# This is a procedural world, never a photograph projected onto scene meshes.
cloudsum=None
for px,py,radius in [(45,75,.30),(540,245,.25),(90,290,.12),(255,390,.065),(385,410,.07)]:
 ray=-(unproject(px,py,1000)-cam.location).normalized()
 dot=n.new('ShaderNodeVectorMath');dot.operation='DOT_PRODUCT';dot.inputs[1].default_value=ray;lk.new(coord.outputs['Normal'],dot.inputs[0])
 remap=n.new('ShaderNodeMapRange');remap.inputs['From Min'].default_value=1-radius*radius*.5;remap.inputs['From Max'].default_value=1;remap.inputs['To Min'].default_value=0;remap.inputs['To Max'].default_value=1;remap.clamp=True;lk.new(dot.outputs['Value'],remap.inputs['Value'])
 if cloudsum is None:cloudsum=remap.outputs['Result']
 else:
  mx=n.new('ShaderNodeMath');mx.operation='MAXIMUM';lk.new(cloudsum,mx.inputs[0]);lk.new(remap.outputs['Result'],mx.inputs[1]);cloudsum=mx.outputs[0]
rough=n.new('ShaderNodeMath');rough.operation='MULTIPLY';rough.inputs[1].default_value=.8;lk.new(tex.outputs['Fac'],rough.inputs[0])
mass=n.new('ShaderNodeMath');mass.operation='MULTIPLY';mass.inputs[1].default_value=.35;lk.new(cloudsum,mass.inputs[0])
add=n.new('ShaderNodeMath');add.operation='ADD';lk.new(mass.outputs[0],add.inputs[0]);lk.new(rough.outputs[0],add.inputs[1])
els=list(ramp.color_ramp.elements);els[0].position=.58;els[1].position=.70;els[2].position=.84;els[2].color=(*linear((.80,.88,.96)),1)
lk.new(add.outputs[0],ramp.inputs[0]);lk.new(ramp.outputs[0],bg.inputs[0]);bg.inputs['Strength'].default_value=.8;lk.new(bg.outputs[0],out.inputs[0])
bpy.ops.object.light_add(type='SUN',location=(8,-5,12));sun=bpy.context.object;sun.data.energy=2.2;sun.data.color=(1,.98,.88);sun.data.angle=.06;sun.rotation_euler=(.6,-.65,-.4)
bpy.ops.object.light_add(type='AREA',location=(3,-8,9));fill=bpy.context.object;fill.data.energy=300;fill.data.size=9;fill.rotation_euler=(Vector((0,0,1))-fill.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.light_add(type='AREA',location=(7,-1,8));rim=bpy.context.object;rim.name='Warm daylight on right arcade';rim.data.energy=2400;rim.data.color=(1,.97,.80);rim.data.size=7;rim.rotation_euler=(Vector((7,6,1.1))-rim.location).to_track_quat('-Z','Y').to_euler()
wp=next(n for n in water.node_tree.nodes if n.type=='BSDF_PRINCIPLED');wp.inputs['Base Color'].default_value=(*linear((.16,.67,.67)),1);wp.inputs['Transmission Weight'].default_value=.85;wp.inputs['Roughness'].default_value=.035
wave.inputs['Scale'].default_value=110;wave.inputs['Distortion'].default_value=4;wavebump.inputs['Distance'].default_value=.004;wavebump.inputs['Strength'].default_value=.2
scene.render.engine='CYCLES';scene.cycles.samples=64;scene.cycles.use_denoising=True;scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=.65
scene.camera=cam;scene.render.resolution_x=1008;scene.render.resolution_y=1200
scene['reconstruction_status']='V3: improved palette and modeled detail; layout/depth still unverified, not completed 1:1.'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Suzume_v3.blend'))
bpy.ops.export_scene.gltf(filepath=str(OUT/'Suzume_v3.glb'),export_format='GLB',export_cameras=True,export_extras=True)
scene.render.filepath=str(OUT/'front_v3.png');bpy.ops.render.render(write_still=True)
print('V3_DONE',len(scene.objects))
