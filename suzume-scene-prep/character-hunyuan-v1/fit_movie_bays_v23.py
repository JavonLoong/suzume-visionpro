"""Fit the visible lower-story openings while preserving the complete ring."""
from pathlib import Path
import json, math, numpy as np
from scipy.optimize import least_squares
R=Path(__file__).parent;O=R/'movie-bays-v23';O.mkdir(exist_ok=True)
placement=json.loads((R/'movie-calibration-v20/courtyard-fit-v20.json').read_text(encoding='utf-8'))
p=placement['parameters'];cam=np.array(placement['depthScaleCenter'])
edges={12:(12-16.5)*math.pi/16,13:-.745387,14:-.567705,15:-.415142,16:-.217486}
bays=[]
for index in range(12,16):
    lo,hi=edges[index],edges[index+1];angle=(lo+hi)/2;radius=23.5*math.cos((hi-lo)/2);width=47*math.sin((hi-lo)/2)+.022
    spec={'index':index,'edges':[lo,hi],'angle':angle,'chordRadius':radius,'bayWidth':width,'openings':[]}
    def project(x,z):
        a=angle+p['yaw'];v=np.array([radius*math.sin(a)+x*math.cos(a)+p['translateX'],radius*math.cos(a)-x*math.sin(a)+p['translateY'],z*p['heightScale']+p['heightOffset']])-cam
        depth=v[1]*math.cos(.01)-v[2]*math.sin(.01)
        return np.array([1276+1380*v[0]/depth,828-1380*(v[1]*math.sin(.01)+v[2]*math.cos(.01))/depth])
    def corners(q):
        x,y,w,h=q
        return np.array([project(x-w/2,y+h),project(x+w/2,y+h),project(x+w/2,y),project(x-w/2,y)])
    boxes={12:[(-350,437,147,674)],13:[(259,441,420,674),(470,441,648,674)],14:[],15:[(1509,440,1668,674),(1700,440,1858,674)]}[index]
    for j,(left,top,right,bottom) in enumerate(boxes):
        target=np.array([[left,top],[right,top],[right,bottom],[left,bottom]])
        result=least_squares(lambda q:(corners(q)-target).ravel(),[0,1.3,1.1,2.2],bounds=([-width/2,.9,.3,1.2],[width/2,1.9,width-.1,3.0]))
        x,y,w,h=result.x;assert -width/2+.06<x-w/2<x+w/2<width/2-.06
        assert y+h<4.60
        spec['openings'].append({'type':'rectangle','name':f'rectangle {j+1}','x':x,'bottom':y,'width':w,'height':h,'panels':6 if index==12 else 3,
            'targets':target.tolist(),'projected':corners(result.x).tolist(),'meanErrorPixels':float(np.linalg.norm(corners(result.x)-target,axis=1).mean()),
            'partiallyOccluded':index in [12,15] and j==0})
    if index==13:
        target=np.array([[758,450],[702,504],[814,504],[702,674],[814,674]])
        def arch(q):
            x,y,w,h,rise=q
            return np.array([project(x,y+h),project(x-w/2,y+h-rise),project(x+w/2,y+h-rise),project(x-w/2,y),project(x+w/2,y)])
        result=least_squares(lambda q:(arch(q)-target).ravel(),[1,1.25,.9,2.0,.5],bounds=([.3,.9,.5,1.5,.25],[width/2,1.8,1.5,2.8,.9]))
        x,y,w,h,rise=result.x
        spec['openings'].append({'type':'arch','name':'arched window','x':x,'bottom':y,'width':w,'height':h,'rise':rise,'panels':2,
            'targets':target.tolist(),'projected':arch(result.x).tolist(),'meanErrorPixels':float(np.linalg.norm(arch(result.x)-target,axis=1).mean())})
    spec['observedLowerStory']=bool(spec['openings'])
    spec['upperStory']='Retain the existing complete geometric upper story; its height and aperture arrangement remain subject to further movie calibration.'
    bays.append(spec)
result={'revision':23,'reference':'reference-opening-50525.jpg','referenceDimensions':[2552,1656],
    'method':'Manual rectangular and arched window landmarks, fixed v20 courtyard placement and fixed foreground camera.',
    'bays':bays,'oneToOneComplete':False,
    'limitations':['Partially occluded window edges are inferred.','The occluded entrance of bay 14 is retained from the existing model.','Upper levels and absolute courtyard dimensions have not been re-fitted in this step.','Landmark residuals are not whole-scene fidelity scores.']}
(O/'bay-fit-v23.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps([{ 'bay':b['index'],'openings':[{'name':o['name'],'width':o['width'],'height':o['height'],'error':o['meanErrorPixels']} for o in b['openings']]} for b in bays],indent=2))
