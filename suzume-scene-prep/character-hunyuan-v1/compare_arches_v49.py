from pathlib import Path
from PIL import Image,ImageDraw
import json,numpy as np
R=Path(__file__).parent;O=R/'poster-arches-v49';D=json.loads((O/'arch-geometry-v49.json').read_text());C=np.array(D['camera']['position']);rot=np.array(D['camera']['rotation']);f=D['camera']['focalPixels']
reference=Image.open(O/'reference-arches-v49.png').convert('RGB');before=Image.open(O/'current-arches-v49.png').convert('RGB');after=Image.open(O/'arch-detail-v49.png').convert('RGB').crop((0,18,840,150));canvas=Image.new('RGB',(840,474),(20,26,29));draw=ImageDraw.Draw(canvas)
for i,(im,label) in enumerate(zip([reference,before,after],['Reference','Before v48','After v49'])):draw.text((8,i*158+5),label,fill='white');canvas.paste(im,(0,i*158+26))
canvas.save(O/'arch-comparison-v49.png');rows=[]
for rec in D['arches']:
 member=next(q for q in D['members'] if q['kind']=='surround' and q['archId']==rec['id']);v=np.array(member['verticesNative']);ring=v[:len(v)//6];apex=ring[ring[:,2].argmax()];bottom=(ring[0]+ring[-1])/2;p=np.array([apex,bottom]);q=(p-C)@rot;uv=np.c_[354+f*q[:,0]/-q[:,2],500-f*q[:,1]/-q[:,2]];u,half,top,base=rec['reference'];want=np.array([[u,top],[u,base]]);error=np.linalg.norm(uv-want,axis=1);rows.append({'arch':rec['id'],'referenceEvidence':rec['evidence'],'referenceAnchors':want.tolist(),'nativeOuterContourAnchors':uv.tolist(),'pixelError':error.tolist()})
observed=[q for q in rows if q['referenceEvidence']=='observed'];maximum=max(max(q['pixelError']) for q in observed);assert maximum<1.5
report={'revision':49,'nativeSha256':json.loads((O/'verification-v49.json').read_text())['nativeSha256'],'scope':'Apex and baseline centers on newly modeled contours at 708x1000. Local anchor agreement does not validate shading, the complete arch curve, hidden geometry, or whole-scene fidelity.','referenceMeasurementUncertaintyPixels':1.5,'maximumObservedAnchorErrorPixels':maximum,'observedAnchorCount':len(observed)*2,'anchors':rows,'oneToOneComplete':False};(O/'arch-projection-comparison-v49.json').write_text(json.dumps(report,indent=2));print('ARCHES_49_OBSERVED_ANCHORS',len(observed)*2,maximum)
