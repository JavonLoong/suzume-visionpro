from pathlib import Path
import bpy,json,hashlib,numpy as np
R=Path(__file__).parent;O=R/'poster-right-facade-v54';O.mkdir(exist_ok=True);source=R/'poster-low-rails-v53/Suzume_dual_scene_low_rails_v53.blend';sha=hashlib.sha256(source.read_bytes()).hexdigest();assert sha=='436a97857da27ee66d68b501b46abace9c50187898cfce77acc84e11d9953b1f';bpy.ops.wm.open_mainfile(filepath=str(source));s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1);bpy.context.view_layer.update();arrays={};rows=[];hotel=0;debris=0;cam=np.array(s.camera.matrix_world)
for ob in s.objects:
 if ob.type!='MESH':continue
 if ob.name.startswith('Circular ruined hotel with exterior entrance solid mesh'):key='mesh'+str(hotel);hotel+=1
 else:continue
 m=ob.data;m.calc_loop_triangles();a=np.array([v.co[:] for v in m.vertices]);M=np.array(ob.matrix_world);world=a@M[:3,:3].T+M[:3,3];faces=np.array([t.vertices[:] for t in m.loop_triangles]);arrays[key+'_vertices']=world;arrays[key+'_faces']=faces;rows.append({'key':key,'name':ob.name,'vertices':len(a),'triangles':len(faces),'materials':[m.name for m in ob.data.materials]})
np.savez_compressed(O/'source-right-facade-v54.npz',**arrays);data={'sourceNativeSha256':sha,'objects':rows,'camera':{'position':cam[:3,3].tolist(),'rotation':cam[:3,:3].tolist(),'focalPixels':s.camera.data.lens/s.camera.data.sensor_height*1000}};(O/'source-right-facade-v54.json').write_text(json.dumps(data,indent=2));print('LOW_RAILS_53_SOURCE',hotel,debris,rows[-2:])
