from pathlib import Path
import ast,json,cv2,numpy as np
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).parent;O=R/'poster-horizon-v42';O.mkdir(exist_ok=True);V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
tree=ast.parse((V/'build_distant_clouds_v9.py').read_text());prefix=[]
for n in tree.body:
    if isinstance(n,ast.For) and isinstance(n.target,ast.Tuple) and ast.unparse(n.target).startswith('(order,'):break
    if isinstance(n,ast.Assign) and ast.unparse(n.targets[0]).startswith('profile[round(840'):continue
    prefix.append(n)
c={'__file__':str(V/'build_distant_clouds_v9.py')};exec(compile(ast.Module(body=prefix,type_ignores=[]),'uncapped mask inspection','exec'),c)
mask=c['mask'];labels=c['labels'];stats=c['stats'];old=np.asarray(Image.open(R/'poster-clouds-v41/source-mask-v41.png').convert('L'))>0
region=np.zeros_like(mask,bool);region[532:559,297:411]=True;added=(mask>0)&(~old)&region
ids=[int(i) for i in np.unique(labels[added]) if i];existing=json.loads((R/'poster-clouds-v41/cloud-geometry-v41.json').read_text())['clouds'];n,oldlabels,oldstats,_=cv2.connectedComponentsWithStats(old.astype(np.uint8),8);rows=[]
for i in ids:
    layer=labels==i;overlap=[]
    for q in existing:
        matches=[j for j in range(1,n) if oldstats[j,:4].tolist()==q['sourceBounds708']];assert len(matches)==1;inter=int(np.count_nonzero(layer&(oldlabels==matches[0])))
        if inter:overlap.append({'cloudIndex':q['index'],'pixels':inter,'fractionOfOldMask':inter/int(oldstats[matches[0],cv2.CC_STAT_AREA])})
    rows.append({'uncappedComponent':i,'bounds':stats[i,:4].tolist(),'area':int(stats[i,cv2.CC_STAT_AREA]),'restoredProbePixels':int(np.count_nonzero(layer&added)),'overlapsOldClouds':overlap})
np.savez_compressed(O/'uncapped-mask-v42.npz',mask=mask,labels=labels,stats=stats,oldMask=old,probeAdded=added)
report={'sourceNativeSha256':'06d79ae053a89f7671d26f878aab1a81eee2d4269e44c5a043781f66e7afb9aa','maskShape':list(mask.shape),'pureSkyProbeRestoredPixels':int(added.sum()),'affectedComponents':rows,'remainingSourceMaskCautions':'The source mask is cropped at the lower sky and may include foreground door or roof pixels; do not turn its bottom border into a cloud slab.'};(O/'inspection-v42.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
ref=Image.open(V/'reference-official.jpg').resize((708,1000),Image.Resampling.LANCZOS);fig,axes=plt.subplots(3,1,figsize=(13,8));axes[0].imshow(ref);axes[0].set_title('Official reference');axes[1].imshow(old,cmap='gray');axes[1].set_title('Existing cloud mask');axes[2].imshow(mask,cmap='gray');axes[2].imshow(np.ma.masked_where(~added,added),cmap='autumn',alpha=.8,vmin=0,vmax=1);axes[2].set_title('Uncapped cloud mask: restored sky probe')
for ax in axes:ax.set_xlim(180,535);ax.set_ylim(598,505);ax.grid(alpha=.15)
fig.tight_layout();fig.savefig(O/'mask-inspection-v42.png',dpi=130);print(json.dumps(report,indent=2))
