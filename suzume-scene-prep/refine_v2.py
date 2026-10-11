import bpy, math, json, random
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
ROOT=Path(__file__).parent
# Reuse deterministic construction helpers, keep previous delivery untouched.
exec((ROOT/'build_reconstruction.py').read_text(encoding='utf-8-sig').split('# Lighting and two saved camera views.')[0])
OUT=ROOT/'reconstruction_v2';OUT.mkdir(exist_ok=True)
scene=bpy.context.scene;scene.render.resolution_x=840;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
bpy.ops.object.camera_add();cam=bpy.context.object;cam.name='Reference_camera_630x750';cam.data.lens=28;cam.data.sensor_fit='VERTICAL';cam.data.sensor_height=32;scene.camera=cam
targets=[(293,552),(345,552),(293,442),(345,442)]
corners=[(-.51,-.08,.22),(.51,-.08,.22),(-.51,-.08,2.3975),(.51,-.08,2.3975)]
def setcam(par):
 d,z,aim,shift=par;cam.location=(0,-d,z);cam.rotation_euler=(Vector((0,0,aim))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.shift_x=shift;bpy.context.view_layer.update()
def projected(p):
 q=world_to_camera_view(scene,cam,Vector(p));return(q.x*630,(1-q.y)*750)
def loss(par):
 setcam(par);return sum((a-c)**2+(b-d)**2 for (a,b),(c,d) in zip(map(projected,corners),targets))
par=[13,2.4,3.9,0];steps=[2,0,.5,.01];best=loss(par)
for it in range(100):
 changed=False
 for j in range(4):
  for sign in [-1,1]:
   cand=par.copy();cand[j]+=steps[j]*sign
   if cand[0]<3 or not .8<=cand[1]<=2.4:continue
   score=loss(cand)
   if score<best:best=score;par=cand;changed=True
 if not changed:steps=[s*.65 for s in steps]
setcam(par)
# Inverse projection to explicit assumed depth planes, never stored as measured depths.
def unproject(px,py,y):
 # Camera view frame interpolates exact Blender projection incl. shift.
 frame=cam.data.view_frame(scene=scene)
 xs=[v.x for v in frame];ys=[v.y for v in frame];z=frame[0].z
 local=Vector((min(xs)+(max(xs)-min(xs))*px/630,max(ys)-(max(ys)-min(ys))*py/750,z))
 direction=cam.matrix_world.to_3x3()@local
 return cam.location+direction*((y-cam.location.y)/direction.y)
def grounded_depth(px,py,z=.08):
 p0=unproject(px,py,0);p1=unproject(px,py,1)
 return (z-p0.z)/(p1.z-p0.z)
def screenrod(name,pts,depth,r,mat=rust,group='05_Reference_frame'):
 def beam_depth(x,y):
  if group!='05_Reference_frame' or name.startswith(('L_','R_')) or 'traces' not in globals():return depth
  distances=[]
  for _,trace,d,_ in traces:
   # Projected x of supporting column at this beam's height.
   segments=list(zip(trace,trace[1:]));seg=min(segments,key=lambda seg:min(abs(y-seg[0][1]),abs(y-seg[1][1])))
   (xa,ya),(xb,yb)=seg;t=(y-ya)/(yb-ya) if yb!=ya else 0;xx=xa+(xb-xa)*t
   distances.append((abs(x-xx),d))
  near=sorted(distances)[:2]
  if near[0][0]<1:return near[0][1]
  weights=[1/max(a,1)**2 for a,_ in near];return sum(w*d for w,(_,d) in zip(weights,near))/sum(weights)
 ps=[unproject(x,y,beam_depth(x,y)) for x,y in pts]
 for a,b in zip(ps,ps[1:]):
  if name.startswith(('L_','R_')) and 'flange' not in name:
   w=r*1.45;h=r*.85;t=r*.22;d=b-a
   profile=[(-w,-h),(w,-h),(w,-h+t),(t,-h+t),(t,h-t),(w,h-t),(w,h),(-w,h),(-w,h-t),(-t,h-t),(-t,-h+t),(-w,-h+t)]
   verts=[(x,y,z) for z in [-d.length/2,d.length/2] for x,y in profile];nn=len(profile)
   faces=[tuple(reversed(range(nn))),tuple(range(nn,2*nn))]+[(j,(j+1)%nn,(j+1)%nn+nn,j+nn) for j in range(nn)]
   mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);o=bpy.data.objects.new(name,mesh);col(group).objects.link(o);o.location=(a+b)/2;o.rotation_euler=d.to_track_quat('Z','Y').to_euler();o.data.materials.append(mat)
  else:rod(name,a,b,r,mat,group)
def screenbox(name,box,depth,thickness,mat,group='04_Reference_facade'):
 x0,y0,x1,y1=box;pts=[unproject(x,y,depth) for x,y in [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]]
 # Front facade planar mesh, backed with real thickness.
 verts=[tuple(p) for p in pts]+[tuple(p+Vector((0,thickness,0))) for p in pts]
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],[(3,2,1,0),(4,5,6,7),(1,5,4,0),(2,6,5,1),(3,7,6,2),(0,4,7,3)])
 ob=bpy.data.objects.new(name,mesh);col(group).objects.link(ob);ob.data.materials.append(mat);ob['depth_status']='assumed; front silhouette traced from reference';return ob
# Remove uniform front-facing facades and all speculative foreground steel.
for o in list(col('04_Ring_facade').objects):
 if o.location.y>-1:bpy.data.objects.remove(o,do_unlink=True)
for o in list(col('05_Broken_frame').objects):bpy.data.objects.remove(o,do_unlink=True)
for o in list(col('03_Shore').objects):
 if o.location.y>-2:bpy.data.objects.remove(o,do_unlink=True)
# Clear old roof vegetation on visible half; replace with reference-aligned detail.
for o in list(col('07_Vegetation').objects):
 if o.name.startswith('Roof moss') and o.location.y>-1:bpy.data.objects.remove(o,do_unlink=True)
left=material('Cool weathered left facade',(.30,.39,.36),noise=True)
right=material('Sunlit ochre green facade',(.61,.60,.34),noise=True)
edge=material('Reference cornice stone',(.50,.56,.45),noise=True)
glass=material('Remaining old glass',(.12,.24,.25),.18,.15)
# Asymmetric real openings, varying heights, roof setbacks.
bays=[(-8,46,451,521,14,left),(47,99,451,520,15,left),(100,149,453,520,16,left),(150,194,466,521,17,left),(195,243,455,520,17,left),(244,290,466,523,18,left),(345,387,480,520,18,right),(387,431,469,520,17,right),(432,482,466,520,16,right),(483,533,467,519,15,right),(534,584,474,519,14,right),(585,639,482,517,13,right)]
for bi,(x0,x1,top,bottom,dep,mat) in enumerate(bays):
 dep=grounded_depth((x0+x1)/2,bottom+2)
 width=x1-x0
 # Repeated small open arcade above ground-floor windows, visible in both film references.
 screenbox('Arcade lower sill',(x0,top-2,x1,top),dep,.6,mat)
 for ai in range(4):
  cx=x0+width*(ai+.5)/4;ar=width/8-1.3;spring=top-7
  pts=[(cx+ar*math.cos(t*math.pi/16),spring-4.4*math.sin(t*math.pi/16)) for t in range(17)]
  screenrod('Upper arcade arch',pts,dep-.12,.032,edge,'04_Reference_facade')
  for xx in [cx-ar,cx+ar]:screenbox('Upper arcade jamb',(xx-.5,spring,xx+.5,top-2),dep-.12,.25,edge)
 screenbox('Stone plinth',(x0,bottom-7,x1,bottom+2),dep,.65,mat)
 screenbox('Deep recessed interior',(x0+4,top,x1-4,bottom-7),dep+1.1,.2,dark)
 for x in [x0,x1-4]:screenbox('Heavy facade pier',(x,top-16,x+4,bottom),dep,.7,mat)
 for z in [top-13,top-5]:screenbox('Cornice band',(x0-1,z,x1+1,z+2),dep-.08,.9,edge)
 # Ground floor slender multi-pane windows, some panes retained.
 for j in range(1,6):
  x=x0+width*j/6;screenbox('Window vertical',(x,top+4,x+.85,bottom-8),dep-.035,.09,green)
 for yy in [top+7,top+18,bottom-11]:screenbox('Window horizontal',(x0+4,yy,x1-4,yy+.9),dep-.035,.09,green)
 if bi%3==0:screenbox('Glass fragment',(x0+6,top+9,x0+width*.27,bottom-12),dep+.08,.025,glass)
 # Decorative arch surrounding central bay opening.
 if bi in [0,3,6,8]:
  cx=(x0+x1)/2;rad=width*.33;spring=top+20
  pts=[(cx+rad*math.cos(t*math.pi/20),spring-rad*.75*math.sin(t*math.pi/20)) for t in range(21)]
  screenrod('Masonry entrance arch',pts,dep-.16,.09,edge,'04_Reference_facade')
  for xx in [cx-rad,cx+rad]:screenbox('Masonry arch jamb',(xx-1,spring,xx+1,bottom-7),dep-.16,.45,edge)
 # Trim blocks and peeling stains, kept as geometry for GLB.
 for k in range(14):
  xx=random.uniform(x0+1,x1-2);yy=random.uniform(top-12,top-2)
  screenbox('Facade weathering chip',(xx,yy,xx+random.uniform(.4,2),yy+random.uniform(.4,1.4)),dep-.025,.01,wall)
# Setback upper volumes produce the uneven roofline of the original.
for box,dep,mat in [((-8,414,76,447),15,left),((88,415,142,447),18,left),((146,420,190,449),19,left),((198,425,255,452),19,left),((365,449,448,465),18,right),((451,433,483,460),20,right),((489,449,547,467),16,right),((548,455,625,474),15,right)]:
 dep=grounded_depth((box[0]+box[2])/2,522)+1.0
 x0,y0,x1,y1=box
 for strip in [(x0,y0,x1,y0+3),(x0,y1-4,x1,y1),(x0,y0,x0+3,y1),(x1-3,y0,x1,y1)]:screenbox('Upper story masonry',strip,dep,.6,mat)
 for xx in range(int(x0+7),int(x1-3),9):screenbox('Upper window posts',(xx,y0+3,xx+1,y1-4),dep,.1,green)
 screenbox('Setback roof cap',(x0-2,y0-3,x1+2,y0),dep-.2,1.3,edge)
# Front parapet, railings and roof pipes.
for x0,x1,yy,dep in [(-8,90,444,14),(99,145,449,16),(194,263,453,17),(364,430,467,17),(431,550,461,16),(551,631,470,14)]:
 dep=grounded_depth((x0+x1)/2,522)
 screenrod('Roof railing',[(x0,yy-10),(x1,yy-10)],dep,.027,green,'04_Reference_facade')
 for xx in range(int(x0),int(x1),7):screenrod('Roof railing vertical',[(xx,yy),(xx,yy-10)],dep,.025,green,'04_Reference_facade')
# Eight surveyed-in-image column traces; depths remain assumptions.
traces=[('L_near',[(-12,536),(8,363),(29,279),(52,243)],-3,.09),('L_main',[(82,525),(87,426),(96,347),(112,310)],4,.085),('L_mid',[(190,525),(194,432),(203,353)],11,.07),('L_far',[(261,522),(255,433),(255,389)],16,.06),('R_far',[(429,522),(416,405),(404,311)],13,.075),('R_mid',[(512,520),(491,389),(460,239)],6,.085),('R_near',[(625,517),(577,337),(556,226),(533,171)],-1,.095),('R_edge',[(666,306),(625,190),(583,112),(548,73)],-4,.09)]
traces=[(name,pts,grounded_depth(*pts[0],z=.025) if pts[0][1]>500 else dep,r) for name,pts,dep,r in traces]
for name,pts,dep,r in traces:
 if pts[0][1]>500:dep=grounded_depth(*pts[0],z=.025)
 screenrod(name,pts,dep,r)
 screenrod(name+' pale flange',[(x+2,y) for x,y in pts],dep-.025,r*.33,edge)
for name,pts,dep in [('L low',[(-12,406),(91,421),(199,438),(258,438)],8),('L middle',[(-8,356),(96,377),(196,390),(254,391)],8),('L upper',[(-8,314),(99,341),(171,352)],5),('L broken',[(-5,265),(75,296)],-2),('L top',[(-3,126),(45,91)],-4),('R low',[(374,464),(428,451),(511,437),(637,410)],9),('R middle',[(405,363),(478,349),(551,342)],8),('R upper',[(407,326),(487,305),(527,298),(560,301)],6),('R cross',[(523,385),(575,371),(638,348)],-1),('R high',[(563,257),(607,245),(646,229)],-2)]:screenrod(name,pts,dep,.045)
for pts,dep in [([(85,487),(105,466),(132,458)],5), ([(195,483),(223,459),(253,451)],11), ([(414,404),(381,367),(367,382)],13)]:screenrod('Knee and broken brace',pts,dep,.034)
# The cropped upper-left spar needs an off-frame support. Mark the addition as inferred.
floating=list(o for o in col('05_Reference_frame').objects if o.name.startswith('L top'))
if floating:
 ob=floating[0];end=ob.matrix_world @ ob.data.vertices[0].co
 # Locate exact rod centre-line endpoint without depending on vertex radius.
 bpy.context.view_layer.update();end=ob.location+ob.rotation_euler.to_matrix()@Vector((0,0,-max(v.co.z for v in ob.data.vertices)))
 foot=Vector((end.x-1.0,end.y,.025));support=rod('Inferred off-frame support',foot,end,.065,rust,'05_Reference_frame');support['evidence']='inferred support outside reference crop'
# Give the edge column a grounded continuation beyond the camera crop.
edgefoot=unproject(666,306,-4);rod('Inferred edge column foot',(edgefoot.x,edgefoot.y,.025),edgefoot,.095,rust,'05_Reference_frame')['evidence']='inferred outside reference crop'
# Add mapped climbing greenery without obscuring key structure.
for x0,x1,yy,dep in [(-8,145,522,14),(195,289,524,17),(361,632,519,15),(364,545,449,17)]:
 dep=grounded_depth((x0+x1)/2,yy if yy>500 else 522)
 for i in range(int((x1-x0)/2)):
  p=unproject(random.uniform(x0,x1),yy+random.uniform(-3,2),dep);sphere('Irregular reference moss',p,(random.uniform(.06,.22),.08,random.uniform(.035,.09)),leaf,'07_Vegetation')
# Clearer film-like water; retain submerged geometry.
wp=next(n for n in water.node_tree.nodes if n.type=='BSDF_PRINCIPLED');wp.inputs['Roughness'].default_value=.025;wp.inputs['Metallic'].default_value=.05;wp.inputs['Transmission Weight'].default_value=.9
for nod in water.node_tree.nodes:
 if nod.type=='BUMP':nod.inputs['Strength'].default_value=.11;nod.inputs['Distance'].default_value=.012
wave=water.node_tree.nodes.new('ShaderNodeTexWave');wave.wave_type='BANDS';wave.bands_direction='Y';wave.inputs['Scale'].default_value=4;wave.inputs['Distortion'].default_value=3;wave.inputs['Detail'].default_value=3
wavebump=water.node_tree.nodes.new('ShaderNodeBump');wavebump.inputs['Strength'].default_value=.19;wavebump.inputs['Distance'].default_value=.025;water.node_tree.links.new(wave.outputs['Color'],wavebump.inputs['Height']);water.node_tree.links.new(wavebump.outputs['Normal'],wp.inputs['Normal']);wp.inputs['Roughness'].default_value=.045
# Lighting: sun from upper right, coloured ambient fill.
world=bpy.data.worlds.new('Reference blue sky');scene.world=world;world.use_nodes=True;n=world.node_tree.nodes;n.clear();links=world.node_tree.links
out=n.new('ShaderNodeOutputWorld');bg=n.new('ShaderNodeBackground');co=n.new('ShaderNodeTexCoord');noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=4.5;noise.inputs['Detail'].default_value=6
ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.52;ramp.color_ramp.elements[0].color=(.025,.28,.58,1);ramp.color_ramp.elements[1].position=.64;ramp.color_ramp.elements[1].color=(.85,.95,1,1)
links.new(co.outputs['Normal'],noise.inputs['Vector']);links.new(noise.outputs['Fac'],ramp.inputs[0]);links.new(ramp.outputs[0],bg.inputs[0]);bg.inputs['Strength'].default_value=.6;links.new(bg.outputs[0],out.inputs[0])
bpy.ops.object.light_add(type='SUN',location=(10,-5,15));sun=bpy.context.object;sun.name='Right hand afternoon sun';sun.data.energy=3;sun.data.angle=.06;sun.rotation_euler=(.6,-.65,-.4)
bpy.ops.object.light_add(type='AREA',location=(3,-8,9));fill=bpy.context.object;fill.data.energy=1100;fill.data.shape='DISK';fill.data.size=12;fill.rotation_euler=(Vector((0,0,1))-fill.location).to_track_quat('-Z','Y').to_euler()
scene.render.engine='CYCLES';scene.cycles.samples=40;scene.cycles.use_denoising=True;scene.view_settings.view_transform='AgX';scene.view_settings.exposure=.7
scene['reconstruction_status']='V2 image-calibrated front view. Hidden geometry, depths and true scale remain unverified.'
report={'reference':'official_front.jpg','reference_size':[630,750],'door_target_pixels':targets,'door_projected_pixels':[projected(p) for p in corners],'door_corner_rmse_pixels':math.sqrt(best/8),'camera_parameters':par,'assumed_depth_planes_m':[t[2] for t in traces],'limitations':['Camera fit uses the same four door points, not independent validation','Steel silhouette traced at inferred depth planes; not measured 3D','Back half remains first-pass inferred geometry','No full 1:1 claim; material and film lighting not matched','GLB procedural weathering not baked']}
(OUT/'calibration.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Suzume_v2.blend'))
bpy.ops.export_scene.gltf(filepath=str(OUT/'Suzume_v2.glb'),export_format='GLB',export_cameras=True,export_extras=True)
scene.render.filepath=str(OUT/'front_v2.png');bpy.ops.render.render(write_still=True)
bpy.ops.object.camera_add(location=(19,-22,17));checkcam=bpy.context.object;checkcam.name='Geometry_check_oblique';checkcam.rotation_euler=(Vector((0,4,2))-checkcam.location).to_track_quat('-Z','Y').to_euler();checkcam.data.lens=35;scene.camera=checkcam;scene.render.resolution_x=1200;scene.render.resolution_y=850;scene.render.filepath=str(OUT/'oblique_v2.png');bpy.ops.render.render(write_still=True)
scene.camera=cam;scene.render.resolution_x=840;scene.render.resolution_y=1000;scene.render.filepath=str(OUT/'front_v2.png');bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Suzume_v2.blend'))
print('V2_DONE',report)
