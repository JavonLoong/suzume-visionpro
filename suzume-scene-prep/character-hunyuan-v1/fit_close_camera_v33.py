"""Revisit the close-shot calibration with a broad physical camera search."""
from pathlib import Path
import json,numpy as np,sys,cv2
from scipy.optimize import least_squares
from PIL import Image,ImageDraw
R=Path(__file__).parent;O=R/'movie-sky-v33';O.mkdir(exist_ok=True)
src=json.loads((R/'movie-sky-v32/source-inspection-v32.json').read_text());F=np.array(src['frameMatrix']);Hi=np.linalg.inv(np.array(src['hingeMatrix']))
marks=[('panel2_1_TR',[1312,186]),('panel2_1_TL',[1352,171]),('panel2_1_BL',[1350,639]),('panel2_1_BR',[1311,616]),('panel3_1_TR',[1385,172]),('panel3_1_TL',[1436,150]),('panel3_1_BL',[1434,682]),('panel3_1_BR',[1383,655]),('knobFront',[1260,730])]
local=np.array([(Hi@np.r_[src['points'][name],1])[:3] for name,_ in marks]);target=np.array([p for _,p in marks],float)
frame_line=np.array([(F@np.array([.815,z,.12,1]))[:3] for z in [0,3.7]])
def basis(p):
 cx,cy,cz,yaw,pitch,roll,f,angle=p[:8];forward=np.array([np.sin(yaw)*np.cos(pitch),np.cos(yaw)*np.cos(pitch),-np.sin(pitch)]);right=np.array([np.cos(yaw),-np.sin(yaw),0.]);up=np.cross(right,forward);return np.array([cx,cy,cz]),right*np.cos(roll)+up*np.sin(roll),-right*np.sin(roll)+up*np.cos(roll),forward
def points(p):
 angle=p[7];co,si=np.cos(angle),np.sin(angle);Ry=np.array([[co,0,si],[0,1,0],[-si,0,co]]);scale=np.linalg.norm(F[:3,0]);unit=F[:3,:3].copy();unit[:,0]/=scale;v=(local*[scale,1,1])@Ry.T+[-.804*scale,.24,.055];return v@unit.T+F[:3,3]
def project(v,p):
 C,right,up,forward=basis(p);d=np.asarray(v)-C;depth=d@forward;cx,cy=p[8:10] if len(p)>8 else (1024,428);return np.stack([cx+p[6]*(d@right)/depth,cy-p[6]*(d@up)/depth],-1)
def residual(p):
 projected=project(points(p),p);line=project(frame_line,p);slope=(line[1,0]-line[0,0])/(line[1,1]-line[0,1]);left=[line[0,0]+(v-line[0,1])*slope for v in [0,856]]
 if '--panels-only' in sys.argv:return (projected[:8]-target[:8]).ravel()/5
 return np.r_[(projected-target).ravel()/5,(np.array(left)-[380,390])/5]
lo=[-10,-30,1.5,-1.4,-.5,-.15,500,.3];hi=[10,-.1,4,1.4,.5,.15,15000,2.8]
if '--shifted' in sys.argv:lo.extend([-1000,-1000]);hi.extend([3000,2000])
results=[]
for angle in [1.,1.55,2.,2.5]:
 for yaw in [-.7,0,.7]:
  p=[0,-5,2.4,yaw,0,0,3500,angle]
  if '--shifted' in sys.argv:p.extend([1024,428])
  fit=least_squares(residual,p,bounds=(lo,hi),loss='soft_l1',x_scale='jac',max_nfev=1500)
  results.append(fit)
best=min(results,key=lambda a:np.linalg.norm(residual(a.x)));p=best.x;C,right,up,forward=basis(p);M=np.eye(4);M[:3,:3]=np.column_stack([right,up,-forward]);M[:3,3]=C;pred=project(points(p),p);err=np.linalg.norm(pred-target,axis=1)
report={'revision':33,'parameters':dict(zip(['cameraX','cameraY','cameraZ','yaw','pitch','roll','focalPixels','doorAngle'],map(float,p))),'cameraMatrix':M.tolist(),'lensMm':float(p[6]*36/856),'meanDoorError':float(err.mean()),'maximumDoorError':float(err.max()),'landmarks':[{'name':n,'target':t,'projected':q.tolist(),'error':float(e)} for (n,t),q,e in zip(marks,pred,err)],'fitResidualNorm':float(np.linalg.norm(residual(p))),'allSolutionNorms':[float(np.linalg.norm(residual(r.x))) for r in results],'accepted':False}
suffix='-panels' if '--panels-only' in sys.argv else '-shifted' if '--shifted' in sys.argv else ''
if len(p)>8:report['principalPoint']=p[8:10].tolist()
homography,_=cv2.findHomography(local[:8,:2],target[:8],0);hp=cv2.perspectiveTransform(local[None,:8,:2],homography)[0];report['planeHomographyError']=np.linalg.norm(hp-target[:8],axis=1).tolist();report['planeHomography']=homography.tolist()
(O/('camera-search'+suffix+'-v33.json')).write_text(json.dumps(report,indent=2));im=Image.open(R/'movie-sky-v32/reference-close-2048.png').convert('RGB');draw=ImageDraw.Draw(im)
for (n,t),q in zip(marks,pred):
 x,y=t;draw.ellipse((x-5,y-5,x+5,y+5),outline='orange',width=2);x,y=q;draw.line((x-7,y,x+7,y),fill='cyan',width=2);draw.line((x,y-7,x,y+7),fill='cyan',width=2)
draw.line([tuple(q) for q in project(frame_line,p)],fill='cyan',width=2);im.save(O/('camera-search-diagnostic'+suffix+'-v33.png'));print(json.dumps(report,indent=2))
