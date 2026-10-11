"""Unproject observed film steelwork onto an inferred complete support ring."""
from pathlib import Path
import json,math,numpy as np
R=Path(__file__).parent;O=R/'movie-steel-v25';O.mkdir(exist_ok=True)
P=json.loads((R/'movie-projection-v24/joint-fit-v24.json').read_text(encoding='utf-8'))['parameters']
V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
old=json.loads((V/'dome-calibration-v7.json').read_text(encoding='utf-8'))
camera=np.array([P['cameraX'],-P['distance'],P['cameraZ']]);center=np.array([P['courtyardX'],P['courtyardY'],0]);radius=20.8
c,s=math.cos(P['pitch']),math.sin(P['pitch']);f=1656*P['lensMm']/36
def unproject(u,v):
    # Native axes: forward +Y, up +Z. Use the far positive cylinder crossing.
    screen=np.array([(u-1276)/f,(828-v)/f,1.])
    ray=np.array([screen[0],screen[2]*c+screen[1]*s,screen[1]*c-screen[2]*s])
    origin=camera-center;a=np.dot(ray[:2],ray[:2]);b=2*np.dot(origin[:2],ray[:2]);cc=np.dot(origin[:2],origin[:2])-radius**2
    roots=np.roots([a,b,cc]);positive=[float(x.real) for x in roots if abs(x.imag)<1e-9 and x.real>0];assert positive,(u,v,roots)
    return camera+max(positive)*ray
def project(point):
    x,y,z=np.array(point)-camera;d=y*c-z*s
    return [1276+f*x/d,828-f*(y*s+z*c)/d]
main=[]
for index,name,uv in [(27,'left main column',[425,836]),(0,'right main column',[1863,832])]:
    point=unproject(*uv);a=math.atan2(point[0]-center[0],point[1]-center[1]);main.append({'index':index,'name':name,'referenceFoot':uv,'angle':a,'point':point.tolist(),'projected':project(point),'footingTop':float(point[2]+.25)})
angles=np.zeros(28);angles[0]=main[1]['angle'];angles[27]=2*math.pi+main[0]['angle'];angles[1]=(angles[0]+.73)/2;angles[2]=.73;angles[3]=.95;angles[26]=2*math.pi-.76
for i in range(4,26):angles[i]=angles[3]+(angles[26]-angles[3])*(i-3)/23
assert np.all(np.diff(angles)>0)
beams=[]
for name,pixels in [
    ('left bowed beam',[[-140,218],[0,247],[100,272],[200,305],[300,335],[412,367]]),
    ('right bowed beam',[[1390,283],[1500,253],[1630,211],[1760,181],[1855,184]])]:
    points=[unproject(*uv).tolist() for uv in pixels]
    beams.append({'name':name,'referencePixels':pixels,'pointsNative':points,'projected':[project(p) for p in points],
                  'inferredOrOccludedPoints':[0] if name.startswith('left') else [0,1]})
ties=[]
for u,v in [(105,274),(208,309),(307,342)]:
    p=unproject(u,v);ties.append({'name':'left slender tie '+str(u),'bottom':p.tolist(),'topHeight':9.2,'referenceBottom':[u,v],'width':.035,'depth':.045})
# The film crop does not expose the upper break points or the rear dome. Keep
# a full ring of columns/ribs, separating measured front features from inference.
result={'revision':25,'reference':'reference-opening-50525.jpg','referenceDimensions':[2552,1656],
    'camera':P,'centerNative':center.tolist(),'radius':radius,'springHeight':8.3,'rise':12,
    'angles':angles.tolist(),'ends':old['ends'],'removedRibs':old['removed_ribs'],'mainColumns':main,'bowedBeams':beams,'slenderTies':ties,
    'columnSection':{'flangeWidth':.29,'radialDepth':.26,'webThickness':.022,'flangeThickness':.027},
    'beamSection':{'radialWidth':.18,'verticalDepth':.13,'webThickness':.018,'flangeThickness':.020},
    'oneToOneComplete':False,'assumptions':['Steel ring radius 20.8 is inferred, constrained to lie inside the 23.5 courtyard.','Visible bowed members are unprojected onto that cylinder; concealed depths are not measured.','Column tops, rear columns and broken radial ribs lie outside this movie crop and remain inferred.','Footings extend to the basin bed; the partially hidden surrounding bank still requires reconstruction.']}
(O/'steel-fit-v25.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({'radius':radius,'columns':main,'beams':[{ 'name':b['name'],'heightRange':[min(p[2] for p in b['pointsNative']),max(p[2] for p in b['pointsNative'])]} for b in beams]},indent=2))
