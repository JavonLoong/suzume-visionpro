import bpy,math,json
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
ROOT=Path(__file__).parent;OUT=ROOT/'reconstruction_v4';OUT.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'reconstruction_v3/Suzume_v3.blend'))
s=bpy.context.scene;cam=bpy.data.objects['Reference_camera_630x750'];s.camera=cam
s.render.resolution_x=1008;s.render.resolution_y=1200
def project(p):
 q=world_to_camera_view(s,cam,p);return(q.x*630,(1-q.y)*750)
def unproject(px,py,y):
 f=cam.data.view_frame(scene=s);xs=[v.x for v in f];ys=[v.y for v in f]
 d=cam.matrix_world.to_3x3()@Vector((min(xs)+(max(xs)-min(xs))*px/630,max(ys)-(max(ys)-min(ys))*py/750,f[0].z))
 return cam.location+d*((y-cam.location.y)/d.y)
def grounded(px,py,z=.04):
 a=unproject(px,py,0);b=unproject(px,py,1);return(z-a.z)/(b.z-a.z)
col=bpy.data.collections.new('V4_Reference_supported_layout');s.collection.children.link(col)
left=bpy.data.materials['Cool weathered left facade'];right=bpy.data.materials['Sunlit ochre green facade'];edge=bpy.data.materials['Reference cornice stone'];green=bpy.data.materials['Oxidized green window frames'];dark=bpy.data.materials['Dark recess']
changes=[]
def meshob(name,verts,faces,mat,evidence):
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);o=bpy.data.objects.new(name,mesh);col.objects.link(o);mesh.materials.append(mat);o['evidence']=evidence;return o
def box(name,rect,depth,thick,mat,evidence='position traced in official front; depth inferred'):
 x0,y0,x1,y1=rect;pts=[unproject(x,y,depth) for x,y in [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]]
 return meshob(name,[tuple(v) for v in pts]+[tuple(v+Vector((0,thick,0))) for v in pts],[(3,2,1,0),(4,5,6,7),(1,5,4,0),(2,6,5,1),(3,7,6,2),(0,4,7,3)],mat,evidence)
def rod(name,a,b,r,mat,evidence='reference arcade silhouette; depth inferred'):
 d=b-a;verts=[(r*math.cos(i*math.pi/6),r*math.sin(i*math.pi/6),z) for z in [-d.length/2,d.length/2] for i in range(12)]
 o=meshob(name,verts,[tuple(reversed(range(12))),tuple(range(12,24))]+[(i,(i+1)%12,(i+1)%12+12,i+12) for i in range(12)],mat,evidence);o.location=(a+b)/2;o.rotation_euler=d.to_track_quat('Z','Y').to_euler();return o
def screenline(name,pts,dep,r,mat):
 ps=[unproject(x,y,dep) for x,y in pts]
 for a,b in zip(ps,ps[1:]):rod(name,a,b,r,mat)
removed=[]
fac=bpy.data.collections.get('04_Reference_facade')
for ob in list(fac.objects):
 pts=[project(ob.matrix_world@Vector(v)) for v in ob.bound_box];x=sum(p[0] for p in pts)/8;y=sum(p[1] for p in pts)/8
 # Two large entrance arches were invented by the repetitive bay generator.
 invented=('Masonry entrance arch' in ob.name or 'Masonry arch jamb' in ob.name) and (x<47 or 432<x<483)
 # Main building ends before the outer raised arcade / distant low block.
 outside=x>563
 # The last bay crosses the actual main-building corner; rebuild it explicitly.
 corner=533<x<=563 and y>473
 if invented or outside or corner:
  removed.append(ob.name);bpy.data.objects.remove(ob,do_unlink=True)
changes.append({'change':'Remove two unsupported large entrance arches','reference_centres_px':[[19,482],[457,493]]})
changes.append({'change':'Main right facade terminates near x=563, no longer across the whole frame','reference_corner_px':[563,520]})
# Trim scattered moss that was attached to the removed extension.
for ob in list(bpy.data.collections['07_Vegetation'].objects):
 if ob.type!='MESH':continue
 x,y=project(ob.matrix_world.translation)
 if x>564 and 467<y<525:bpy.data.objects.remove(ob,do_unlink=True)
# Reconstruct the final actual bay and its return wall as a connected three-dimensional corner.
dep=grounded(548,521)
box('Right final bay sill',(534,512,563,521),dep,.65,right)
box('Right final bay header',(534,472,563,482),dep,.65,right)
for x in [534,560]:box('Right final bay pier',(x,472,x+3,520),dep,.65,right)
box('Right final bay dark interior',(537,483,560,512),dep+1.0,.15,dark)
for x in range(539,559,5):box('Right final bay mullion',(x,483,x+.65,512),dep-.025,.1,green)
for y in [486,499,510]:box('Right final bay transom',(537,y,560,y+.65),dep-.025,.1,green)
# Visible return runs away from the facade, leaving the distant background exposed.
a=unproject(563,520,dep);b=unproject(577,510,dep+3.0)
topa=unproject(563,473,dep);topb=unproject(577,468,dep+3.0)
meshob('Right wing return wall',[tuple(p) for p in [a,b,topb,topa]],[(0,1,2,3)],right,'right wing return inferred from visible corner; depth 3 working units provisional')
# A low distant block is separated from the foreground main wing.
far=grounded(620,515)
box('Distant low building',(600,487,642,515),far,.5,right)
box('Distant low cornice',(598,483,645,488),far-.1,.8,edge)
for x in [605,616,628,639]:
 box('Distant rectangular window',(x-3,491,x+3,507),far-.02,.035,dark)
 box('Distant window centre bar',(x-.3,491,x+.3,507),far-.05,.05,green)
# Continuous raised arcade following one shared three-dimensional path.
def arcadepoint(x,y):return unproject(x,y,dep+(x-563)*.05)
def arcbox(name,rect,mat):
 x0,y0,x1,y1=rect;cx=(x0+x1)/2
 ps=[arcadepoint(x,y-(x-cx)*.23) for x,y in [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]]
 return meshob(name,[tuple(v) for v in ps]+[tuple(v+Vector((0,.6,0))) for v in ps],[(3,2,1,0),(4,5,6,7),(1,5,4,0),(2,6,5,1),(3,7,6,2),(0,4,7,3)],mat,'continuous path from visible arcade; depth provisional')
for k in range(7):
 x0=563+k*11;x1=x0+11;cx=(x0+x1)/2
 y=458-(cx-563)*.23
 arcbox('Raised arcade parapet',(x0,y-11,x1,y-8),edge)
 for x in [x0,x1]:
  yp=458-(x-563)*.23;arcbox('Raised arcade pier',(x-.5,yp-8,x+.5,yp+6),right)
 pts=[(cx+4.8*math.cos(i*math.pi/16),y-1-6*math.sin(i*math.pi/16)) for i in range(17)]
 ps=[arcadepoint(x,yy-(x-cx)*.23) for x,yy in pts]
 for p,q in zip(ps,ps[1:]):rod('Raised arcade arch',p,q,.038,edge)
 arcbox('Raised arcade lower band',(x0,y+6,x1,y+8),right)
for x in [563,640]:
 p=arcadepoint(x,466-(x-563)*.23);q=Vector((p.x,p.y,.04));rod('Arcade grounded support',q,p,.09,right,'inferred support at return and outside reference crop')
changes.append({'change':'Separate right main wing, return, elevated arcade and distant low building','depth_status':'inferred, not triangulated'})
# Upper left volumes are closed wall masses with openings, not open skeletal galleries.
for x0,y0,x1,y1 in [(89,414,143,445),(147,420,190,450),(199,426,255,454)]:
 d=grounded((x0+x1)/2,524)+1.0
 box('Left upper solid sill',(x0,y1-7,x1,y1),d+.13,.5,left)
 box('Left upper solid lintel',(x0,y0,x1,y0+9),d+.13,.5,left)
 for x in range(x0+4,x1-4,17):box('Left upper wall between windows',(x,y0+8,x+7,y1-6),d+.13,.5,left)
 box('Left upper back wall',(x0,y0+8,x1,y1-6),d+1.0,.2,dark)
changes.append({'change':'Restore solid upper-left wall masses and recessed windows','reference_bounds_px':[[89,414,143,445],[147,420,190,450],[199,426,255,454]]})
s['reconstruction_status']='V4 explicit facade-placement corrections; depth still inferred and rear layout unverified.'
(OUT/'layout_changes.json').write_text(json.dumps({'reference':'official_front.jpg','reference_size':[630,750],'changes':changes,'removed_objects':len(removed),'limitations':['Single-image positions are constrained; 3D depth is not solved','Do not treat Hunyuan generation as geometric ground truth','Side and rear layout remain unverified','No 1:1 completion claim']},ensure_ascii=False,indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Suzume_v4_layout.blend'))
bpy.ops.export_scene.gltf(filepath=str(OUT/'Suzume_v4_layout.glb'),export_format='GLB',export_cameras=True,export_extras=True)
s.cycles.samples=48;s.render.filepath=str(OUT/'front_v4.png');bpy.ops.render.render(write_still=True)
bpy.ops.object.camera_add(location=(18,-21,14));c=bpy.context.object;c.name='Layout_inspection';c.rotation_euler=(Vector((0,5,2))-c.location).to_track_quat('-Z','Y').to_euler();c.data.lens=37;s.camera=c;s.render.resolution_x=1200;s.render.resolution_y=850;s.render.filepath=str(OUT/'layout_v4.png');bpy.ops.render.render(write_still=True)
s.camera=cam;s.render.resolution_x=1008;s.render.resolution_y=1200;bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Suzume_v4_layout.blend'))
print('V4_READY',len(removed),len(s.objects))
