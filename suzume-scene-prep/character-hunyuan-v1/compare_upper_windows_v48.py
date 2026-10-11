from pathlib import Path
from PIL import Image,ImageDraw
import json,numpy as np
R=Path(__file__).parent;O=R/'poster-upper-windows-v48';V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
ref=Image.open(V/'reference-hires.jpg').resize((2124,3000)).convert('RGB').crop((0,555*3,280*3,585*3));before=Image.open(R/'poster-fascia-v47/fascia-detail-v47.png').convert('RGB').crop((0,180,840,270));after=Image.open(O/'upper-window-detail-v48.png').convert('RGB').crop((0,0,840,90));canvas=Image.new('RGB',(840,348),(20,26,29));draw=ImageDraw.Draw(canvas)
for i,(im,label) in enumerate(zip([ref,before,after],['Reference','Before v47','After v48'])):draw.text((8,i*116+5),label,fill='white');canvas.paste(im,(0,i*116+26))
canvas.save(O/'upper-window-comparison-v48.png')
D=json.loads((O/'upper-window-geometry-v48.json').read_text());C=np.array(D['camera']['position']);rot=np.array(D['camera']['rotation']);f=D['camera']['focalPixels'];edges=(np.arange(33)-16.5)*np.pi/16;edges[13:21]=[-.745387,-.567705,-.415142,-.217486,.006904,.147421,.411245,.678266]
reference={1:[[53,564.5],[77,566],[77,578],[53,576.2]],2:[[82.5,566.4],[106,567.55],[106,580],[82.5,578.5]],3:[[110.5,568],[134,569.1],[134,581.3],[110.5,580]]};measurements=[]
for k,target in reference.items():
 parts=[q for q in D['windowParts'] if q['id']==k];corners=[]
 for side,zi in [('left',1),('right',1),('right',0),('left',0)]:
  p=next(q for q in parts if q['leftExterior' if side=='left' else 'rightExterior']);bay=p['bay'];a=(edges[bay]+edges[bay+1])/2;h=(edges[bay+1]-edges[bay])/2;rad=np.array([np.sin(a),np.cos(a),0]);t=np.array([np.cos(a),-np.sin(a),0]);point=rad*23.5*np.cos(h)+t*p['x'][0 if side=='left' else 1]+[0,0,p['z'][zi]];q=(point-C)@rot;corners.append([354+f*q[0]/-q[2],500-f*q[1]/-q[2]])
 err=np.linalg.norm(np.array(corners)-target,axis=1);measurements.append({'window':k,'manuallyObservedImageCorners':target,'modeledOpeningImageCorners':corners,'cornerPixelErrors':err.tolist()})
maximum=max(max(q['cornerPixelErrors']) for q in measurements)
report={'scope':'Twelve manually observed corners of three fully visible upper window openings at 708x1000; the partly visible left window and hidden depth are excluded. These local anchors do not prove whole-scene fidelity.','manualMeasurementUncertaintyPixels':1.5,'maximumPixelError':maximum,'windows':measurements,'oneToOneComplete':False}
(O/'window-projection-comparison-v48.json').write_text(json.dumps(report,indent=2));print('UPPER_WINDOWS_48_REFERENCE_CORNERS',maximum,'pixels maximum')
