"""Read the actual saved night volumes, sky and portal transport before editing."""
from pathlib import Path
import bpy,json,numpy as np,hashlib
from mathutils import Vector
R=Path(__file__).parent;O=R/'movie-night-v30';O.mkdir(exist_ok=True)
source=R/'movie-water-v29/Suzume_scene_movie_water_v29.blend';bpy.ops.wm.open_mainfile(filepath=str(source))
s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72);bpy.context.view_layer.update()
def val(v):
    if isinstance(v,(bool,int,float,str)):return v
    try:return list(v)
    except:return str(v)
def material(m):
    return {'name':m.name,'properties':{k:val(v) for k,v in m.items()},'nodes':[{'name':n.name,'type':n.bl_idname,'operation':getattr(n,'operation',None),'image':getattr(n,'image',None).name if getattr(n,'image',None) else None,'inputs':[{'index':i,'name':sock.name,'value':val(sock.default_value),'linked':sock.is_linked} for i,sock in enumerate(n.inputs) if hasattr(sock,'default_value')]} for n in m.node_tree.nodes],'links':[[l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name] for l in m.node_tree.links]}
rows=[]
for ob in bpy.data.collections['Editable night realm'].all_objects:
    if not ob.name.startswith('Spatial twilight cloud volume ') and ob.name!='Native enclosing night sky':continue
    bound=np.array([list(ob.matrix_world@Vector(p)) for p in ob.bound_box]);row={'name':ob.name,'location':list(ob.location),'scale':list(ob.scale),'rotation':list(ob.rotation_euler),'matrix':[list(r) for r in ob.matrix_world],'worldBounds':[bound.min(0).tolist(),bound.max(0).tolist()],'parent':ob.parent.name if ob.parent else None,'hideRender':ob.hide_render,'visibleCamera':ob.visible_camera,'visibleShadow':ob.visible_shadow,'materials':[material(m) for m in ob.data.materials]};rows.append(row)
    if ob.name.startswith('Spatial twilight cloud'):
        v=next(n for n in ob.data.materials[0].node_tree.nodes if n.type=='PRINCIPLED_VOLUME');print('CLOUD',ob.name,list(ob.location),list(ob.scale),'COLOR',list(v.inputs['Color'].default_value),'EMISSION',list(v.inputs['Emission Color'].default_value),flush=True)
    else:
        print('SKY',ob.name,'BOUNDS',row['worldBounds'],'SHADOW',ob.visible_shadow,flush=True)
        for n in ob.data.materials[0].node_tree.nodes:
            if n.type=='TEX_ENVIRONMENT':
                im=n.image;a=np.empty(len(im.pixels),np.float32);im.pixels.foreach_get(a);a=a.reshape(-1,4);row['image']={'name':im.name,'size':list(im.size),'colorspace':im.colorspace_settings.name,'rgbMin':a[:,:3].min(0).tolist(),'rgbMax':a[:,:3].max(0).tolist(),'packed':bool(im.packed_file)};print('SKY_IMAGE',row['image'],flush=True)
            elif n.type=='EMISSION':print('SKY_EMISSION_STRENGTH',n.inputs['Strength'].default_value,flush=True)
instances=[]
for ob in s.objects:
    if ob.instance_type=='COLLECTION' and ob.instance_collection:instances.append({'name':ob.name,'collection':ob.instance_collection.name,'matrix':[list(r) for r in ob.matrix_world]})
aperture=bpy.data.objects['Spatial doorway portal aperture'];portal={'matrix':[list(r) for r in aperture.matrix_world],'materials':[material(m) for m in aperture.data.materials]}
result={'sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'objects':rows,'instances':instances,'portal':portal,'camera':{'matrix':[list(r) for r in s.camera.matrix_world],'lens':s.camera.data.lens},'sceneExposure':s.view_settings.exposure,'oneToOneComplete':False}
(O/'source-inspection-v30.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print('NIGHT_30_INSPECTED',len(rows),flush=True)
