from pathlib import Path
import sys,json,numpy as np
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).parent;O=R/'poster-horizon-v42';V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
reference=np.asarray(Image.open(V/'reference-official.jpg').convert('RGB').resize((708,1000),Image.Resampling.LANCZOS),float)/255;old=np.asarray(Image.open(R/'poster-clouds-v41/poster-front-v41.png').convert('RGB'),float)/255
trial='--trial' in sys.argv;name='horizon-trial-v42.png' if trial else 'poster-front-v42.png';candidate=np.asarray(Image.open(O/name).convert('RGB'),float)/255
if trial:
    assert candidate.shape[:2]==(180,708);new=np.zeros_like(old);new[480:660]=candidate
else:new=candidate
roi=np.s_[535:559,297:411];report={'revision':42,'image':name,'probeIn708Frame':{'x':[297,411],'y':[535,559]},'beforeRGBMeanAbsoluteError255':float(np.abs(old[roi]-reference[roi]).mean()*255),'afterRGBMeanAbsoluteError255':float(np.abs(new[roi]-reference[roi]).mean()*255),'referenceMeanRGB255':(reference[roi].mean((0,1))*255).tolist(),'beforeMeanRGB255':(old[roi].mean((0,1))*255).tolist(),'afterMeanRGB255':(new[roi].mean((0,1))*255).tolist(),'scope':'Only the fixed unobscured sky rectangle above the door; includes both cloud and surrounding sky. Does not measure full-scene likeness or inferred depth.','oneToOneComplete':False}
(O/('trial-color-v42.json' if trial else 'color-comparison-v42.json')).write_text(json.dumps(report,indent=2),encoding='utf-8')
fig,axes=plt.subplots(3,1,figsize=(13,7));
for ax,im,title in zip(axes,[reference,old,new],['Official reference','Before: central cloud bank missing','After: restored continuous bank']):
    ax.imshow(im);ax.set_xlim(235,530);ax.set_ylim(578,510);ax.set_title(title);ax.grid(alpha=.15)
fig.tight_layout();fig.savefig(O/('horizon-trial-comparison-v42.png' if trial else 'horizon-comparison-v42.png'),dpi=130);print(json.dumps(report,indent=2))
