from pathlib import Path
import json,base64,zlib,struct,cv2,numpy as np
R=Path(__file__).parent;O=R/'poster-clouds-v41';V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
new=json.loads((O/'cloud-geometry-v41.json').read_text());old=json.loads((V/'distant-cloud-volumes-v9.json').read_text());mask=cv2.imdecode(np.frombuffer((O/'source-mask-v41.png').read_bytes(),dtype=np.uint8),0);count,labels,stats,_=cv2.connectedComponentsWithStats((mask>0).astype('u1'),8)
cam=json.loads((R/'poster-v38/restoration-v38.json').read_text())['posterCamera'];M=np.array(cam['matrixWorld']);C=M[:3,3];f=cam['lens']/cam['sensorHeight']*1000
data=np.load(O/'cloud-geometry-v41.npz');scale=4
def raster(world,faces):
    d=(world-C)@M[:3,:3];uv=np.c_[354+f*d[:,0]/(-d[:,2]),500-f*d[:,1]/(-d[:,2])];out=np.zeros((1000*scale,708*scale),np.uint8)
    for tri in np.rint(uv[faces]*scale+(scale-1)/2).astype(np.int32):cv2.fillConvexPoly(out,tri,1)
    return out>0
rows=[]
for rec in new['clouds']:
    q=old[rec['index']];raw=zlib.decompress(base64.b64decode(q['data']));nv,nf=struct.unpack_from('<II',raw);v=np.frombuffer(raw,dtype='<i2',count=nv*3,offset=8).reshape(-1,3)/4096;faces=np.frombuffer(raw,dtype='<u2',count=nf*3,offset=8+nv*6).reshape(-1,3);world=(v*np.array(q['scale'])+np.array(q['center']))[:,[0,2,1]]*[1,-1,1]
    rendered=raster(world,faces);ids=[i for i in range(1,count) if stats[i,:4].tolist()==rec['sourceBounds708']];assert len(ids)==1;target=np.zeros((1000,708),bool);target[:labels.shape[0]]=labels==ids[0];area=int(target.sum());target=np.repeat(np.repeat(target,scale,0),scale,1);iou=np.count_nonzero(rendered&target)/np.count_nonzero(rendered|target)
    candidate=raster(data[rec['key']+'_world'],data[rec['key']+'_faces']);new_iou=np.count_nonzero(candidate&target)/np.count_nonzero(candidate|target)
    rows.append({'cloud':rec['index'],'sourceAreaPixels':area,'oldTriangles':nf,'newTriangles':rec['triangles'],'oldSilhouetteIoU':float(iou),'newSilhouetteIoU':float(new_iou)})
weights=np.array([q['sourceAreaPixels'] for q in rows],float);weights/=weights.sum();report={'revision':41,'scope':'Rasterized silhouettes of 28 closed lower clouds, sampled at four times the 708x1000 mask resolution with pixel-center alignment, versus the inherited v9 segmented and inpainted mask. Includes uncertain occluded contours; not a comparison against unmodified full-scene pixels.','weightedOldIoU':float(np.dot(weights,[q['oldSilhouetteIoU'] for q in rows])),'weightedNewIoU':float(np.dot(weights,[q['newSilhouetteIoU'] for q in rows])),'checks':rows,'oneToOneComplete':False}
(O/'silhouette-comparison-v41.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({k:report[k] for k in ['weightedOldIoU','weightedNewIoU']},indent=2))
