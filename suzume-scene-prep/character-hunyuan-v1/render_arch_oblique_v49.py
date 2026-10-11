from pathlib import Path
import bpy,json,hashlib
from mathutils import Vector
R=Path(__file__).parent;O=R/'poster-arches-v49';native=O/'Suzume_dual_scene_arches_v49.blend';report=json.loads((O/'verification-v49.json').read_text());assert hashlib.sha256(native.read_bytes()).hexdigest()==report['nativeSha256']
bpy.ops.wm.open_mainfile(filepath=str(native));s=bpy.data.scenes['Official poster courtyard v38'];bpy.context.window.scene=s;s.frame_set(1);s.camera.location=(-8.5,13,5.8);s.camera.rotation_euler=(Vector((-12.8,20,5.30))-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.lens=54;s.render.use_border=False;s.render.use_crop_to_border=False;s.render.resolution_x=900;s.render.resolution_y=500;s.render.resolution_percentage=100;s.cycles.samples=24;s.cycles.use_denoising=True;s.render.filepath=str(O/'arch-oblique-detail-v49.png');bpy.ops.render.render(write_still=True);print('ARCHES_49_OBLIQUE_DETAIL_DONE',flush=True)
