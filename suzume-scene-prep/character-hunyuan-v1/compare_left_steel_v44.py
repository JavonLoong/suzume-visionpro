from pathlib import Path
from PIL import Image
import numpy as np,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).parent;O=R/'poster-left-steel-v44';V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
ref=np.array(Image.open(V/'reference-hires.jpg').resize((1416,2000),Image.Resampling.LANCZOS));trial=np.array(Image.open(O/'left-steel-trial-v44.png'))
fig,axes=plt.subplots(1,2,figsize=(10,8),constrained_layout=True)
axes[0].imshow(ref[700:920,:160]);axes[1].imshow(trial[20:240,:160]);axes[0].set_title('Reference: split upper section');axes[1].set_title('Current trial: outer section');
for ax in axes:ax.axis('off')
fig.savefig(O/'outer-section-trial-comparison.png',dpi=130);plt.close(fig)
official=np.array(Image.open(V/'reference-official.jpg').resize((1416,2000),Image.Resampling.LANCZOS))
before=np.array(Image.open(R/'poster-lower-clouds-v43/poster-front-v43.png').resize((1416,2000),Image.Resampling.LANCZOS))
fig,axes=plt.subplots(1,3,figsize=(15,11),constrained_layout=True)
for ax,img,title in zip(axes,[official[680:1450,:600],before[680:1450,:600],trial],['Official reference','Before: v43','After: v44 left steel']):
    ax.imshow(img,extent=[0,300,725,340],aspect='equal');ax.set_title(title);ax.set_xticks(range(0,301,50));ax.set_yticks(range(350,726,50));ax.grid(alpha=.12)
fig.savefig(O/'left-steel-comparison-v44.png',dpi=140);plt.close(fig)
