"""Selected sky/cloud patch diagnostics only; no overall similarity claim."""
from pathlib import Path
from PIL import Image
import numpy as np,json
R=Path(__file__).parent;O=R/'movie-night-v30';q=json.loads((O/'night-spec-v30.json').read_text(encoding='utf-8'))
paths={'reference':R/'movie-surfaces-v28/reference-opening.jpg','previous':R/'movie-water-v29/movie-front-v29.png','current':O/'movie-front-v30.png'}
ims={k:np.asarray(Image.open(p).convert('RGB')) for k,p in paths.items()};rows={}
for name,box in q['referencePatchBoxes'].items():
    rows[name]={}
    for key,im in ims.items():
        h,w=im.shape[:2];x0,y0,x1,y1=[round(v*(w/2552 if i%2==0 else h/1656)) for i,v in enumerate(box)];p=im[y0:y1,x0:x1]
        rows[name][key]={'meanRGB':np.mean(p,axis=(0,1)).round(2).tolist(),'medianRGB':np.median(p.reshape(-1,3),axis=0).tolist()}
result={'revision':30,'renders':{k:p.name for k,p in paths.items()},'patches':rows,'interpretation':'Manually selected sky/cloud patches; density silhouettes and occlusion can differ within each patch. These statistics do not measure all-angle fidelity or overall similarity.','oneToOneComplete':False}
(O/'night-appearance-v30.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(rows,indent=2))
