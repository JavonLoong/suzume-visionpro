from pathlib import Path
import bpy,json,hashlib,sys,ast,numpy as np
R=Path(__file__).parent;O=R/'poster-water-v40';sys.path.insert(0,str(R))
from poster_water_setup_v40 import apply_water
source=R/'poster-steel-v39/Suzume_dual_scene_steel_v39.blend'
q=json.loads((O/'water-spec-v40.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(source))
s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1)
water=next(o for o in s.objects if o.name.startswith('Live planar reflective shallow water'))
movie=bpy.data.scenes['Daytime circular hotel'];assert water.data.materials[0] not in set(m for o in movie.objects if o.type=='MESH' for m in o.data.materials if m)
mat=apply_water(s,q);s['poster_water_revision']=40
s.render.resolution_x=708;s.render.resolution_y=1000;s.render.resolution_percentage=100;s.render.use_border=False;s.render.use_crop_to_border=False;s.cycles.samples=32;s.cycles.use_denoising=True
native=O/'Suzume_dual_scene_water_v40.blend';bpy.ops.wm.save_as_mainfile(filepath=str(native))
audit={'revision':40,'sourceNativeSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'nativeSha256':hashlib.sha256(native.read_bytes()).hexdigest(),'waterObject':water.name,'waterMaterial':mat.name,'parameters':q,'sourceImageUsedInWaterShader':False,'changedGeometry':False,'oneToOneComplete':False}
(O/'integration-v40.json').write_text(json.dumps(audit,indent=2),encoding='utf-8');print('POSTER_WATER_40_SAVED',audit['nativeSha256'],flush=True)
