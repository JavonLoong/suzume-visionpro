"""Read-only color sampling, not an image transformation or fidelity verdict."""
from pathlib import Path
from PIL import Image
import numpy as np,json
O=Path(__file__).parent;R=O.parent
V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
ref=np.asarray(Image.open(V/'reference-opening-50525.jpg').convert('RGB'))
regions={'shirt':(1135,714,1215,791),'skirt':(1130,898,1230,1060),'hair':(1140,546,1200,625)}
targets={name:np.median(ref[y0:y1,x0:x1].reshape(-1,3),axis=0) for name,(x0,y0,x1,y1) in regions.items()}
def inspect(path,crop=False):
    data=np.asarray(Image.open(path).convert('RGB'));rows={};score=0
    for name,(x0,y0,x1,y1) in regions.items():
        coords=np.array([x0*720/2552,y0*468/1656,x1*720/2552,y1*468/1656]).astype(int)
        if crop:coords-=np.array([272,65,272,65])
        a,b,c,d=coords;pixels=data[b:d,a:c].reshape(-1,3)
        median=np.median(pixels,axis=0);error=float(np.linalg.norm(median-targets[name]));score+=error
        rows[name]={'medianRGB':median.tolist(),'targetRGB':targets[name].tolist(),'RGBDistance':error,'samplePixels':len(pixels)}
    return {'file':path.name,'regions':rows,'meanRGBDistance':score/3}
result={'method':'Median RGB in manually selected shirt, skirt and hair regions, projected by the existing reference camera fit. This measures only local color and is not a one-to-one or all-view score.',
        'variants':[inspect(R/'native-pose-front-v17.png'),inspect(O/'portal-light-candidate.png')]}
for power in [15,30,50]:
    path=O/f'aperture-light-{power}.png'
    if path.exists():result['variants'].append(inspect(path,True))
(O/'light-color-comparison.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
