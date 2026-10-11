from pathlib import Path
import numpy as np,json
from PIL import Image
R=Path(__file__).parent;O=R/'movie-bays-v23'
regions=json.loads((O/'left-color-regions-v23.json').read_text(encoding='utf-8'));variants=[]
paths=sorted(O.glob('left-light-trial-*.png'))
if (O/'lighting-v23.json').exists():paths.append(O/'movie-front-v23.png')
for path in paths:
    image=np.asarray(Image.open(path).convert('RGB'),dtype=float);rows=[]
    for roi in regions:
        x,y,xx,yy=roi['renderBox'];actual=np.median(image[y:yy,x:xx].reshape(-1,3),axis=0);target=np.array(roi['referenceMedian'])
        rows.append({'region':roi['name'],'median':actual.tolist(),'target':target.tolist(),'rgbDistance':float(np.linalg.norm(actual-target))})
    variants.append({'file':path.name,'patches':rows,'meanRgbDistance':float(np.mean([r['rgbDistance'] for r in rows]))})
result={'scope':'Three manually selected facade patches only, not a complete visual fidelity score.','variants':variants}
(O/'left-light-comparison-v23.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
for v in sorted(variants,key=lambda v:v['meanRgbDistance']):print(v['file'],round(v['meanRgbDistance'],2),[r['median'] for r in v['patches']])
