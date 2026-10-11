"""Compare selected mist patches after the final full render."""
from pathlib import Path
from PIL import Image
import numpy as np,json
R=Path(__file__).parent;O=R/'movie-terrain-v31';boxes={'leftLowMist':[980,650,1055,690],'rightLowMist':[1330,648,1405,686]};files={'reference':R/'movie-surfaces-v28/reference-opening.jpg','v30':R/'movie-night-v30/movie-front-v30.png','v31':O/'movie-front-v31.png'};rows={}
for name,box in boxes.items():
    rows[name]={}
    for label,path in files.items():
        im=np.asarray(Image.open(path).convert('RGB'));h,w=im.shape[:2];x0,y0,x1,y1=[round(v*(w/2552 if i%2==0 else h/1656)) for i,v in enumerate(box)];patch=im[y0:y1,x0:x1].reshape(-1,3);rows[name][label]={'medianRGB':np.median(patch,axis=0).tolist(),'meanRGB':np.mean(patch,axis=0).round(2).tolist()}
out={'revision':31,'patchBoxes':boxes,'patches':rows,'scope':'Two manually chosen mist regions in the reference view. Finite render resolution, visibility and plant placement affect their statistics. Not an overall or all-angle similarity metric.','oneToOneComplete':False};(O/'mist-appearance-v31.json').write_text(json.dumps(out,indent=2),encoding='utf-8');print(json.dumps(rows,indent=2))
