from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib
R=Path(__file__).parent;O=R/'poster-ground-v52';V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103');native=O/'Suzume_dual_scene_ground_v52.blend';v=json.loads((O/'verification-v52.json').read_text());assert hashlib.sha256(native.read_bytes()).hexdigest()==v['nativeSha256'];assert (O/'ground-detail-v52.png').stat().st_mtime>native.stat().st_mtime
im=Image.open(V/'reference-hires.jpg');reference=im.crop((0,650*2.824,305*2000/708,714*2.824)).resize((915,192),Image.Resampling.LANCZOS).convert('RGB');before=Image.open(R/'poster-foreground-v51/foreground-detail-v51.png').convert('RGB').crop((0,225,915,417));after=Image.open(O/'ground-detail-v52.png').convert('RGB').crop((0,0,915,192));canvas=Image.new('RGB',(915,654),(20,26,29));draw=ImageDraw.Draw(canvas)
for i,(im,label) in enumerate([(reference,'Reference'),(before,'Before v51'),(after,'After v52')]):draw.text((8,i*218+5),label,fill='white');canvas.paste(im,(0,i*218+26))
canvas.save(O/'ground-comparison-v52.png');reference.save(O/'reference-detail-v52.png');print('GROUND_52_COMPARISON_SAVED')
