from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib
R=Path(__file__).parent;O=R/'poster-right-facade-v54';V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103');native=O/'Suzume_dual_scene_right_facade_v54.blend';v=json.loads((O/'verification-v54.json').read_text());assert hashlib.sha256(native.read_bytes()).hexdigest()==v['nativeSha256'];assert (O/'right-facade-detail-v54.png').stat().st_mtime>native.stat().st_mtime
reference=Image.open(V/'reference-hires.jpg').crop((390*2000/708,600*2.824,2000,715*2.824)).resize((954,345),Image.Resampling.LANCZOS).convert('RGB');before=Image.open(O/'right-facade-before-v53.png').convert('RGB');after=Image.open(O/'right-facade-detail-v54.png').convert('RGB');assert before.size==after.size==(954,345);canvas=Image.new('RGB',(954,1113),(20,26,29));draw=ImageDraw.Draw(canvas)
for i,(im,label) in enumerate([(reference,'Reference'),(before,'Before v53'),(after,'After v54')]):draw.text((8,i*371+5),label,fill='white');canvas.paste(im,(0,i*371+26))
canvas.save(O/'right-facade-comparison-v54.png');print('RIGHT_FACADE_54_COMPARISON_SAVED')
