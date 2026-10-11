import bpy,json,math
from pathlib import Path
from mathutils import Vector
R=Path(__file__).parent;O=R/'movie-material-v22';O.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'movie-windows-v21'/'Suzume_scene_movie_windows_v21.blend'))
s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72);bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();cam=s.camera
sun=next(o for o in s.objects if o.type=='LIGHT' and o.data.type=='SUN');sun_direction=sun.matrix_world.to_quaternion()@Vector((0,0,1))
regions=json.loads((R/'movie-windows-v21'/'facade-color-gap-v21.json').read_text())['regions'];rows=[]
for region in regions:
    q=region['referenceBox'];u=(q[0]+q[2])/2;v=(q[1]+q[3])/2;aspect=s.render.resolution_x/s.render.resolution_y
    ray=cam.matrix_world.to_quaternion()@Vector(((u/2552-.5)*36/30*aspect,(.5-v/1656)*36/30,-1));ray.normalize()
    hit,location,normal,face,obj,matrix=s.ray_cast(deps,cam.matrix_world.translation,ray)
    record={'region':region['region'],'visibleObject':obj.name if obj else None,'point':list(location),'normal':list(normal),'sunIncidenceCosine':normal.dot(sun_direction),'towardSun':[]}
    if hit:
        origin=location+normal*.015
        for i in range(6):
            h,pt,no,fi,ob,ma=s.ray_cast(deps,origin,sun_direction,distance=1000)
            if not h:break
            record['towardSun'].append({'object':ob.name,'distance':(pt-location).length,'shadowVisible':ob.visible_shadow,'point':list(pt)})
            origin=pt+sun_direction*.015
    rows.append(record)
materials=[]
for name in ['Circular ruined hotel with exterior entrance solid mesh.017','Circular ruined hotel with exterior entrance solid mesh.008']:
    m=bpy.data.materials[name];materials.append({'name':name,'diffuse':list(m.diffuse_color),'nodes':[{'name':n.name,'type':n.type,'image':n.image.name if n.type=='TEX_IMAGE' and n.image else None,'inputs':{i.name:list(i.default_value) if hasattr(i.default_value,'__len__') and not isinstance(i.default_value,str) else i.default_value for i in n.inputs if hasattr(i,'default_value')}} for n in m.node_tree.nodes]})
out={'sceneExposure':s.view_settings.exposure,'viewTransform':s.view_settings.view_transform,'sun':{'object':sun.name,'energy':sun.data.energy,'color':list(sun.data.color),'directionTowardSun':list(sun_direction)},'sampleRays':rows,'materials':materials}
(O/'shadow-diagnosis-v22.json').write_text(json.dumps(out,indent=2),encoding='utf-8');print(json.dumps(out,indent=2),flush=True)
