from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib
R=Path(__file__).parent;O=R/'poster-low-rails-v53';V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103');native=O/'Suzume_dual_scene_low_rails_v53.blend';v=json.loads((O/'verification-v53.json').read_text());assert hashlib.sha256(native.read_bytes()).hexdigest()==v['nativeSha256'];assert (O/'low-rails-detail-v53.png').stat().st_mtime>native.stat().st_mtime
im=Image.open(V/'reference-hires.jpg');reference=im.crop((0,650*2.824,305*2000/708,714*2.824)).resize((915,192),Image.Resampling.LANCZOS).convert('RGB');before=Image.open(R/'poster-ground-v52/ground-detail-v52.png').convert('RGB').crop((0,0,915,192));after=Image.open(O/'low-rails-detail-v53.png').convert('RGB').crop((0,0,915,192));canvas=Image.new('RGB',(915,654),(20,26,29));draw=ImageDraw.Draw(canvas)
for i,(im,label) in enumerate([(reference,'Reference'),(before,'Before v52'),(after,'After v53')]):draw.text((8,i*218+5),label,fill='white');canvas.paste(im,(0,i*218+26))
canvas.save(O/'low-rails-comparison-v53.png');print('LOW_RAILS_53_COMPARISON_SAVED')
