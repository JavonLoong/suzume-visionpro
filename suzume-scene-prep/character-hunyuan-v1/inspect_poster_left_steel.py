from pathlib import Path
import numpy as np
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).parent;O=R/'poster-lower-clouds-v43';V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
ref=np.array(Image.open(V/'reference-hires.jpg').resize((1416,2000),Image.Resampling.LANCZOS))
before=np.array(Image.open(R/'poster-horizon-v42/poster-front-v42.png').resize((1416,2000)))
fig,axes=plt.subplots(1,2,figsize=(11,12),constrained_layout=True)
for ax,img,title in zip(axes,[ref,before],['Reference: left steel and facade','Existing steel before the next revision']):
    ax.imshow(img[680:1460,:590],extent=[0,295,730,340],aspect='equal');ax.set_title(title);ax.set_xticks(range(0,296,25));ax.set_yticks(range(350,731,25));ax.grid(alpha=.3)
fig.savefig(O/'left-steel-next-diagnosis.png',dpi=145);plt.close(fig)
