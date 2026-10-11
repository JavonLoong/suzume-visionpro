from pathlib import Path
import numpy as np,json,sys
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).parent;O=R/'poster-water-v40';O.mkdir(exist_ok=True);V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
reference=np.asarray(Image.open(V/'reference-official.jpg').convert('RGB'),float)/255
source=R/'poster-steel-v39/poster-front-v39.png'
if '--candidate' in sys.argv:source=O/sys.argv[sys.argv.index('--candidate')+1]
render=np.asarray(Image.open(source).convert('RGB').resize((354,500),Image.Resampling.LANCZOS),float)/255
bands=[(354,374),(375,398),(399,426),(427,452),(453,468)];rows=[]
for y0,y1 in bands:
    xmask=np.ones(354,bool);xmask[143:215]=False;xmask[:12]=False;xmask[-12:]=False
    rec={'yRange':[y0,y1]}
    for label,im in [('reference',reference),('render',render)]:
        a=im[y0:y1][:,xmask].reshape(-1,3);luma=a@np.array([.2126,.7152,.0722])
        rec[label]={'meanRGB255':(a.mean(0)*255).tolist(),'medianRGB255':(np.median(a,axis=0)*255).tolist(),'lumaQ10Q90':np.percentile(luma,[10,90]).tolist(),'lumaStd':float(luma.std())}
    rec['meanColorError255']=float(np.mean(abs(np.array(rec['reference']['meanRGB255'])-rec['render']['meanRGB255'])));rows.append(rec)
name=source.stem;report={'image':str(source),'reference':'reference-official.jpg','bands':rows,'meanBandColorError255':float(np.mean([q['meanColorError255'] for q in rows])),'scope':'Water bands with door reflection, outer image edges and release text excluded; color and contrast only, not full scene fidelity.'}
(O/(name+'-measurement.json')).write_text(json.dumps(report,indent=2),encoding='utf-8')
fig,axes=plt.subplots(1,2,figsize=(14,6));
for ax,im,title in zip(axes,[reference,render],['Official poster water','Current native water']):
    ax.imshow(im,extent=(0,354,500,0));ax.set_ylim(470,345);ax.set_xlim(0,354);ax.set_title(title);ax.grid(alpha=.15)
fig.tight_layout();fig.savefig(O/(name+'-comparison.png'),dpi=110)
print(json.dumps(report,indent=2))
