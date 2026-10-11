"""Correct the measured roof shadow and the new bay's yellow-green plaster."""
from pathlib import Path
import bpy,json,math,sys,numpy as np,hashlib
from mathutils import Vector
R=Path(__file__).parent;O=R/'movie-material-v22';O.mkdir(exist_ok=True)
F=json.loads((R/'movie-windows-v21'/'window-fit-v21.json').read_text());fit=json.loads((R/'movie-calibration-v20'/'courtyard-fit-v20.json').read_text());p=fit['parameters'];k=fit['depthScale'];C=np.array(fit['depthScaleCenter']);angle=F['angle']+p['yaw'];sin=math.sin(angle);cos=math.cos(angle)
bpy.ops.wm.open_mainfile(filepath=str(R/'movie-windows-v21'/'Suzume_scene_movie_windows_v21.blend'))
s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72);bpy.context.view_layer.update()
def to_local(a):
    q=C+(a-C)/k;xx=q[:,0]-p['translateX'];yy=q[:,1]-p['translateY'];return np.column_stack((cos*xx-sin*yy,(q[:,2]-p['heightOffset'])/p['heightScale'],F['chordRadius']-(sin*xx+cos*yy)))
def to_world(a):
    a=np.array(a,float).reshape(-1,3);x,y,z=a.T;q=np.column_stack((sin*(F['chordRadius']-z)+x*cos+p['translateX'],cos*(F['chordRadius']-z)-x*sin+p['translateY'],y*p['heightScale']+p['heightOffset']));return C+k*(q-C)
def mesh_hash(o):
    a=np.empty(len(o.data.vertices)*3,np.float32);o.data.vertices.foreach_get('co',a);return hashlib.sha256(a.tobytes()).hexdigest()
wall=bpy.data.objects['Solid plaster wall with two through-openings v21'];wall_before=mesh_hash(wall)
changes=[]
for name,old_center,old_depth,new_center,new_depth in [('Upper cornice v21',.08,.70,.025,.30),('Upper wall shadow course v21',.035,.55,.025,.20)]:
    o=bpy.data.objects[name];a=np.array([v.co[:] for v in o.data.vertices]);local=to_local(a);local[:,2]=new_center+(local[:,2]-old_center)*new_depth/old_depth;o.data.vertices.foreach_set('co',to_world(local).astype('f4').ravel());o.data.update();o.data.normals_split_custom_set([(0,0,0)]*len(o.data.loops));changes.append({'part':name,'oldDepth':old_depth,'newDepth':new_depth,'oldCenter':old_center,'newCenter':new_center})
o=bpy.data.objects['Roof slab v21'];a=np.array([v.co[:] for v in o.data.vertices]);local=to_local(a);old_front=local[:,2].copy();local[:,2]=-4.595+(old_front+4.595)*(.12+4.595)/(.355+4.595);local[:,0]*=(F['chordRadius']-local[:,2])/(F['chordRadius']-old_front)
o.data.vertices.foreach_set('co',to_world(local).astype('f4').ravel());o.data.update();o.data.normals_split_custom_set([(0,0,0)]*len(o.data.loops));changes.append({'part':o.name,'oldFrontProjection':.355,'newFrontProjection':.12,'backRetained':-4.595})

def srgb_hex(value):
    q=np.array([(value>>16)&255,(value>>8)&255,value&255])/255;return np.where(q<=.04045,q/12.92,((q+.055)/1.055)**2.4)
new_materials={}
for source,name,color in [('Circular ruined hotel with exterior entrance solid mesh.017','Movie pale plaster v22',0xf1eee6),('Circular ruined hotel with exterior entrance solid mesh.008','Movie warm stone trim v22',0xe9e5d7),('Circular ruined hotel with exterior entrance solid mesh.014','Movie shaded glazing v22',0x213040),('Circular ruined hotel with exterior entrance solid mesh.011','Movie aged window frame v22',0x777562)]:
    old=bpy.data.materials[source];m=old.copy();m.name=name;rgb=srgb_hex(color);m.diffuse_color=(*rgb,1)
    for node in m.node_tree.nodes:
        if node.type=='MIX_RGB' and node.blend_type=='MULTIPLY':node.inputs[1].default_value=(*rgb,1)
        if node.type=='BSDF_PRINCIPLED':node.inputs['Base Color'].default_value=(*rgb,1)
    new_materials[old]=m
for o in bpy.data.collections['Movie right facade — solid openings v21'].objects:
    for slot in o.material_slots:
        if slot.material in new_materials:slot.material=new_materials[slot.material]

power=4800
if '--power' in sys.argv:power=float(sys.argv[sys.argv.index('--power')+1])
normal=Vector((-sin,-cos,0));position=Vector(to_world([[-1,4.4,0]])[0])+normal*7;target=Vector(to_world([[.1,3.2,0]])[0])
data=bpy.data.lights.new('Soft courtyard fill on the movie facade v22','AREA');data.shape='RECTANGLE';data.size=11;data.size_y=10;data.energy=power;data.color=(1,.90,.72)
light=bpy.data.objects.new(data.name,data);s.collection.objects.link(light);light.location=position;light.rotation_euler=(target-position).to_track_quat('-Z','Y').to_euler()
light['purpose']='Approximate bright, diffuse courtyard illumination in the animated reference. Inferred light; no measured physical lighting data.'
bpy.context.view_layer.update();assert mesh_hash(wall)==wall_before
audit={'revision':22,'changedRoofParts':changes,'wallGeometryHash':wall_before,'wallAndWindowGeometryPreserved':True,'materials':{old.name:new.name for old,new in new_materials.items()},'fillLight':{'type':'AREA','powerWatts':power,'dimensions':[11,10],'position':list(position),'target':list(target),'color':list(data.color)},'foregroundOnBackSideOfEmitter':float((Vector((0,0,1.5))-position).normalized().dot((target-position).normalized()))<0,'oneToOneComplete':False}

# Repeat the diagnosed upper-wall shadow ray after reducing the overhang.
point=Vector((22.275026321411133,30.829051971435547,13.98263931274414));sun=bpy.data.objects['DirectionalLight'];direction=sun.matrix_world.to_quaternion()@Vector((0,0,1));deps=bpy.context.evaluated_depsgraph_get()
h,pt,no,fi,ob,ma=s.ray_cast(deps,point+normal*.015,direction,distance=10)
audit['upperPlasterSunBlockerAfter']=ob.name if h else None
assert not h or not ob.visible_shadow,audit['upperPlasterSunBlockerAfter']
s.render.resolution_x=720;s.render.resolution_y=468;s.render.resolution_percentage=100;s.cycles.samples=24;s.cycles.use_denoising=True
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Suzume_scene_movie_material_v22.blend'));(O/'integration-v22.json').write_text(json.dumps(audit,indent=2),encoding='utf-8');print('FACADE_CORRECTION_SAVED',json.dumps(audit),flush=True)
if '--trials' in sys.argv:
    s.render.use_border=True;s.render.use_crop_to_border=False;s.render.border_min_x=520/720;s.render.border_max_x=1;s.render.border_min_y=(468-250)/468;s.render.border_max_y=(468-45)/468;s.render.use_persistent_data=True
    for energy in [0,600,1200]:
        data.energy=energy;s.render.filepath=str(O/f'facade-trial-{energy}.png');bpy.ops.render.render(write_still=True);print('FACADE_TRIAL_RENDERED',energy,flush=True)
if '--render' in sys.argv:
    s.render.use_border=False;data.energy=power;s.cycles.samples=32;s.render.filepath=str(O/'movie-front-v22.png');bpy.ops.render.render(write_still=True)
