"""Read existing renders to compare local color and foreground stability."""
from pathlib import Path
import json
import numpy as np
from PIL import Image

R = Path(__file__).parent; O = R/'movie-material-v22'; W = R/'movie-windows-v21'
V = Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
old = np.asarray(Image.open(W/'movie-front-v21.png').convert('RGB'), dtype=float)
new = np.asarray(Image.open(O/'movie-front-v22.png').convert('RGB'), dtype=float)
ref = np.asarray(Image.open(V/'reference-opening-50525.jpg').convert('RGB'), dtype=float)
def sample(image, box):
    x0,y0,x1,y1 = box
    return image[y0:y1,x0:x1].reshape(-1,3)
regions = json.loads((W/'facade-color-gap-v21.json').read_text(encoding='utf-8'))['regions']
plaster = []
for r in regions:
    a = np.median(sample(old,r['renderBox']),axis=0)
    b = np.median(sample(new,r['renderBox']),axis=0)
    target = np.array(r['referenceMedian'])
    plaster.append({'region':r['region'],'before':a.tolist(),'after':b.tolist(),'reference':target.tolist(),
        'beforeRgbDistance':float(np.linalg.norm(a-target)),'afterRgbDistance':float(np.linalg.norm(b-target))})
foreground = []
for name,box in {'shirt':(1135,714,1215,791),'skirt':(1130,898,1230,1060),'hair':(1140,546,1200,625)}.items():
    actual_box = (np.array(box)*np.array([720/2552,468/1656,720/2552,468/1656])).astype(int)
    a = np.median(sample(old,actual_box),axis=0)
    b = np.median(sample(new,actual_box),axis=0)
    foreground.append({'region':name,'before':a.tolist(),'after':b.tolist(),'maximumChannelMedianChange':float(np.max(np.abs(b-a)))})
window = []
for name,image,box in [('reference',ref,(1980,465,2210,660)),('v21',old,(559,131,624,187)),('v22',new,(559,131,624,187))]:
    window.append({'variant':name,'rgbQuantiles10_25_50_75_90':np.percentile(sample(image,box),[10,25,50,75,90],axis=0).tolist()})
result = {'revision':22,'scope':'Only three fixed plaster patches, three character patches and a window crop; not a whole-image or one-to-one fidelity score.',
    'plaster':plaster,'foregroundStability':foreground,'windowRegion':window,
    'plasterMeanRgbDistanceBefore':float(np.mean([r['beforeRgbDistance'] for r in plaster])),
    'plasterMeanRgbDistanceAfter':float(np.mean([r['afterRgbDistance'] for r in plaster])),
    'oneToOneComplete':False}
(O/'final-color-comparison-v22.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
