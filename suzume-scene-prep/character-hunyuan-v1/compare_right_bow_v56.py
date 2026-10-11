from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib
R=Path(__file__).parent;O=R/'poster-right-bow-v56';V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103');native=O/'Suzume_dual_scene_right_bow_v56.blend';v=json.loads((O/'verification-v56.json').read_text());assert hashlib.sha256(native.read_bytes()).hexdigest()==v['nativeSha256'];assert (O/'right-bow-detail-v56.png').stat().st_mtime>native.stat().st_mtime
reference=Image.open(V/'reference-hires.jpg').crop((500*2000/708,570*2.824,2000,635*2.824)).resize((832,260),Image.Resampling.LANCZOS).convert('RGB');before=Image.open(O/'right-bow-before-v55.png').convert('RGB');after=Image.open(O/'right-bow-detail-v56.png').convert('RGB');assert before.size==after.size==(832,260);canvas=Image.new('RGB',(832,858),(20,26,29));draw=ImageDraw.Draw(canvas)
for i,(im,label) in enumerate([(reference,'Reference'),(before,'Before v55'),(after,'After v56')]):draw.text((8,i*286+5),label,fill='white');canvas.paste(im,(0,i*286+26))
canvas.save(O/'right-bow-comparison-v56.png');print('RIGHT_BOW_56_COMPARISON_SAVED')
