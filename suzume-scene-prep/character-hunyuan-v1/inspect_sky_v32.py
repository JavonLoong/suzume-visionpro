"""Inspect real door transforms and luminous stars for a second reference camera."""
from pathlib import Path
import bpy,json,hashlib,numpy as np,sys
from mathutils import Vector
R=Path(__file__).parent;O=R/'movie-sky-v32';O.mkdir(exist_ok=True);V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103');sys.path.insert(0,str(R));from night_audit_v30 import fingerprint,topology,material_digest
source=R/'movie-terrain-v31/Suzume_scene_movie_terrain_v31.blend';bpy.ops.wm.open_mainfile(filepath=str(source));s=bpy.data.scenes['Daytime circular hotel'];bpy.context.window.scene=s;s.frame_set(72);bpy.context.view_layer.update()
frame=bpy.data.objects['Complete six-panel white door and frame'];hinge=bpy.data.objects['Animated door leaf and hinges'];M=hinge.matrix_world;F=frame.matrix_world
points={}
for i,p in enumerate(json.loads((V/'door-panel-calibration-v10.json').read_text())['panel_parameters']):
    x,y,w,h=p['parameters']
    for side in [-1,1]:
        for name,dx,dy in [('BL',-1,-1),('BR',1,-1),('TR',1,1),('TL',-1,1)]:points[f'panel{i}_{side}_{name}']=list(M@Vector((x+dx*w/2,y+dy*h/2,side*.085)))
for key,pt in {'knobFront':[1.5625,1.626,.18],'knobBack':[1.5625,1.626,-.18],'leafBL':[0,0,.055],'leafBR':[1.6,0,.055],'leafTR':[1.6,3.4,.055],'leafTL':[0,3.4,.055]}.items():points[key]=list(M@Vector(pt))
for side in [-1,1]:
    for z in [0,.2,1,2,3,3.7]:points[f'frame{side}_{z}']=list(F@Vector((side*.815,z,.12)))
star=bpy.data.objects['Spatial luminous stars'];verts=np.array([v.co[:] for v in star.data.vertices]);MW=np.array(star.matrix_world);world=verts@MW[:3,:3].T+MW[:3,3];groups=world.reshape(-1,6,3);centers=groups.mean(1);radii=np.linalg.norm(groups-centers[:,None,:],axis=2).max(1)
result={'sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'frameMatrix':[list(r) for r in F],'hingeMatrix':[list(r) for r in M],'points':points,'starCount':len(centers),'largeStars':[{'index':int(i),'center':centers[i].tolist(),'radius':float(radii[i])} for i in np.argsort(radii)[-12:]],'starWorldHash':fingerprint(star),'starTopologyHash':topology(star),'starMaterial':{'name':star.data.materials[0].name,'graphHash':material_digest(star.data.materials[0])},'sceneCompositorEnabled':s.use_nodes,'worldExposure':s.view_settings.exposure}
(O/'source-inspection-v32.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');np.savez_compressed(O/'original-stars-v32.npz',world=world,centers=centers,radii=radii)
print(json.dumps({k:v for k,v in result.items() if k!='points'},ensure_ascii=True),flush=True)
