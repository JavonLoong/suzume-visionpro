"""Clean reference-driven head candidate. Procedural geometry, not AI texture.

The v17 reconstruction supplies scale/orientation. Face landmarks and hair
layout follow the film reference; this remains an approximation until reviewed.
"""
import bpy, math, json, numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
H=Path(__file__).parent;O=H/'clean-v18';O.mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
parts=[]
def linear(hexcolor):
    a=np.array([int(hexcolor[i:i+2],16)/255 for i in (0,2,4)])
    return np.where(a<=.04045,a/12.92,((a+.055)/1.055)**2.4).tolist()+[1]
def material(name,color,rough=.8):
    m=bpy.data.materials.new(name);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=linear(color)
    p.inputs['Roughness'].default_value=rough;p.inputs['Specular IOR Level'].default_value=.12
    return m
skin=material('Suzume warm skin','dfbd91');skin_shadow=material('Ear and nostril warm shadow','b58967')
hair=material('Dark warm brown hair','3b3532');hair_line=material('Fine hair edge','2b2826');hair_light=material('Subtle combed hair','524840')
white=material('Warm eye white','eee8da');iris_rim=material('Dark iris rim','504039');iris=material('Brown iris','987054')
amber=material('Iris lower amber','b78856');pupil=material('Pupil and eyelashes','302b29');highlight=material('Eye catchlight','fff9ed',.55)
gold=material('Gold left barrette','cc962d',.5);red=material('Red crossed left barrette','a84d48',.5)
def mesh(name,vertices,faces,mat):
    data=bpy.data.meshes.new(name);data.from_pydata(vertices,[],faces);data.update()
    obj=bpy.data.objects.new(name,data);bpy.context.scene.collection.objects.link(obj);data.materials.append(mat)
    for p in data.polygons:p.use_smooth=True
    obj['head_part_v18']=True;parts.append(obj);return obj
def sphere(name,center,scale,mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=40,ring_count=24,location=center)
    obj=bpy.context.object;obj.name=name;obj.scale=scale
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    obj.data.materials.append(mat)
    for p in obj.data.polygons:p.use_smooth=True
    obj['head_part_v18']=True;parts.append(obj);return obj
def bezier(points,t):
    a,b,c,d=[np.asarray(p,float) for p in points]
    return (1-t)**3*a+3*(1-t)**2*t*b+3*(1-t)*t*t*c+t**3*d
def line(name,points,mat,depth=.004,taper=False):
    data=bpy.data.curves.new(name,'CURVE');data.dimensions='3D';data.bevel_depth=depth;data.bevel_resolution=2
    s=data.splines.new('POLY');s.points.add(len(points)-1)
    for i,(p,co) in enumerate(zip(s.points,points)):
        p.co=(*co,1)
        if taper:p.radius=.12+.88*math.sin(math.pi*(i/(len(points)-1)*.86+.07))
    obj=bpy.data.objects.new(name,data);bpy.context.scene.collection.objects.link(obj);data.materials.append(mat)
    obj['head_part_v18']=True;parts.append(obj);return obj
knots=np.array([-.52,-.43,-.25,0,.20,.40,.62,.77,.84])
widths=np.array([.018,.19,.33,.423,.452,.455,.37,.21,.015])
fronts=np.array([-.30,-.405,-.48,-.495,-.48,-.44,-.345,-.18,-.03])
backs=np.array([.10,.20,.36,.49,.55,.55,.48,.29,.04])
def hermite(z,values):
    z=float(np.clip(z,knots[0],knots[-1]));i=min(len(knots)-2,max(0,int(np.searchsorted(knots,z)-1)))
    slopes=np.empty(len(values));slopes[0]=(values[1]-values[0])/(knots[1]-knots[0]);slopes[-1]=(values[-1]-values[-2])/(knots[-1]-knots[-2])
    slopes[1:-1]=(values[2:]-values[:-2])/(knots[2:]-knots[:-2])
    h=knots[i+1]-knots[i];t=(z-knots[i])/h
    return (2*t**3-3*t*t+1)*values[i]+(t**3-2*t*t+t)*h*slopes[i]+(-2*t**3+3*t*t)*values[i+1]+(t**3-t*t)*h*slopes[i+1]
def face_y(x,z):
    w=max(.025,hermite(z,widths));f=hermite(z,fronts);b=hermite(z,backs);center=(f+b)/2
    u=min(.999,abs(x)/w);y=center-(center-f)*(1-u**4)**.5
    y-=.060*math.exp(-(x/.065)**2-((z+.035)/.115)**2)
    y-=.021*math.exp(-(x/.12)**2-((z+.245)/.065)**2)
    return y
vertices=[];faces=[];nr=112;nt=160
for i,z in enumerate(np.linspace(-.52,.84,nr)):
    w=max(.01,hermite(z,widths));f=hermite(z,fronts);b=hermite(z,backs);center=(f+b)/2
    for j in range(nt):
        angle=2*math.pi*j/nt;x=w*math.sin(angle)
        y=face_y(x,z) if math.cos(angle)>=0 else center+(b-center)*(-math.cos(angle))
        # The chin rises continuously toward the jaw hinges, rather than ending
        # in a horizontal ring under the face.
        jaw_lift=(1-math.cos(angle))*.5*max(0,(-z-.20)/.32)*.18
        vertices.append((x,y,z+jaw_lift))
        if i:
            a=(i-1)*nt+j;c=(i-1)*nt+(j+1)%nt;d=i*nt+(j+1)%nt;e=i*nt+j
            faces.append((a,e,d,c))
bottom_center=len(vertices);vertices.append((0,-.10,-.43))
top_center=len(vertices);vertices.append((0,0,.84))
for j in range(nt):
    faces.append((bottom_center,j,(j+1)%nt))
    faces.append((top_center,(nr-1)*nt+(j+1)%nt,(nr-1)*nt+j))
mesh('Clean facial surface',vertices,faces,skin)
# A neck with real volume, subsequently fitted inside the existing collar.
vertices=[];faces=[]
for i,z in enumerate(np.linspace(-1.0,-.10,32)):
    for j in range(64):
        a=2*math.pi*j/64;r=.115+max(0,(-z-.78))*.20
        vertices.append((r*math.cos(a),.06+r*1.15*math.sin(a),z))
        if i:faces.append(((i-1)*64+j,i*64+j,i*64+(j+1)%64,(i-1)*64+(j+1)%64))
mesh('Clean neck',vertices,faces,skin)
for sign in [-1,1]:
    sphere(('Right' if sign<0 else 'Left')+' ear',(sign*.455,-.015,.015),(.072,.064,.145),skin)
    sphere(('Right' if sign<0 else 'Left')+' ear concha',(sign*.522,-.016,.021),(.008,.024,.070),skin_shadow)
    points=[]
    for a in np.linspace(-.85,4.1,36):points.append((sign*.526,-.015+.043*math.cos(a),.021+.104*math.sin(a)))
    line('Ear helix',points,skin,.010)
def patch(name,cx,cz,rx,rz,offset,mat,tilt=0,almond=False,eye_center=None):
    offset*=.35
    v=[(cx,face_y(cx,cz)-offset,cz)];f=[];segments=64;rings=16
    for ring in range(1,rings+1):
        r=ring/rings
        for j in range(segments):
            a=2*math.pi*j/segments;x=cx+rx*r*math.cos(a);vertical=math.sin(a)
            if almond:vertical=math.copysign(abs(vertical)**1.35,vertical)*(1 if vertical>0 else .87)
            z=cz+rz*r*vertical+tilt*(x-cx)
            if eye_center is not None:
                ex,ez=eye_center;u=min(1,abs((x-ex)/.132))
                up=ez+.097*max(0,1-u*u)**.675;down=ez-.084*max(0,1-u*u)**.675
                z=float(np.clip(z,down+.0003,up-.0003))
            v.append((x,face_y(x,z)-offset,z))
            if ring==1:f.append((0,1+j,1+(j+1)%segments))
            else:
                prev=1+(ring-2)*segments;cur=1+(ring-1)*segments
                f.append((prev+j,cur+j,cur+(j+1)%segments,prev+(j+1)%segments))
    return mesh(name,v,f,mat)
for sign in [-1,1]:
    cx=sign*.224;cz=.17;side='left' if sign>0 else 'right';eye=(cx,cz)
    patch(side+' sclera',cx,cz,.132,.097,.006,white,almond=True)
    patch(side+' limbus',cx,cz-.004,.075,.090,.008,iris_rim,eye_center=eye)
    patch(side+' iris',cx,cz-.004,.067,.083,.010,iris,eye_center=eye)
    patch(side+' lower iris amber',cx,cz-.051,.036,.025,.012,amber,eye_center=eye)
    patch(side+' tall pupil',cx,cz+.006,.029,.050,.014,pupil,eye_center=eye)
    patch(side+' upper catchlight',cx-.024,cz+.037,.017,.026,.018,highlight,-.15,eye_center=eye)
    patch(side+' lower catchlight',cx+.028,cz-.031,.006,.009,.018,highlight,eye_center=eye)
    for label,points,thickness,mat in [
        ('upper lashes',[(cx-.132,cz),(cx-.094,cz+.128),(cx+.091,cz+.129),(cx+.132,cz)],.006,pupil),
        ('lower lid',[(cx-.07,cz-.070),(cx-.027,cz-.09),(cx+.059,cz-.093),(cx+.111,cz-.034)],.0008,skin_shadow),
        ('eyebrow',[(cx-.134,.361),(cx-.08,.432),(cx+.064,.430),(cx+.126,.362)],.008,pupil)]:
        coords=[]
        for t in np.linspace(0,1,40):
            x,z=bezier(points,t);coords.append((x,face_y(x,z)-.012,z))
        line(side+' '+label,coords,mat,thickness,True)
    outer=cx+sign*.12
    for i in range(3):
        z=cz+.010+i*.019;x=outer-sign*.005*i
        line(side+' eyelash '+str(i),[(x,face_y(x,z)-.014,z),(x+sign*(.026-i*.003),face_y(x,z)-.014,z+.021)],pupil,.003,True)
for sign in [-1,1]:patch('Subtle nostril',sign*.023,-.093,.008,.004,.004,skin_shadow)
mouth=[]
for t in np.linspace(0,1,40):
    x,z=bezier([(-.074,-.25),(-.03,-.239),(.035,-.241),(.075,-.255)],t);mouth.append((x,face_y(x,z)-.004,z))
line('Quiet mouth line',mouth,skin_shadow,.0032,True)
# Smooth scalp cap. Bangs and side locks are separate closed swept meshes.
v=[];f=[];rows=64;cols=144
for i in range(rows):
    for j in range(cols):
        theta=2*math.pi*j/cols;a=abs((theta+math.pi)%(2*math.pi)-math.pi)
        bottom=float(np.interp(a,[0,.6,1.55,math.pi],[.57,.39,-.10,-.31]))
        z=.8949+(bottom-.8949)*i/(rows-1)
        sphere_factor=math.sqrt(max(0,1-((z-.25)/.645)**2))
        blend=float(np.clip((z-.43)/.15,0,1));blend=blend*blend*(3-2*blend)
        w=(max(.018,hermite(min(z,.84),widths))+.035)*(1-blend)+.51*sphere_factor*blend
        fz=(hermite(min(z,.84),fronts)-.034)*(1-blend)+(.045-.525*sphere_factor)*blend
        bz=(hermite(min(z,.84),backs)+.034)*(1-blend)+(.045+.575*sphere_factor)*blend;mid=(fz+bz)/2
        x=w*math.sin(theta);co=math.cos(theta)
        y=mid-(mid-fz)*math.sqrt(max(0,1-math.sin(theta)**4)) if co>=0 else mid+(bz-mid)*(-co)
        v.append((x,y,z))
        if i:f.append(((i-1)*cols+j,i*cols+j,i*cols+(j+1)%cols,(i-1)*cols+(j+1)%cols))
mesh('Smooth hair cap',v,f,hair)
def lock(name,controls,width,depth=.018,mat=hair):
    v=[];f=[];rows=40;cols=12
    for side in [-1,1]:
        for i,t in enumerate(np.linspace(0,1,rows)):
            center=bezier(controls,t);tangent=bezier(controls,min(1,t+.001))-bezier(controls,max(0,t-.001))
            transverse=np.array([tangent[2],0,-tangent[0]]);transverse/=max(1e-9,np.linalg.norm(transverse))
            breadth=width*(.45+.55*math.sin(math.pi*t*.82))*(1-t**3)+.0004
            for j,u in enumerate(np.linspace(-1,1,cols)):
                p=center+transverse*u*breadth/2
                if 'bang' in name or 'forelock' in name or 'temple' in name:
                    p[1]=face_y(p[0],min(p[2],.832))-.030
                p[1]+=side*depth*(.45+.55*(1-u*u))
                v.append(p.tolist())
                if i and j:
                    k=(0 if side<0 else rows*cols)+i*cols+j
                    quad=(k-cols-1,k-1,k,k-cols)
                    f.append(quad if side<0 else tuple(reversed(quad)))
    layer=rows*cols
    for i in range(rows-1):
        for j in [0,cols-1]:
            a=i*cols+j;b=(i+1)*cols+j;f.append((a,b,b+layer,a+layer))
    mesh(name,v,f,mat)
    return controls
locks=[
 ('Swept right temple',[(-.10,-.32,.77),(-.34,-.48,.67),(-.49,-.48,.40),(-.46,-.39,.25)],.17),
 ('Fine right forelock',[(-.14,-.33,.78),(-.27,-.54,.62),(-.22,-.58,.35),(-.16,-.54,.245)],.075),
 ('Central pointed bang',[(-.08,-.34,.78),(-.11,-.61,.63),(-.04,-.60,.33),(.035,-.55,.225)],.15),
 ('Middle pointed bang',[(-.045,-.33,.78),(.09,-.63,.62),(.14,-.60,.36),(.205,-.53,.235)],.19),
 ('Left pointed bang',[(.015,-.32,.78),(.25,-.57,.66),(.30,-.57,.38),(.36,-.45,.27)],.20),
 ('Left temple sweep',[(.10,-.29,.77),(.40,-.46,.65),(.49,-.44,.36),(.51,-.24,.17)],.20),
 ('Right side lock',[(-.48,-.18,.27),(-.53,-.19,.03),(-.49,-.14,-.34),(-.39,-.11,-.60)],.071),
 ('Left side lock',[(.48,-.18,.27),(.54,-.19,.02),(.49,-.14,-.37),(.40,-.11,-.60)],.071),
 ('First small crown tuft',[(-.14,-.20,.79),(-.24,-.25,.86),(-.25,-.17,.95),(-.18,-.11,.974)],.034),
 ('Second small crown tuft',[(-.12,-.17,.80),(-.14,-.21,.89),(-.10,-.12,.95),(-.025,-.055,.967)],.033)]
for name,controls,width in locks:lock(name,controls,width)
sphere('Ponytail tie',(0,.615,.51),(.13,.065,.09),hair_line)
for k in range(6):
    angle=2*math.pi*k/6;dx=.09*math.cos(angle);dy=.065*math.sin(angle)
    controls=[(dx*.3,.615+dy*.2,.51),(dx,.85+dy,.48),(dx*1.5,.79+dy,-.32),(dx*1.3+.025,.64+dy,-.77-.10*(k%3)/2)]
    v=[];f=[]
    for i,t in enumerate(np.linspace(0,1,48)):
        center=bezier(controls,t);tangent=Vector(bezier(controls,min(1,t+.001))-bezier(controls,max(0,t-.001))).normalized()
        transverse=Vector((1,0,0));second=tangent.cross(transverse).normalized()
        radius=float((.060+.025*math.sin(math.pi*t))*(1-t**3)+.0005)
        for j in range(20):
            a=2*math.pi*j/20;p=Vector(center)+radius*(math.cos(a)*transverse+math.sin(a)*second)
            v.append(tuple(p))
            if i:f.append(((i-1)*20+j,i*20+j,i*20+(j+1)%20,(i-1)*20+(j+1)%20))
    mesh('Solid ponytail lock '+str(k),v,f,hair)
# Mount pins on the *outer hair*, including overlapping locks, not on the face
# approximation. Sample along each bar so a straight chord cannot cut inside.
hair_vertices=[];hair_faces=[]
for obj in parts:
    if obj.type=='MESH' and obj.data.materials[0] in (hair,hair_line):
        base=len(hair_vertices);hair_vertices.extend([v.co.copy() for v in obj.data.vertices])
        hair_faces.extend([tuple(base+i for i in p.vertices) for p in obj.data.polygons])
hair_bvh=BVHTree.FromPolygons(hair_vertices,hair_faces)
for name,ends,mat in [
    ('Left gold hairpin',[(.235,.607),(.365,.667)],gold),
    ('Left red hairpin slash',[(.298,.407),(.384,.528)],red),
    ('Left red hairpin crossbar',[(.272,.497),(.416,.450)],red)]:
    pts=[]
    for t in np.linspace(0,1,28):
        x,z=np.array(ends[0])*(1-t)+np.array(ends[1])*t
        hit,normal,idx,dist=hair_bvh.ray_cast(Vector((x,-2,z)),Vector((0,1,0)))
        if hit is None:raise RuntimeError(f'Hairpin {name} is outside the hair at {x},{z}')
        pts.append((x,hit.y-.011,z))
    line(name,pts,mat,.010)
# Convert every element to a portable mesh; curves remain reproducible in code.
for obj in bpy.context.scene.objects:obj.select_set(False)
for obj in parts:obj.select_set(True)
bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.convert(target='MESH')
parts=[o for o in bpy.context.scene.objects if o.type=='MESH' and o.get('head_part_v18')]
for obj in parts:
    obj['origin']='Reference-driven clean mathematical geometry; Hunyuan v17 used for dimensions and registration only.'
    obj.data.calc_loop_triangles()
audit={'revision':18,'method':'Reference-driven smooth facial surface, actual curved eye geometry, separate swept hair locks and physical left hairpins',
       'notNewHunyuanGeneration':True,'meshParts':len(parts),'triangles':sum(len(o.data.loop_triangles) for o in parts),'oneToOneComplete':False,
       'reference':'reference-suzume-official-face.jpg and existing generated four-view guides','status':'candidate_pending_comparison'}
(O/'candidate-audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
bpy.ops.export_scene.gltf(filepath=str(O/'Suzume-clean-head-v18.glb'),export_format='GLB',use_selection=True,export_animations=False)
s=bpy.context.scene;s.name='Clean head comparison v18';s.render.engine='CYCLES';s.cycles.samples=48;s.cycles.use_denoising=True
s.render.resolution_x=480;s.render.resolution_y=560;s.render.resolution_percentage=100;s.view_settings.view_transform='Standard';s.view_settings.look='None'
s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.5,.5,.5,1);s.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.6
for pos,power,size in [((3,-4,5),250,4),((-3,-2,1),100,4),((0,4,4),160,3)]:
    d=bpy.data.lights.new('Comparison softbox','AREA');d.energy=power;d.shape='DISK';d.size=size
    o=bpy.data.objects.new(d.name,d);s.collection.objects.link(o);o.location=pos;o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler()
d=bpy.data.cameras.new('Reference comparison');cam=bpy.data.objects.new(d.name,d);s.collection.objects.link(cam);s.camera=cam;d.type='ORTHO';d.ortho_scale=2.2
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Suzume-clean-head-v18.blend'))
for label,a in [('front',0),('left',math.pi/2),('back',math.pi),('threequarter',.42)]:
    cam.location=(5*math.sin(a),-5*math.cos(a),0);cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler()
    s.render.filepath=str(O/f'head-{label}.png');bpy.ops.render.render(write_still=True)
print('CLEAN_HEAD_CANDIDATE',json.dumps(audit),flush=True)
