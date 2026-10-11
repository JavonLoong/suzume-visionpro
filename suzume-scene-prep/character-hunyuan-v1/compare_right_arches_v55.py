from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib
R=Path(__file__).parent;O=R/'poster-right-arches-v55';V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103');native=O/'Suzume_dual_scene_right_arches_v55.blend';v=json.loads((O/'verification-v55.json').read_text());assert hashlib.sha256(native.read_bytes()).hexdigest()==v['nativeSha256'];assert (O/'right-arches-detail-v55.png').stat().st_mtime>native.stat().st_mtime
reference=Image.open(V/'reference-hires.jpg').crop((430*2000/708,558*2.824,2000,625*2.824)).resize((834,201),Image.Resampling.LANCZOS).convert('RGB');before=Image.open(O/'right-arches-before-v54.png').convert('RGB');after=Image.open(O/'right-arches-detail-v55.png').convert('RGB');assert before.size==after.size==(834,201);canvas=Image.new('RGB',(834,681),(20,26,29));draw=ImageDraw.Draw(canvas)
for i,(im,label) in enumerate([(reference,'Reference'),(before,'Before v54'),(after,'After v55')]):draw.text((8,i*227+5),label,fill='white');canvas.paste(im,(0,i*227+26))
canvas.save(O/'right-arches-comparison-v55.png');print('RIGHT_ARCHES_55_COMPARISON_SAVED')
