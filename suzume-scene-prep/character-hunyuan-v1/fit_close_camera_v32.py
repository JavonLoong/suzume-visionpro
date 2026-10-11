"""Fit a separate close reference camera to existing door geometry, with no mesh warp."""
from pathlib import Path
import json,sys,numpy as np
from scipy.optimize import least_squares
from PIL import Image,ImageDraw
R=Path(__file__).parent;O=R/'movie-sky-v32';src=json.loads((O/'source-inspection-v32.json').read_text(encoding='utf-8'));F=np.array(src['frameMatrix']);H=np.array(src['hingeMatrix']);Hi=np.linalg.inv(H)
marks=[('panel2_1_TR',[1312,186]),('panel2_1_TL',[1352,171]),('panel2_1_BL',[1350,639]),('panel2_1_BR',[1311,616]),('panel3_1_TR',[1385,172]),('panel3_1_TL',[1436,150]),('panel3_1_BL',[1434,682]),('panel3_1_BR',[1383,655]),('knobFront',[1260,730])]
local=np.array([(Hi@np.r_[src['points'][name],1])[:3] for name,_ in marks]);target=np.array([p for _,p in marks],float)
def basis(p):
    cx,cy,cz,yaw,pitch,roll,f,angle=p;forward=np.array([np.sin(yaw)*np.cos(pitch),np.cos(yaw)*np.cos(pitch),-np.sin(pitch)]);right=np.array([np.cos(yaw),-np.sin(yaw),0.]);up=np.cross(right,forward);return np.array([cx,cy,cz]),right*np.cos(roll)+up*np.sin(roll),-right*np.sin(roll)+up*np.cos(roll),forward
def points(p):
    angle=p[7];co,si=np.cos(angle),np.sin(angle);Ry=np.array([[co,0,si],[0,1,0],[-si,0,co]])
    if '--rigid-leaf' in sys.argv:
        scale=np.linalg.norm(F[:3,0]);unit=F[:3,:3].copy();unit[:,0]/=scale;v=(local*[scale,1,1])@Ry.T+[-.804*scale,.24,.055];return v@unit.T+F[:3,3]
    v=local@Ry.T+[-.804,.24,.055];return v@F[:3,:3].T+F[:3,3]
def project(v,p):
    C,right,up,forward=basis(p);d=np.asarray(v)-C;depth=d@forward;return np.stack([1024+p[6]*(d@right)/depth,428-p[6]*(d@up)/depth],-1)
frame_line=np.array([(F@np.array([.815,z,.12,1]))[:3] for z in [0,3.7]])
def residual(p,fixed=False):
    projected=project(points(p),p);err=(projected-target).ravel()/5
    line=project(frame_line,p);slope=(line[1,0]-line[0,0])/(line[1,1]-line[0,1]);left=[line[0,0]+(v-line[0,1])*slope for v in [0,856]]
    return np.r_[err,(np.array(left)-[383,378])/3, (p[7]-1.55)/(.0001 if fixed else .35)]
lower=[-1,-7,1.7,-.4,-.3,-.08,600,1.30];upper=[1,-.5,3.3,.4,.3,.08,5000,1.95]
initial=[.15,-3.1,2.5,0,0,0,2300,1.55];fixed=least_squares(lambda p:residual(p,True),initial,bounds=(lower,upper),loss='soft_l1',max_nfev=3000)
fit=least_squares(residual,fixed.x,bounds=(lower,upper),loss='soft_l1',max_nfev=3000);p=fit.x;C,right,up,forward=basis(p);M=np.eye(4);M[:3,:3]=np.column_stack([right,up,-forward]);M[:3,3]=C;proj=project(points(p),p);errors=np.linalg.norm(proj-target,axis=1)
result={'revision':32,'reference':'reference-opening-50528.jpg','referenceSize':[6400,2675],'fittingSize':[2048,856],'manualLandmarks':[{ 'name':name,'target':t,'projected':r.tolist(),'errorPixels':float(e)} for (name,t),r,e in zip(marks,proj,errors)],'parameters':dict(zip(['cameraX','cameraY','cameraZ','yaw','pitch','roll','focalPixels','doorAngle'],map(float,p))),'cameraMatrix':M.tolist(),'lensMm':float(p[6]*36/856),'meanDoorLandmarkErrorPixels':float(errors.mean()),'fixedDoorAngleMeanErrorPixels':float(np.linalg.norm(project(points(fixed.x),fixed.x)-target,axis=1).mean()),'leftFrameConstraint':[[383,0],[378,856]],'scope':'Manually annotated door molding and partly occluded handle only. Character pose, wider architecture and lens distortion are not calibrated by this fit. Door angle is a separate inferred pose for this close shot; the main opening camera and pose remain unchanged.','oneToOneComplete':False}
suffix='-rigid' if '--rigid-leaf' in sys.argv else ''
result['rigidLeafTrial']='--rigid-leaf' in sys.argv
(O/('close-camera-fit'+suffix+'-v32.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
im=Image.open(O/'reference-close-2048.png').convert('RGB');d=ImageDraw.Draw(im)
for i,((name,t),r) in enumerate(zip(marks,proj)):
    x,y=t;d.ellipse((x-5,y-5,x+5,y+5),outline='orange',width=2);x,y=r;d.line((x-6,y,x+6,y),fill='cyan',width=2);d.line((x,y-6,x,y+6),fill='cyan',width=2);d.text((x+8,y),str(i),fill='cyan')
d.line([tuple(x) for x in project(frame_line,p)],fill='cyan',width=2);im.save(O/('close-camera-landmark-diagnostic'+suffix+'.png'))
print(json.dumps({k:result[k] for k in ['parameters','lensMm','meanDoorLandmarkErrorPixels','fixedDoorAngleMeanErrorPixels']},indent=2))
