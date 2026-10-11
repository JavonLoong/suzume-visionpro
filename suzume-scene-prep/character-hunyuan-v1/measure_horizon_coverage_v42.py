from pathlib import Path
import json,cv2,numpy as np
from PIL import Image
R=Path(__file__).parent;O=R/'poster-horizon-v42';V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
cam=json.loads((R/'poster-v38/restoration-v38.json').read_text())['posterCamera'];M=np.array(cam['matrixWorld']);C=M[:3,3];f=cam['lens']/cam['sensorHeight']*1000;scale=4
def project(v):
    d=(v-C)@M[:3,:3];return np.c_[354+f*d[:,0]/(-d[:,2]),500-f*d[:,1]/(-d[:,2])]
def raster(v,faces):
    p=project(v);image=np.zeros((1000*scale,708*scale),np.uint8)
    for tri in np.rint(p[faces]*scale+(scale-1)/2).astype(np.int32):cv2.fillConvexPoly(image,tri,1)
    return image>0
old=np.load(R/'poster-clouds-v41/cloud-geometry-v41.npz');current=np.load(O/'horizon-geometry-v42.npz');before=np.zeros((1000*scale,708*scale),bool)
for index in [1,3]:before|=raster(old['cloud'+str(index)+'_world'],old['cloud'+str(index)+'_faces'])
after=raster(current['world'],current['faces']);raw=np.asarray(Image.open(V/'cloud-segmentation.png').convert('L'));raw=cv2.resize(raw,(708,round(raw.shape[0]*708/2000)),interpolation=cv2.INTER_AREA)>150
roi=np.s_[535*scale:559*scale,297*scale:411*scale];target=np.repeat(np.repeat(raw[535:559,297:411],scale,0),scale,1);rows={}
for name,mask in [('before',before[roi]),('after',after[roi])]:rows[name]={'sourceCloudRecall':float(np.count_nonzero(mask&target)/np.count_nonzero(target)),'sourceCloudIoU':float(np.count_nonzero(mask&target)/np.count_nonzero(mask|target)),'probeFractionCovered':float(mask.mean())}
report={'revision':42,'sourceProbeIn708Frame':{'x':[297,411],'y':[535,559]},'rawSourceCloudPixels':int(raw[535:559,297:411].sum()),'samplingScale':scale,**rows,'scope':'Only the unobscured sky probe above the door, against the original segmentation before the erroneous cap. This tests recovered geometry coverage, not cloud color, unobserved depth or whole-scene equivalence.','oneToOneComplete':False};(O/'coverage-v42.json').write_text(json.dumps(report,indent=2),encoding='utf-8');assert rows['after']['sourceCloudRecall']>rows['before']['sourceCloudRecall']+.8;print(json.dumps(report,indent=2))
