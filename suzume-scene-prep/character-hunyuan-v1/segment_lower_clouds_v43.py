"""Observed lower-cloud bands with explicitly inferred foreground occlusions."""
from pathlib import Path
import numpy as np,cv2,json
from PIL import Image
from scipy.ndimage import gaussian_filter,distance_transform_edt
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).parent;O=R/'poster-lower-clouds-v43';O.mkdir(exist_ok=True)
V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
rgb=np.array(Image.open(V/'reference-hires.jpg').resize((1416,2000),Image.Resampling.LANCZOS))/255
official=np.array(Image.open(V/'reference-official.jpg').resize((1416,2000),Image.Resampling.BICUBIC))/255
# These lower envelopes lie behind the actual foreground silhouette. The door
# is separately excluded, so its white paint can never become cloud pigment.
skyline=np.array([[0,508],[40,510],[55,501],[103,506],[123,521],[154,517],[173,515],[193,512],[241,520],[268,580],[293,586],[294,600],[310,603],[405,606],[430,599],[446,581],[453,566],[482,563],[507,560],[546,560],[581,548],[588,541],[618,545],[622,557],[650,562],[680,556],[708,551]],float)
Y,X=np.mgrid[:2000,:1416];u=X/2;v=Y/2
visible=v<np.interp(u,skyline[:,0],skyline[:,1])-2
door=np.array([[309,562],[339,562],[346,556],[358,559],[365,554],[373,558],[389,559],[401,565],[405,616],[309,616]],float)
foreground=np.zeros((2000,1416),np.uint8);cv2.fillPoly(foreground,[np.rint(door*2).astype(np.int32)],1)
steel=[([[14,490],[0,532]],9),([[177,470],[168,565]],9),([[260,482],[266,600]],9),([[507,470],[522,610]],11),([[652,470],[674,608]],11),([[0,514],[270,538]],7),([[465,535],[708,505]],7),([[433,577],[510,585],[708,559]],8)]
for points,width in steel:cv2.polylines(foreground,[np.rint(np.array(points)*2).astype(np.int32)],False,1,int(width*2))
visible &= foreground==0
# Three observed strata, continued through occluded spans. Their envelopes
# follow different observed ridges; none is a rectangular image-facing sheet.
bands=[
 {'name':'Lower grey-blue stratus bank v43','depth':282.,'upper':[[0,538],[90,541],[180,541],[255,543],[280,542],[299,545],[319,551],[336,549],[355,548],[373,552],[395,550],[420,545],[444,543],[472,546],[500,541],[531,548],[554,546],[577,543],[601,544],[635,547],[660,545],[683,549],[708,547]],'lower':[[0,561],[100,562],[200,562],[270,561],[294,562],[318,563],[342,566],[368,567],[390,564],[413,565],[440,560],[472,556],[500,557],[529,561],[555,562],[584,558],[611,558],[640,562],[670,560],[708,559]]},
 {'name':'Lower layered horizon cloud v43','depth':312.,'upper':[[0,566],[120,566],[240,565],[269,563],[289,563],[308,565],[329,568],[355,568],[379,567],[402,570],[420,569],[436,565],[452,562],[474,560],[502,562],[538,563],[574,565],[620,564],[666,565],[708,563]],'lower':[[0,593],[120,593],[240,592],[270,590],[292,589],[313,584],[339,585],[367,587],[395,585],[416,582],[437,579],[456,579],[480,578],[513,582],[550,584],[590,587],[630,586],[668,586],[708,588]]},
 {'name':'Distant low horizon billows v43','depth':345.,'upper':[[0,592],[100,592],[220,592],[270,590],[288,588],[306,590],[329,588],[358,589],[384,587],[405,588],[421,587],[440,587],[461,585],[480,583],[510,586],[550,586],[610,588],[660,588],[708,588]],'lower':[[0,625],[110,625],[220,625],[280,625],[310,624],[350,626],[400,625],[440,622],[480,624],[525,625],[580,624],[640,625],[708,626]]}
]
arrays={'visible':visible.astype('u1'),'foreground':foreground,'skyline':skyline};records=[]
fig,axes=plt.subplots(4,1,figsize=(18,11),constrained_layout=True)
axes[0].imshow(rgb[1040:1240],extent=[0,708,620,520],aspect='auto');axes[0].set_title('Reference lower sky; traced cloud envelopes')
for i,band in enumerate(bands):
    upper=np.interp(u,np.array(band['upper'])[:,0],np.array(band['upper'])[:,1]);lower=np.interp(u,np.array(band['lower'])[:,0],np.array(band['lower'])[:,1])
    envelope=(v>=upper)&(v<=lower)
    # Clouds may be darker than clear sky. Keep blue-grey values without the
    # brightness threshold that discarded the shadow layers in the old mask.
    valid=visible&envelope&(rgb[:,:,0]<rgb[:,:,1]+.015)&(rgb[:,:,1]<rgb[:,:,2]+.035)
    valid &= (v>530)&(v<609)
    # The bright high-resolution source and official color grade differ in
    # facade shadows. Require sky chroma in both to reject blue-grey masonry
    # whose official pigment is actually foliage green.
    valid &= (official[:,:,0]<official[:,:,1]+.005)&(official[:,:,1]<official[:,:,2]-.015)
    assert valid.sum()>700,(i,valid.sum())
    _,nearest=distance_transform_edt(~valid,return_indices=True)
    pigments=np.clip(official+.30*(rgb-gaussian_filter(rgb,(2.8,2.8,0))),0,1)
    seed=np.rint(pigments[nearest[0],nearest[1]]*255).astype('u1')
    # Continuous interpolation is restricted to the inferred parts of each band.
    fill=(envelope&~valid).astype('u1')*255
    color=cv2.inpaint(seed,fill,7,cv2.INPAINT_NS).astype(float)/255
    confidence=np.clip(distance_transform_edt(valid)/3,0,1)
    small_mask=cv2.resize(envelope.astype('u1'),(708,1000),interpolation=cv2.INTER_NEAREST)
    arrays['mask'+str(i)]=small_mask;arrays['rgb'+str(i)]=color.astype('f4');arrays['confidence'+str(i)]=confidence.astype('f4')
    records.append({**band,'index':i,'observedPigmentPixelsAt1416':int(valid.sum()),'occludedAndBackDepthInferred':True})
    a=axes[i+1];overlay=rgb.copy();overlay[envelope]=.4*overlay[envelope]+.6*np.array([[1,.3,.2],[.2,1,.3],[.3,.4,1]][i]);a.imshow(overlay[1040:1240],extent=[0,708,620,520],aspect='auto');a.set_title(band['name'])
    axes[0].plot(np.array(band['upper'])[:,0],np.array(band['upper'])[:,1],lw=1)
for a in axes:a.set_xticks(range(0,709,50));a.set_yticks(range(520,621,20));a.set_ylim(620,520);a.grid(alpha=.18)
fig.savefig(O/'lower-band-segmentation-v43.png',dpi=130);plt.close(fig)
np.savez_compressed(O/'lower-bands-v43.npz',**arrays)
(O/'lower-bands-v43.json').write_text(json.dumps({'revision':43,'bands':records,'scope':'Manually traced three lower cloud strata, including visible dark cloud pixels excluded by the earlier brightness filter. Continuation behind foreground is inferred; surfaces have closed geometric thickness in the subsequent build.','oneToOneComplete':False},indent=2),encoding='utf-8')
print('LOWER_BANDS_SEGMENTED',[(q['name'],q['observedPigmentPixelsAt1416']) for q in records])
