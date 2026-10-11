from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np,json,hashlib
R=Path(__file__).parent;O=R/'poster-fascia-v47';V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
ref=Image.open(V/'reference-hires.jpg').convert('RGB').resize((2124,3000));before=Image.open(R/'poster-railings-v46/railing-detail-v46.png').convert('RGB');after=Image.open(O/'fascia-detail-v47.png').convert('RGB')
crops=[ref.crop((0,543*3,280*3,581*3)),before.crop((0,(543-495)*3,280*3,(581-495)*3)),after.crop((0,(543-495)*3,280*3,(581-495)*3))]
out=Image.new('RGB',(840,3*(114+26)),(20,26,29));draw=ImageDraw.Draw(out)
for k,(im,label) in enumerate(zip(crops,['Reference','Before v46','After v47'])):draw.text((8,k*140+6),label,fill='white');out.paste(im,(0,k*140+26))
out.save(O/'fascia-comparison-v47.png')
arrays=[np.asarray(im) for im in [ref,before,after]];colors=[]
for a,offset in zip(arrays,[0,495,495]):colors.append(np.median(a[(559-offset)*3:(562-offset)*3,75*3:95*3,:3],axis=(0,1)))
errors=[float(np.linalg.norm(c-colors[0])) for c in colors[1:]]
report={'scope':'One unobstructed local fascia strip, x=75..95 and y=559..562 at 708x1000. RGB median diagnostic, not whole-scene equivalence.','referenceRGBMedian':colors[0].tolist(),'beforeRGBMedian':colors[1].tolist(),'afterRGBMedian':colors[2].tolist(),'beforeRGBDistance':errors[0],'afterRGBDistance':errors[1],'oneToOneComplete':False}
(O/'fascia-comparison-v47.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
