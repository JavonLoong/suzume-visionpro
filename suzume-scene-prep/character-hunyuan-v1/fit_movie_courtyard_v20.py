"""Fit a complete courtyard placement to manually observed movie landmarks.

Only the architectural placement is fitted. The established foreground camera,
door, character and foot clearances are held fixed. This is not a full-image
similarity score and the poster scene must remain separately available.
"""
from pathlib import Path
import numpy as np,json,math
from scipy.optimize import least_squares
R=Path(__file__).parent;O=R/'movie-calibration-v20';O.mkdir(exist_ok=True)
radius=23.5;edges=np.array([-.745387,-.567705,-.415142,-.217486,.006904])
angle=(edges[0]+edges[1])/2;half=(edges[1]-edges[0])/2
chord=radius*np.cos(half);width=2*radius*np.sin(half)+.022
cam=np.array([.18,-4.04*np.cos(.01),1.94+4.04*np.sin(.01)])
focal=1656*30/36
def world(angle,r,x,z,params):
    yaw,tx,ty,sz,tz=params;a=angle+yaw
    return np.array([r*np.sin(a)+x*np.cos(a)+tx,r*np.cos(a)-x*np.sin(a)+ty,z*sz+tz])
def project(p):
    x,y,z=p-cam;depth=y*np.cos(.01)-z*np.sin(.01)
    return np.array([1276+focal*x/max(depth,.01),828-focal*(y*np.sin(.01)+z*np.cos(.01))/max(depth,.01)]),depth
anchors=[]
for a,u,label,weight in zip(edges,[195,892,1430,1908,2544],['pier 13','pier 14','pier 15 behind door, inferred','pier 16','pier 17'],[1,1,.35,1,.65]):
    anchors.append({'name':label,'angle':float(a),'radius':radius,'localX':0,'height':2.4,'target':[u,None],'weight':weight})
for name,x,z,target in [
    ('left arched window crown',width*.26,3.36,[758,450]),
    ('left arched window sill',width*.26,1.22,[758,674]),
    ('left arched window left jamb',width*.26-.5,2.2,[702,568]),
    ('left arched window right jamb',width*.26+.5,2.2,[814,568]),
    ('left rectangular window top left',-width*.48,3.36,[259,441]),
    ('left rectangular window bottom right',-width*.04,1.22,[648,674]),
    ('arcade lower cornice',0,4.67,[None,285]),
    ('left upper cornice',0,6.52,[None,56])]:
    anchors.append({'name':name,'angle':angle,'radius':float(chord),'localX':x,'height':z,'target':target,'weight':1})
def residual(params):
    values=[]
    for a in anchors:
        uv,depth=project(world(a['angle'],a['radius'],a['localX'],a['height'],params))
        values.extend([(uv[i]-v)*a['weight'] for i,v in enumerate(a['target']) if v is not None])
        values.append(max(0,2-depth)*100)
    # Door remains within the reconstructed courtyard, with room to orbit.
    values.append(max(0,np.hypot(params[1],params[2])-21.0)*100)
    return values
fit=least_squares(residual,[.5,0,-12,1,2],bounds=([-.4,-20,-21,.4,-2],[1.4,20,10,3,6]),loss='soft_l1',f_scale=25,max_nfev=2000)
def measurements(params):
    rows=[]
    for a in anchors:
        uv,depth=project(world(a['angle'],a['radius'],a['localX'],a['height'],params));target=np.array([v if v is not None else uv[i] for i,v in enumerate(a['target'])])
        rows.append({**a,'projected':uv.tolist(),'errorPixels':float(np.linalg.norm(uv-target)),'depth':float(depth)})
    return rows
before=measurements([0,0,0,1,0]);after=measurements(fit.x)
result={'revision':20,'reference':'reference-opening-50525.jpg','dimensions':[2552,1656],
        'method':'Robust least squares on manual facade landmarks. Foreground camera and geometry are fixed.',
        'parameters':dict(zip(['yaw','translateX','translateY','heightScale','heightOffset'],fit.x.tolist())),
        'before':before,'after':after,'meanAnchorErrorBefore':float(np.mean([a['errorPixels'] for a in before])),
        'meanAnchorErrorAfter':float(np.mean([a['errorPixels'] for a in after])),
        'oneToOneComplete':False,'limitations':['Landmark annotations are manual and partially occluded.','A global placement cannot correct every window proportion or bay type.','Rendered and all-angle review is still required.']}
# A single image leaves uniform depth/size scale about the camera ambiguous.
# Ground the building on the same horizontal water plane as the foreground.
# These two water-contact estimates are partially hidden by the terrace/debris;
# they constrain the depth ambiguity, not an independently known real size.
water_anchors=[{'angle':angle,'radius':float(chord-.50),'targetY':860},
               {'angle':float((edges[3]+edges[4])/2),'radius':float(radius*np.cos((edges[4]-edges[3])/2)-.50),'targetY':855}]
def ground_residual(scale):
    values=[]
    for a in water_anchors:
        p=world(a['angle'],a['radius'],0,0,fit.x)
        p=cam+float(scale[0])*(p-cam);p[2]=.05
        values.append(project(p)[0][1]-a['targetY'])
    return values
unconstrained=least_squares(ground_residual,[4.0],bounds=([1],[10]),loss='soft_l1',f_scale=12)
# Reject the roughly 6x solution: its giant architecture is a poor all-angle
# reconstruction. Cap at 3x, explicitly retaining a waterline projection error.
depth_fit=least_squares(ground_residual,[2.0],bounds=([1],[3]),loss='soft_l1',f_scale=12)
result['unconstrainedDepthScaleRejected']=float(unconstrained.x[0])
result['depthScale']=float(depth_fit.x[0]);result['depthScaleCenter']=cam.tolist()
result['waterContactAnchors']=water_anchors;result['waterContactResidualPixels']=ground_residual(depth_fit.x)
result['dimensionsInferred']=True
result['limitations'].append('Absolute architectural size is inferred from an animated reference; foreground and background may not share a physical camera. The depth fit gives a very large courtyard and requires orbit review.')
(O/'courtyard-fit-v20.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k not in ['before','after']},indent=2))
print(json.dumps([{'name':r['name'],'error':r['errorPixels'],'projection':r['projected']} for r in after],indent=2))
