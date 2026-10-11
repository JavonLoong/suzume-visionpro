"""Compare unobscured reference patches; the source image is only read."""
from pathlib import Path
from PIL import Image
import numpy as np,json
R=Path(__file__).parent;O=R/'poster-v38'
V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
images={key:np.asarray(Image.open(path).convert('RGB'),dtype=float) for key,path in {
    'reference':V/'reference-official.jpg',
    'previousPosterNative':V/'native-poster-v12.png',
    'movieEnvironmentAtPosterCamera':O/'poster-current-before-v38.png',
    'posterV38':O/'poster-front-final-v38.png'}.items()}
patches={
    'clear sky upper center':[147,15,168,30],
    'clear sky middle left':[116,92,137,112],
    'clear sky center gap':[128,136,147,151],
    'cloud upper left shade':[16,12,33,28],
    'cloud left highlight':[24,104,39,116],
    'cloud left underside':[19,122,38,136],
    'cloud right highlight':[280,66,296,82],
    'cloud right underside':[309,107,330,119],
}
rows=[]
for name,box in patches.items():
    colors={}
    for key,im in images.items():
        x0,y0,x1,y1=np.rint(np.array(box)*([im.shape[1]/354,im.shape[0]/500]*2)).astype(int)
        colors[key]=np.median(im[y0:y1,x0:x1].reshape(-1,3),axis=0)
    rows.append({'name':name,'referenceBox354x500':box,'medianRGB255':{k:v.tolist() for k,v in colors.items()},'meanAbsoluteChannelError255':{k:float(np.mean(abs(v-colors['reference']))) for k,v in colors.items() if k!='reference'}})
report={'revision':38,'reference':'reference-official.jpg','sourceImageUnmodified':True,'patches':rows,'meanPatchColorError255':{key:float(np.mean([q['meanAbsoluteChannelError255'][key] for q in rows])) for key in list(images)[1:]},'scope':'Eight fixed unobscured sky/cloud color patches. Does not measure architecture, cloud outlines, water, 3D depth or full-scene similarity.','oneToOneComplete':False}
(O/'color-comparison-v38.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report['meanPatchColorError255'],indent=2))
