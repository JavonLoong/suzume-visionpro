"""Fit actual window openings on bay 16, using v20's fixed courtyard transform."""
from pathlib import Path
import numpy as np,json,math
from scipy.optimize import least_squares
R=Path(__file__).parent;O=R/'movie-windows-v21';O.mkdir(exist_ok=True)
fit=json.loads((R/'movie-calibration-v20'/'courtyard-fit-v20.json').read_text());p=fit['parameters']
edges=[-.217486,.006904];angle=sum(edges)/2;chord=23.5*math.cos((edges[1]-edges[0])/2);width=47*math.sin((edges[1]-edges[0])/2)+.022
cam=np.array(fit['depthScaleCenter']);k=fit['depthScale']
def project(x,z,front=0):
    a=angle+p['yaw'];point=np.array([(chord-front)*math.sin(a)+x*math.cos(a)+p['translateX'],(chord-front)*math.cos(a)-x*math.sin(a)+p['translateY'],z*p['heightScale']+p['heightOffset']])
    point=cam+k*(point-cam);x,y,z=point-cam;depth=y*math.cos(.01)-z*math.sin(.01)
    return np.array([1276+1380*x/depth,828-1380*(y*math.sin(.01)+z*math.cos(.01))/depth])
rect_targets=np.array([[1960,444],[2230,444],[2230,674],[1960,674]])
def corners(q):
    x,y,w,h=q;return np.array([project(x-w/2,y+h),project(x+w/2,y+h),project(x+w/2,y),project(x-w/2,y)])
rectangle=least_squares(lambda q:(corners(q)-rect_targets).ravel(),[-1,1.22,2.2,2.1],bounds=([-2.2,.9,1.2,1.3],[0,1.8,3.2,3.0]))
circle_targets=np.array([[2390,437],[2443,490],[2390,543],[2337,490]])
def cardinal(q):
    x,z,rx,ry=q;return np.array([project(x,z+ry),project(x+rx,z),project(x,z-ry),project(x-rx,z)])
circle=least_squares(lambda q:(cardinal(q)-circle_targets).ravel(),[1.3,2.9,.42,.54],bounds=([.4,2,.2,.25],[2.3,3.6,.8,1]))
roof=least_squares(lambda q:[project(0,q[0])[1]-277],[5.5],bounds=([4.5],[6.5]))
result={'revision':21,'reference':'reference-opening-50525.jpg','referenceDimensions':[2552,1656],'bayIndex':16,'angle':angle,'edges':edges,'chordRadius':chord,'bayWidth':width,'rectangle':dict(zip(['x','bottom','width','height'],rectangle.x.tolist())),'oculus':dict(zip(['x','centerY','radiusX','radiusY'],circle.x.tolist())),'rectangleTargets':rect_targets.tolist(),'rectangleProjected':corners(rectangle.x).tolist(),'oculusTargets':circle_targets.tolist(),'oculusProjected':cardinal(circle.x).tolist(),'rectangleMeanErrorPixels':float(np.mean(np.linalg.norm(corners(rectangle.x)-rect_targets,axis=1))),'oculusMeanErrorPixels':float(np.mean(np.linalg.norm(cardinal(circle.x)-circle_targets,axis=1))),'notes':['Manual image annotations, not official dimensions.','Oculus profile compensates for the inherited vertical facade scale; the finished opening is close to circular in world space.','This local fit is not a whole-image fidelity score.'],'oneToOneComplete':False}
result['roofY']=float(roof.x[0]);result['roofTargetY']=277;result['roofProjected']=project(0,roof.x[0]).tolist()
drain=least_squares(lambda q:[project(q[0],3.4,.47)[0]-2299],[.6])
result['drainpipe']={'x':float(drain.x[0]),'bottom':.66,'top':4.92,'radius':.038,'front':.47}
(O/'window-fit-v21.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
