from pathlib import Path
import json,numpy as np
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.ndimage import map_coordinates,gaussian_filter1d
from scipy.signal import find_peaks
R=Path(__file__).parent;O=R/'poster-railings-v46';V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
ref=Image.open(V/'reference-hires.jpg').convert('RGB').resize((2124,3000)).crop((0,495*3,300*3,585*3));before=Image.open(R/'poster-rooftops-v45/rooftop-detail-v45.png').convert('RGB');after=Image.open(O/'railing-detail-v46.png').convert('RGB')
fig,axs=plt.subplots(3,1,figsize=(15,9),dpi=150)
for ax,im,title in zip(axs,[ref,before,after],['High-resolution reference','Before: v45 rails and ivy','After: v46 rails and ivy']):
    ax.imshow(im,extent=(0,300,585,495));ax.set_xlim(0,280);ax.set_ylim(573,530);ax.set_title(title);ax.set_yticks(np.arange(530,574,5));ax.grid(alpha=.17)
fig.tight_layout();fig.savefig(O/'railing-comparison-v46.png');plt.close(fig)
geo=json.loads((O/'railing-geometry-v46.json').read_text());targets=geo['topReference'];us=np.array([q['u'] for q in targets]);vs=np.array([q['v'] for q in targets]);xs=np.linspace(52,104,1041);upper=np.interp(xs,us,vs);measures=[]
for label,im in [('reference',ref),('reconstruction',after)]:
    a=np.asarray(im).mean(2)/255;samples=[]
    for t in np.linspace(.25,.78,12):samples.append(map_coordinates(a,[(upper+10*t-495)*3,xs*3],order=1))
    sig=np.mean(samples,axis=0);detail=sig-gaussian_filter1d(sig,12);peaks,_=find_peaks(detail,distance=17,prominence=.008);dist=np.diff(xs[peaks]);dist=dist[(dist>1)&(dist<2.3)];measures.append({'label':label,'detectedPeaks':xs[peaks].tolist(),'medianSpacingPixels':float(np.median(dist)) if len(dist) else None})
(O/'railing-comparison-v46.json').write_text(json.dumps({'revision':46,'scope':'Local bar density in an exposed 52..104 pixel interval at 708x1000. Peak estimates are sensitive to paint, lighting and source resolution; they do not establish whole-scene fidelity.','measurements':measures,'oneToOneComplete':False},indent=2));print(json.dumps(measures,indent=2))
