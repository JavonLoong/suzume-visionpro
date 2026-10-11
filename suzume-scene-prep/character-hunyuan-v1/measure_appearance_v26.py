"""Matched broad patches for diagnosing lighting, not a scene-fidelity score."""
from pathlib import Path
from PIL import Image
import json,numpy as np
R=Path(__file__).parent;O=R/'movie-shore-v26'
reference=Image.open('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103/reference-opening-50525.jpg').convert('RGB')
render=Image.open(O/'movie-front-v26.png').convert('RGB')
patches={'left shaded wall':[490,325,625,365],'right lit wall':[1990,300,2280,337],'left lower rust pipe':[580,758,665,784],'right lower rust pipe':[2010,768,2110,785],'right bank slab':[1950,870,2170,893]}
def sample(im,box):
    rgb=np.asarray(im.crop(box),dtype=float).reshape(-1,3)/255
    med=np.median(rgb,axis=0);linear=np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4)
    return {'medianSrgb255':np.round(med*255,2).tolist(),'medianLinearLuminance':float(np.median(linear@[.2126,.7152,.0722]))}
rows=[]
for name,box in patches.items():
    scaled=[round(v*render.size[i%2]/reference.size[i%2])for i,v in enumerate(box)];ref=sample(reference,box);current=sample(render,scaled)
    rows.append({'patch':name,'referenceBox':box,'renderBox':scaled,'reference':ref,'render':current,'renderOverReferenceLuminance':current['medianLinearLuminance']/ref['medianLinearLuminance']})
result={'purpose':'Broad matched patch appearance diagnosis; not a full fidelity score and not an albedo estimate.','revision':26,'patches':rows,'interpretationLimit':'Manual rectangles can contain different stains, shadows and detailed geometry. Inspect images before changing lighting or materials.'}
(O/'appearance-patches-v26.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(rows,indent=2))
