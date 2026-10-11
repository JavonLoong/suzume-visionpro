from pathlib import Path
import json,numpy as np,sys
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).parent;O=R/'poster-clouds-v41';O.mkdir(exist_ok=True);V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
source=R/'poster-water-v40/poster-front-v40.png'
if '--candidate' in sys.argv:source=O/sys.argv[sys.argv.index('--candidate')+1]
reference=Image.open(V/'reference-official.jpg').convert('RGB').resize((708,1000),Image.Resampling.LANCZOS);render=Image.open(source).convert('RGB').resize((708,1000),Image.Resampling.LANCZOS)
fig,axes=plt.subplots(2,1,figsize=(13,9))
for ax,im,title in zip(axes,[reference,render],['Official poster: lower cloud field','Native lower cloud field: '+source.stem]):
    ax.imshow(im);ax.set_xlim(0,708);ax.set_ylim(580,330);ax.set_title(title);ax.grid(alpha=.15)
fig.tight_layout();fig.savefig(O/(source.stem+'-cloud-comparison.png'),dpi=130)
print('CLOUD_COMPARISON',source.stem)
