import bpy,math,random,json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).parent;OUT=ROOT/'reconstruction_v6';OUT.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'reconstruction_v5/Suzume_v5.blend'))
s=bpy.context.scene;cam=bpy.data.objects['Reference_camera_630x750'];s.camera=cam;s.render.resolution_x=630;s.render.resolution_y=750
houses=bpy.data.collections.new('V6 architectural relief and repairs');s.collection.children.link(houses)
left=bpy.data.materials['V5 aged blue grey lime plaster'];right=bpy.data.materials['V5 warm pale green plaster'];stone=bpy.data.materials['V5 worn cornice'];frame=bpy.data.materials['V5 faded painted frame'];dark=bpy.data.materials['V5 unlit room'];earth=bpy.data.materials['V5 bank stone']
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

# Repair projected bays with physical connecting party walls at depth changes.
bays=[(-8,41,464,521),(41,86,465,524),(86,143,470,525),(143,190,474,526),(190,244,473,525),(244,290,478,526),(346,380,483,524),(380,425,478,523),(425,472,476,522),(472,519,474,521),(519,563,475,520)]
for a,b in zip(bays,bays[1:]):
 if a[1]!=b[0]:continue
 x=a[1];da=ground((a[0]+a[1])/2,a[3]+1);db=ground((b[0]+b[1])/2,b[3]+1)
 ps=[unproject(x,y,d) for d,t,bt in [(da,a[2]-12,a[3]),(db,b[2]-12,b[3])] for y in [t,bt]]
 o=mesh('Connecting party wall',[tuple(p) for p in ps],[(0,1,3,2)],left if x<300 else right);mod=o.modifiers.new('Real wall thickness','SOLIDIFY');mod.thickness=.12
# Front elevation's two raised, shallow curved pediments are not generic flat roofs.
for x0,x1,edge,rise in [(88,190,465,15),(190,261,467,13)]:
 d=ground((x0+x1)/2,526)-.24;cx=(x0+x1)/2
 curve=[]
 for j in range(33):
  x=x0+(x1-x0)*j/32;y=edge-rise*math.sin(math.pi*j/32)**.7;curve.append((x,y))
 for (x,y),(xx,yy) in zip(curve,curve[1:]):
  pts=[unproject(u,v,d) for u,v in [(x,y),(xx,yy),(xx,edge+5),(x,edge+5)]]
  obj=mesh('Curved pediment solid fascia',[tuple(p) for p in pts],[(0,1,2,3)],left);mod=obj.modifiers.new('Pediment depth','SOLIDIFY');mod.thickness=.25
  rod('Curved cornice upper',unproject(x,y,d-.04),unproject(xx,yy,d-.04),.045,stone)
  rod('Curved cornice shadow line',unproject(x,y+2.8,d-.06),unproject(xx,yy+2.8,d-.06),.024,left)
 for j in range(12):
  x=x0+4+(x1-x0-8)*j/11;y=edge-rise*math.sin(math.pi*(x-x0)/(x1-x0))**.7
  box('Pediment vertical relief',(x,y+4,x+1,edge+2),d-.07,.045,stone)
 box('Pediment lower belt',(x0-1,edge+4,x1+1,edge+6),d-.09,.32,left)
# Stepped pilasters, plinths, weathered cornice courses, panels and window aprons.
for i,(x0,x1,top,bot) in enumerate(bays):
 d=ground((x0+x1)/2,bot+1);m=left if x0<300 else right
 for x in [x0+1.6,x1-2.2]:
  box('Pilaster shaft',(x-.9,top+1,x+.9,bot-5),d-.065,.18,m)
  box('Pilaster base',(x-1.7,bot-7,x+1.7,bot-3),d-.13,.23,stone if x0>300 else left)
  box('Pilaster capital',(x-1.8,top-2,x+1.8,top+1.5),d-.14,.26,m)
  box('Capital moulding',(x-2.2,top-3,x+2.2,top-2),d-.18,.3,stone)
 for y,w in [(top-10,1),(top-7,.6),(bot-6,.7)]:box('Layered horizontal moulding',(x0,y,x1,y+w),d-.085,.18,m)
 if i not in (3,6):
  box('Window recessed apron',(x0+6,bot-7,x1-6,bot-2),d-.04,.07,m)
  for j in range(3):
   x=x0+8+j*(x1-x0-16)/3
   box('Apron raised panel',(x,bot-6,x+(x1-x0-19)/3,bot-3),d-.09,.08,m)
# Flat green mass in V5 gets warmer plaster, with blue-shaded left wing retained.
def tint(mat,lo,hi):
 for n in mat.node_tree.nodes:
  if n.type=='VALTORGB':n.color_ramp.elements[0].color=(*lo,1);n.color_ramp.elements[-1].color=(*hi,1)
tint(left,(.045,.09,.10),(.19,.28,.28));tint(right,(.17,.23,.09),(.46,.49,.25))
# Broken plaster/chips are shallow physical patches, bounded to wall piers, never the openings.
random.seed(601)
for x0,x1,top,bot in bays:
 d=ground((x0+x1)/2,bot+1)
 for j in range(24):
  x=random.choice([x0+2,x1-2])+random.uniform(-.7,.7);y=random.uniform(top+2,bot-3);r=random.uniform(.2,.8)
  vs=[tuple(unproject(x+math.cos(k*math.pi/3)*r,y+math.sin(k*math.pi/3)*r*1.6,d-.16)) for k in range(6)]
  mesh('Plaster loss',vs,[tuple(range(6))],earth)
# Replace fine comb-like ripples with two irregular world-scale wave fields.
water=bpy.data.materials['Clear turquoise water'];nt=water.node_tree;n=nt.nodes;lk=nt.links
for node in n:
 if node.type=='VECT_MATH' and node.operation=='MULTIPLY':node.inputs[1].default_value=(1,2.2,1)
 if node.type=='TEX_NOISE':node.inputs['Scale'].default_value=.8;node.inputs['Detail'].default_value=2;noise=node
 if node.type=='BUMP':bump=node
bump.inputs['Strength'].default_value=.30;bump.inputs['Distance'].default_value=.035
# Make scene model inspection convenient on opening.
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':
   area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.shading.type='MATERIAL'
s.cycles.samples=32;s.render.resolution_x=1008;s.render.resolution_y=1200;s.render.filepath=str(OUT/'front_v6.png')
s['reconstruction_status']='V6 adds curved pediments, mouldings, pilasters, connecting walls and irregular ripples; still not a verified 1:1 replica.'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Suzume_v6.blend'));bpy.ops.render.render(write_still=True)
for o in bpy.context.selected_objects:o.select_set(False)
for o in s.objects:
 if o.type=='MESH' and not any(c.name=='V5_Volumetric_clouds' for c in o.users_collection):o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(OUT/'Suzume_v6.glb'),export_format='GLB',use_selection=True,export_extras=True)
print('V6_READY')
