from pathlib import Path
import bpy,json,hashlib
R=Path(__file__).parent;O=R/'poster-arches-v49';report=json.loads((O/'verification-v49.json').read_text());source=R/'poster-upper-windows-v48/Suzume_dual_scene_upper_windows_v48.blend';native=O/'Suzume_dual_scene_arches_v49.blend'
def images():
 return {im.name:hashlib.sha256(im.packed_file.data).hexdigest() for im in bpy.data.images if im.packed_file}
assert hashlib.sha256(source.read_bytes()).hexdigest()==report['sourceNativeSha256'];bpy.ops.wm.open_mainfile(filepath=str(source));before=images();assert before
assert hashlib.sha256(native.read_bytes()).hexdigest()==report['nativeSha256'];bpy.ops.wm.open_mainfile(filepath=str(native));after=images();assert before==after
(O/'packed-image-preservation-v49.json').write_text(json.dumps({'nativeSha256':report['nativeSha256'],'allPackedImageBytesPreserved':True,'imageCount':len(after),'images':after},indent=2));print('ARCHES_49_PACKED_IMAGES_PRESERVED',len(after))
