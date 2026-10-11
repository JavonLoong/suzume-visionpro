"""Compare selected material and illumination patches, without a fidelity score."""
from pathlib import Path
from PIL import Image
import json,numpy as np
R=Path(__file__).parent;O=R/'movie-lighting-v27'
reference=Image.open('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103/reference-opening-50525.jpg').convert('RGB')
patches={p['patch']:p['referenceBox'] for p in json.loads((R/'movie-shore-v26/appearance-patches-v26.json').read_text(encoding='utf-8'))['patches']}
patches.update({'character white blouse':[1138,711,1170,752],'left white door frame':[938,685,952,945],'clear sky':[2240,120,2350,160]})
def sample(im,box):
    rgb=np.asarray(im.crop(box),dtype=float).reshape(-1,3)/255;med=np.median(rgb,axis=0);linear=np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4)
    return {'medianSrgb255':np.round(med*255,2).tolist(),'medianLinearLuminance':float(np.median(linear@[.2126,.7152,.0722]))}
result={'purpose':'Manually selected broad patch comparison, not an overall fidelity score.','referencePatches':{n:sample(reference,b)for n,b in patches.items()},'renders':{}}
for p in [R/'movie-shore-v26/movie-front-v26.png',*O.glob('trial-*.png'),*O.glob('movie-front-v27.png')]:
    im=Image.open(p).convert('RGB');rows={}
    for name,box in patches.items():
        scaled=[round(v*im.size[i%2]/reference.size[i%2])for i,v in enumerate(box)];rows[name]=sample(im,scaled);rows[name]['overReferenceLuminance']=rows[name]['medianLinearLuminance']/result['referencePatches'][name]['medianLinearLuminance']
    result['renders'][p.name]=rows
(O/'appearance-comparison-v27.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
for name,rows in result['renders'].items():print(name,json.dumps({k:{'rgb':v['medianSrgb255'],'ratio':round(v['overReferenceLuminance'],2)}for k,v in rows.items()}))
