"""Local water color and reflection contrast diagnostics, not a fidelity score."""
from pathlib import Path
from PIL import Image,ImageFilter
import json,numpy as np
R=Path(__file__).parent;O=R/'movie-water-v29'
source=Image.open(R/'movie-surfaces-v28/reference-opening.jpg').convert('RGB')
patches={'left foreground paving':[100,1350,650,1600],'left middle water':[120,1000,650,1200],'right broad reflection':[1800,1030,2450,1280],'right foreground':[1850,1370,2460,1600]}
def inspect(im):
    # A common resolution keeps the local contrast statistic comparable.
    im=im.resize((720,468),Image.Resampling.LANCZOS);rows={}
    for key,box in patches.items():
        b=[round(v*im.size[i%2]/source.size[i%2]) for i,v in enumerate(box)];crop=im.crop(b);a=np.asarray(crop,dtype=float);smooth=np.asarray(crop.filter(ImageFilter.GaussianBlur(1.2)),dtype=float);l=smooth@[.2126,.7152,.0722]
        rows[key]={'meanSrgb255':np.round(a.mean((0,1)),2).tolist(),'medianSrgb255':np.round(np.median(a.reshape(-1,3),0),2).tolist(),'softLuminanceP90minusP10':float(np.percentile(l,90)-np.percentile(l,10)),'brightPixelFraction':float(np.mean(a.max(2)>225))}
    return rows
result={'scope':'Manually chosen water patches at a common resolution. Colors and local contrast only; not overall fidelity.','referenceBoxes':patches,'reference':inspect(source),'renders':{}}
for file in [R/'movie-surfaces-v28/movie-front-v28.png',*sorted(O.glob('trial-*.png')),*O.glob('movie-front-v29.png')]:result['renders'][file.name]=inspect(Image.open(file).convert('RGB'))
(O/'water-appearance-v29.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
for name,rows in [('reference',result['reference']),*result['renders'].items()]:print(name,{k:row['meanSrgb255'] for k,row in rows.items()})
