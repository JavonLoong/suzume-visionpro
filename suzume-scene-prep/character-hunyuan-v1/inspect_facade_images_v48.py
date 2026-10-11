from pathlib import Path
import bpy,hashlib
R=Path(__file__).parent
bpy.ops.wm.open_mainfile(filepath=str(R/'poster-upper-windows-v48/Suzume_dual_scene_upper_windows_v48.blend'))
for name in ['Reference-calibrated facade surface pigments.001','Reference-calibrated upper facade pigments v48']:
 m=bpy.data.materials.get(name)
 for n in m.node_tree.nodes:
  if n.type=='TEX_IMAGE' and n.image:
   im=n.image;print(name,im.name,list(im.size),im.file_format,hashlib.sha256(im.packed_file.data).hexdigest(),flush=True)

original=bpy.data.materials['Reference-calibrated facade surface pigments.001']
image=next(n.image for n in original.node_tree.nodes if n.type=='TEX_IMAGE' and n.image and list(n.image.size)==[1100,330])
(R/'poster-upper-windows-v48/original-facade-pigments-v48.png').write_bytes(image.packed_file.data)
