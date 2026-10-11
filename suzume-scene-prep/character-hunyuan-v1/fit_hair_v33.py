"""Fit a continuous ponytail deformation to the opening-frame hair-tip landmark."""
from pathlib import Path
import numpy as np,json
from scipy.optimize import least_squares
R=Path(__file__).parent;O=R/'movie-hair-v33';d=np.load(O/'head-source-v33.npz');p=d['original'];base=d['local'];world=d['world'];q=json.loads((R/'movie-projection-v24/joint-fit-v24.json').read_text())['parameters']
def smooth(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
root_phase=smooth(.15,.50,p[:,2]);rear_start=.225+root_phase*(.30-.225);rear_end=.255+root_phase*(.43-.255)
mask=smooth(rear_start,rear_end,p[:,1])*(1-smooth(.25,.35,np.abs(p[:,0])))*(1-smooth(.35,.60,p[:,2]))
progress=np.maximum(.6-p[:,2],0);tip=int(np.argmin(np.where(mask>.99,world[:,2],100)))
target=np.array([1183.5,772.]);C=np.array([q['cameraX'],-q['distance'],q['cameraZ']]);pitch=q['pitch'];up=np.array([0,np.sin(pitch),np.cos(pitch)]);forward=np.array([0,np.cos(pitch),-np.sin(pitch)]);f=q['lensMm']/36*1656
def deform(parameters):
 stretch,tip_x=parameters;out=base.copy();out[:,2]-=.118*progress*mask*(stretch-1);out[:,0]+=.118*tip_x*mask*(progress/progress[tip])**2
 predicted=world+(out-base)*[-2.9325,-2.9325,2.9325]
 return out,predicted
def project(v):
 v=v-C;return np.stack([1276+f*v[...,0]/(v@forward),828-f*(v@up)/(v@forward)],-1)
fit=least_squares(lambda pars:project(deform(pars)[1][tip])-target,[1.5,-.05],bounds=([1,-.3],[2.1,.3]),xtol=1e-12,gtol=1e-12,ftol=1e-12)
new,wp=deform(fit.x);np.savez_compressed(O/'hair-deformation-v33.npz',local=new,mask=mask,predictedWorld=wp)
report={'revision':33,'reference':'reference-opening-50525.jpg','referenceDimensions':[2552,1656],'method':'Smooth, spatially localized extension of the existing Hunyuan ponytail; original mesh topology and vertex colors retained.','targetTipPixels':target.tolist(),'tipVertex':tip,'parameters':{'extensionFactor':float(fit.x[0]),'tipOriginalXShift':float(fit.x[1])},'beforeTipPixels':project(world[tip]).tolist(),'predictedTipPixels':project(wp[tip]).tolist(),'beforeTipWorld':world[tip].tolist(),'predictedTipWorld':wp[tip].tolist(),'movedVertices':int(np.any(new!=base,axis=1).sum()),'untouchedFaceAndFrontVertices':int((p[:,1]<=.225).sum()),'maskDefinition':{'rearYRoot':[.30,.43],'rearYLowerTail':[.225,.255],'rootBlendZ':[.15,.50],'sideAbsX':[.25,.35],'rootZ':[.35,.60]},'oneToOneComplete':False,'scope':'A manually measured back-view silhouette point does not establish facial likeness or all-angle fidelity.'}
(O/'hair-fit-v33.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
