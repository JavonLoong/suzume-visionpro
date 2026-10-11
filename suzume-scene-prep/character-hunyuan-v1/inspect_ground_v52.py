from pathlib import Path
import bpy,json,hashlib,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).parent;O=R/'poster-ground-v52';O.mkdir(exist_ok=True);source=R/'poster-foreground-v51/Suzume_dual_scene_foreground_v51.blend';sha=hashlib.sha256(source.read_bytes()).hexdigest();assert sha=='01726e6771ec7ba31008c64487b2c73a4d70c567eceaea34116191f50902b074'
bpy.ops.wm.open_mainfile(filepath=str(source));s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1);bpy.context.view_layer.update();camera=np.array(s.camera.matrix_world);C=camera[:3,3];rot=camera[:3,:3];f=s.camera.data.lens/s.camera.data.sensor_height*1000;arrays={};rows=[];extra=[];vv=[];ff=[];tags=[];offset=0
for ob in s.objects:
 if ob.type!='MESH' or ob.hide_render:continue
 m=ob.data
 if not len(m.polygons):continue
 a=np.array([v.co[:] for v in m.vertices]);M=np.array(ob.matrix_world);world=a@M[:3,:3].T+M[:3,3];m.calc_loop_triangles();faces=np.array([t.vertices[:] for t in m.loop_triangles]);lo=world.min(0);hi=world.max(0)
 ishotel=ob.name.startswith('Circular ruined hotel with exterior entrance solid mesh')
 if ishotel:key='mesh'+str(len(rows))
 elif lo[2]<1.1 and hi[2]<3 and (lo[1]>3 or 'flagstone' in ob.name.lower()):key='extra'+str(len(extra))
 else:continue
 arrays[key+'_vertices']=world;arrays[key+'_faces']=faces;rec={'key':key,'name':ob.name,'vertices':len(world),'triangles':len(faces),'materials':[m.name for m in ob.data.materials],'bounds':[lo.tolist(),hi.tolist()]};(rows if ishotel else extra).append(rec)
 keep=world[faces][:,:,2].max(1)<1.1;selected=faces[keep];vv.extend(world.tolist());ff.extend((selected+offset).tolist());tags.extend([[ob.name,key,int(i)] for i in np.flatnonzero(keep)]);offset+=len(world)
tree=BVHTree.FromPolygons(vv,ff,all_triangles=True);probes=[]
for u,v in [(8,698),(30,698),(50,699),(80,699),(94,699),(145,699),(180,700),(200,700),(225,701),(270,703),(50,709),(90,704),(162,706),(260,707),(13,711),(286,710)]:
 ray=rot@np.array([(u-354)/f,(500-v)/f,-1]);ray/=np.linalg.norm(ray);hit=tree.ray_cast(Vector(C),Vector(ray),100);rec={'uv':[u,v]}
 if hit[0] is not None:rec.update({'hit':list(hit[0]),'object':tags[hit[2]][0],'key':tags[hit[2]][1],'triangle':tags[hit[2]][2]})
 probes.append(rec)
np.savez_compressed(O/'source-ground-v52.npz',**arrays);out={'sourceNativeSha256':sha,'objects':rows,'extraObjects':extra,'camera':{'position':C.tolist(),'rotation':rot.tolist(),'focalPixels':f},'probes':probes};(O/'source-ground-v52.json').write_text(json.dumps(out,indent=2),encoding='utf-8');print(json.dumps({'hotelMeshes':len(rows),'extraMeshes':extra,'probes':probes},indent=2),flush=True)
