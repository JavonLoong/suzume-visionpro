from pathlib import Path
import json,numpy as np
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).parent;O=R/'poster-rooftops-v45';V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
ref=Image.open(V/'reference-official.jpg').convert('RGB').resize((2124,3000));hi=Image.open(V/'reference-hires.jpg').convert('RGB').resize((2124,3000));before=Image.open(R/'poster-left-steel-v44/poster-front-v44.png').convert('RGB').resize((2124,3000));after=Image.open(O/'rooftop-detail-v45.png').convert('RGB')
box=(0,495*3,300*3,585*3);images=[hi.crop(box),ref.crop(box),before.crop(box),after]
fig,axs=plt.subplots(4,1,figsize=(15,12),dpi=150)
for ax,im,title in zip(axs,images,['High-resolution reference: shape','Official reference: color','Before: v44','After: v45 roof equipment']):
    ax.imshow(im,extent=(0,300,585,495));ax.set_title(title);ax.set_yticks([500,520,540,560,580]);ax.grid(alpha=.15)
fig.tight_layout();fig.savefig(O/'rooftop-comparison-v45.png');plt.close(fig)
# A small fully visible casing patch avoids steel, ladder and trim.
# This is explicitly a local color check, not whole-scene image similarity.
patch=[84,530,98,538];u0,y0,u1,y1=patch
r=np.asarray(ref)[y0*3:y1*3,u0*3:u1*3].astype(float);b=np.asarray(before)[y0*3:y1*3,u0*3:u1*3].astype(float);a=np.asarray(after)[(y0-495)*3:(y1-495)*3,u0*3:u1*3].astype(float)
metric={'revision':45,'scope':'Fixed exposed left equipment casing patch, excluding beams, ladder and seams. Before reconstruction much of this reference casing region was wrongly empty sky, so this error reduction combines restored geometry and color. It is not a whole-scene fidelity measure.','patch708x1000':patch,'officialRGBMean255':r.mean((0,1)).tolist(),'beforeRGBMean255':b.mean((0,1)).tolist(),'afterRGBMean255':a.mean((0,1)).tolist(),'beforeRGBMeanAbsoluteError255':float(np.abs(b-r).mean()),'afterRGBMeanAbsoluteError255':float(np.abs(a-r).mean()),'oneToOneComplete':False}
metric['otherExposedCasingPatches']=[]
for label,(u0,y0,u1,y1) in [('right house',(220,540,234,546)),('central tank',(150,534,160,541)),('partial tank',(10,524,16,529))]:
    rr=np.asarray(ref)[y0*3:y1*3,u0*3:u1*3].astype(float);aa=np.asarray(after)[(y0-495)*3:(y1-495)*3,u0*3:u1*3].astype(float)
    metric['otherExposedCasingPatches'].append({'label':label,'patch708x1000':[u0,y0,u1,y1],'referenceMean':rr.mean((0,1)).tolist(),'reconstructionMean':aa.mean((0,1)).tolist(),'RGBMeanAbsoluteError255':float(np.abs(aa-rr).mean())})
(O/'rooftop-comparison-v45.json').write_text(json.dumps(metric,indent=2));print(json.dumps(metric,indent=2))
