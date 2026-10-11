from pathlib import Path
import sys,json,numpy as np,cv2
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).parent;O=R/'poster-lower-clouds-v43';V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
ref=np.array(Image.open(V/'reference-official.jpg').resize((708,1000),Image.Resampling.LANCZOS)).astype(float)
before=np.array(Image.open(R/'poster-horizon-v42/poster-front-v42.png').convert('RGB')).astype(float)
trial='--trial' in sys.argv
if trial:
    after=before.copy();crop=np.array(Image.open(O/'lower-sky-trial-v43.png').convert('RGB'));assert crop.shape==(140,708,3),crop.shape;after[500:640]=crop
else:after=np.array(Image.open(O/'poster-front-v43.png').convert('RGB')).astype(float)
mask=cv2.resize(np.load(O/'lower-bands-v43.npz')['visible'],(708,1000),interpolation=cv2.INTER_NEAREST).astype(bool);yy,xx=np.mgrid[:1000,:708];mask&=(yy>=540)&(yy<610)&(xx>=270)
result={'revision':43,'trial':trial,'sourceVisibleSkyPixels':int(mask.sum()),'maskScope':'All manually visible sky pixels in x270:708, y540:610 at 708 by 1000, excluding the door, foliage, steel and rooftop silhouette. Color agreement only; not a whole-scene or hidden-depth metric.','beforeRGBMeanAbsoluteError255':float(np.mean(abs(before[mask]-ref[mask]))),'afterRGBMeanAbsoluteError255':float(np.mean(abs(after[mask]-ref[mask]))),'referenceMeanRGB255':ref[mask].mean(0).tolist(),'beforeMeanRGB255':before[mask].mean(0).tolist(),'afterMeanRGB255':after[mask].mean(0).tolist(),'oneToOneComplete':False}
prefix='trial' if trial else 'final';(O/(prefix+'-comparison-v43.json')).write_text(json.dumps(result,indent=2),encoding='utf-8')
fig,axes=plt.subplots(3,1,figsize=(17,9),constrained_layout=True)
for ax,img,title in zip(axes,[ref,before,after],['Official reference','Before: v42','After: three solid lower cloud banks']):
    ax.imshow(img[510:620,235:708].astype('u1'),extent=[235,708,620,510],aspect='auto');ax.set_title(title);ax.set_xticks(range(250,709,50));ax.set_yticks(range(520,621,20))
fig.savefig(O/(prefix+'-comparison-v43.png'),dpi=130);plt.close(fig);print(json.dumps(result,indent=2))
