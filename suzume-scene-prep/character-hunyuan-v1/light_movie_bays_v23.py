"""Fit the cool shade and localized sunlight visible around the left arch."""
from pathlib import Path
import bpy,json,numpy as np,math,sys
from mathutils import Vector
R=Path(__file__).parent;O=R/'movie-bays-v23'
bpy.ops.wm.open_mainfile(filepath=str(O/'Suzume_scene_movie_bays_v23.blend'))
s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72)
F=json.loads((O/'bay-fit-v23.json').read_text(encoding='utf-8'));b=next(b for b in F['bays'] if b['index']==13)
fit=json.loads((R/'movie-calibration-v20/courtyard-fit-v20.json').read_text(encoding='utf-8'));p=fit['parameters'];k=fit['depthScale'];C=np.array(fit['depthScaleCenter']);a=b['angle']+p['yaw'];n=Vector((-math.sin(a),-math.cos(a),0))
def point(x,y):
    q=np.array([b['chordRadius']*math.sin(a)+x*math.cos(a)+p['translateX'],b['chordRadius']*math.cos(a)-x*math.sin(a)+p['translateY'],y*p['heightScale']+p['heightOffset']])
    return Vector(C+k*(q-C))
def set_color(name,value):
    m=bpy.data.materials[name];q=np.array([(value>>16)&255,(value>>8)&255,value&255])/255;rgb=np.where(q<=.04045,q/12.92,((q+.055)/1.055)**2.4);m.diffuse_color=(*rgb,1)
    for node in m.node_tree.nodes:
        if node.type=='MIX_RGB' and node.blend_type=='MULTIPLY':node.inputs[1].default_value=(*rgb,1)
        if node.type=='BSDF_PRINCIPLED':node.inputs['Base Color'].default_value=(*rgb,1)
set_color('Movie bay material material-2 v23',0xe1e4e6)
set_color('Movie bay material material-1 v23',0xe4e5e3)
def emitter(name,kind,pos,target,color,power):
    obj=bpy.data.objects.get(name)
    if not obj:
        data=bpy.data.lights.new(name,kind);obj=bpy.data.objects.new(name,data);s.collection.objects.link(obj)
    data=obj.data;data.energy=power;data.color=color;obj.location=pos;obj.rotation_euler=(target-pos).to_track_quat('-Z','Y').to_euler()
    obj['purpose']='Inferred movie illumination; not measured physical lighting.'
    return obj
ambient_target=point(-.3,3.1);ambient_position=point(-.3,4.4)+n*7
refined='--refined' in sys.argv
shade=emitter('Cool courtyard fill on the left facade v23','AREA',ambient_position,ambient_target,(.45,.28,1) if refined else (.55,.7,1),500)
shade.data.shape='RECTANGLE';shade.data.size=16;shade.data.size_y=12
sun_target=point(1.55,2.5) if refined else point(1.35,3.1);sun_position=sun_target+n*7+Vector((0,0,5))
key=emitter('Localized sunlight around the arched window v23','SPOT',sun_position,sun_target,(1,.78,.72) if refined else (1,.90,.77),1600)
key.data.spot_size=math.radians(45);key.data.spot_blend=.15;key.data.shadow_soft_size=.10
s.render.resolution_x=720;s.render.resolution_y=468;s.render.resolution_percentage=100;s.cycles.samples=24;s.cycles.use_denoising=True
if '--trials' in sys.argv:
    s.render.use_border=True;s.render.use_crop_to_border=False;s.render.border_min_x=0;s.render.border_max_x=255/720;s.render.border_min_y=(468-205)/468;s.render.border_max_y=(468-75)/468;s.render.use_persistent_data=True
    variants=[(320,3200),(320,4800),(320,6400)] if refined else [(0,0),(250,800),(500,1600),(750,2400)]
    for ambient,power in variants:
        shade.data.energy=ambient;key.data.energy=power;s.render.filepath=str(O/f"left-light-trial-{'refined-' if refined else ''}{ambient}-{power}.png");bpy.ops.render.render(write_still=True);print('LEFT_LIGHT_TRIAL',ambient,power,flush=True)
if '--save' in sys.argv:
    ambient=float(sys.argv[sys.argv.index('--ambient')+1]) if '--ambient' in sys.argv else 500
    power=float(sys.argv[sys.argv.index('--key')+1]) if '--key' in sys.argv else 1600
    shade.data.energy=ambient;key.data.energy=power;s.render.use_border=False
    specs=[]
    for ob,target in [(shade,ambient_target),(key,sun_target)]:
        d=ob.data;specs.append({'name':ob.name,'type':d.type,'powerWatts':d.energy,'position':list(ob.location),'target':list(target),'color':list(d.color),
            **({'dimensions':[d.size,d.size_y]} if d.type=='AREA' else {'angleRadians':d.spot_size/2,'blend':d.spot_blend})})
    audit={'revision':23,'materials':{'material-2':0xe1e4e6,'material-1':0xe4e5e3},'lights':specs,'inferredLighting':True,'oneToOneComplete':False}
    bpy.ops.wm.save_as_mainfile(filepath=str(O/'Suzume_scene_movie_bays_v23.blend'));(O/'lighting-v23.json').write_text(json.dumps(audit,indent=2),encoding='utf-8');print('LEFT_LIGHT_SAVED',json.dumps(audit),flush=True)
    if '--render' in sys.argv:
        s.render.filepath=str(O/'movie-front-v23.png');bpy.ops.render.render(write_still=True)
