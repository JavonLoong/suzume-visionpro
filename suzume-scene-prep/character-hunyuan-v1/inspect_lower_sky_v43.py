from pathlib import Path
import json,numpy as np,cv2
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).parent;O=R/'poster-lower-clouds-v43';O.mkdir(exist_ok=True)
V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
hi=np.array(Image.open(V/'reference-hires.jpg').resize((1416,2000),Image.Resampling.LANCZOS))
old=np.array(Image.open(R/'poster-horizon-v42/poster-front-v42.png').resize((1416,2000)))
source=np.array(Image.open(V/'cloud-segmentation.png').resize((1416,1184),Image.Resampling.NEAREST))
fig,ax=plt.subplots(3,1,figsize=(18,10),constrained_layout=True)
for a,img,title in zip(ax,[hi,old,source],['Reference high-resolution geometry source','Current native v42','Inherited cloud segmentation']):
    a.imshow(img[940:1220],extent=[0,708,610,470],aspect='auto',cmap='gray' if img.ndim==2 else None);a.set_xlim(0,708);a.set_ylim(610,470);a.set_xticks(range(0,709,25));a.set_yticks(range(470,611,20));a.grid(alpha=.2);a.set_title(title)
fig.savefig(O/'lower-sky-inspection-v43.png',dpi=130);plt.close(fig)
print('LOWER_SKY_INSPECTION_READY')
