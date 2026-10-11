from pathlib import Path
import json,cv2,numpy as np
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).parent;O=R/'poster-clouds-v41';V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
reference=np.asarray(Image.open(V/'reference-official.jpg').convert('RGB').resize((708,1000),Image.Resampling.LANCZOS))
raw=np.asarray(Image.open(V/'cloud-segmentation.png').convert('L'));source=cv2.resize(raw,(708,round(raw.shape[0]*708/2000)),interpolation=cv2.INTER_AREA)>150;used=np.asarray(Image.open(O/'source-mask-v41.png').convert('L'))>0
loss=source&(~used);region=np.zeros_like(loss);region[532:592,297:411]=1;loss &=region
fig,axes=plt.subplots(1,3,figsize=(14,5));axes[0].imshow(reference);axes[0].set_title('Official reference');axes[1].imshow(source,cmap='gray');axes[1].set_title('Original cloud mask');axes[2].imshow(used,cmap='gray');axes[2].imshow(np.ma.masked_where(~loss,loss),cmap='autumn',vmin=0,vmax=1,alpha=.75);axes[2].set_title('Used mask: removed pixels in yellow')
for ax in axes:ax.set_xlim(260,450);ax.set_ylim(600,510);ax.axhline(531.54,color='red',alpha=.5,linestyle='--');ax.grid(alpha=.15)
fig.tight_layout();fig.savefig(O/'central-cloud-cap-diagnosis-v41.png',dpi=130)
path=O/'missing-central-cloud-diagnosis-v41.json';d=json.loads(path.read_text());d['pureSkyProbeAboveDoorIn708Frame']={'x':[297,411],'y':[535,559],'rawCloudMaskPixels':int(source[535:559,297:411].sum()),'usedCloudMaskPixels':int(used[535:559,297:411].sum())};d['diagnosticFigure']='central-cloud-cap-diagnosis-v41.png';path.write_text(json.dumps(d,indent=2),encoding='utf-8');print(d['pureSkyProbeAboveDoorIn708Frame'])
