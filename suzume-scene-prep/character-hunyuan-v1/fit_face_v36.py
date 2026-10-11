"""Facial proportions from the official character still, with separate 3D parts.
The expression and the unseen head depth remain reconstructed assumptions.
"""
from pathlib import Path
import json,numpy as np
from scipy.optimize import least_squares
from scipy.interpolate import CubicHermiteSpline
R=Path(__file__).parent;O=R/'movie-face-v36';O.mkdir(exist_ok=True)
a=np.load(R/'movie-head-v35/head-check-v35.npz');world=a['after'];source=np.load(R/'movie-head-v35/head-source-v35.npz');local=source['local'];groups=json.loads((R/'movie-head-v35/groups-v35.json').read_text())
orig=local.copy();orig[:,0]=(orig[:,0]+.004)/.118;orig[:,1]/=.118;orig[:,2]=(orig[:,2]-(1.1751030684-.9738872647*.118))/.118
face_ids=np.array(groups['Head part :: Clean facial surface']);B=np.c_[orig[face_ids],np.ones(len(face_ids))];mapping=np.linalg.lstsq(B,world[face_ids],rcond=None)[0];assert np.linalg.norm(B@mapping-world[face_ids],axis=1).max()<1e-6
def mapped(v):return np.c_[v,np.ones(len(v))]@mapping
C=np.array([-.15,5,2.75]);F=np.array([0,-4.4,-.1]);F/=np.linalg.norm(F);right=np.cross(F,[0,0,1]);right/=np.linalg.norm(right);up=np.cross(right,F)
def project(v):return np.c_[325+(v-C)@right*800/1.35,400-(v-C)@up*800/1.35]
current_uv=project(world);eye_ids=[groups['Head part :: right sclera'][0],groups['Head part :: left sclera'][0]];eye_uv=current_uv[eye_ids];eye_mid=eye_uv.mean(0);eye_distance=np.linalg.norm(eye_uv[1]-eye_uv[0])
reference_eyes=np.array([[338.5,150.5],[443.5,154.] ]);ref_mid=reference_eyes.mean(0);axis=reference_eyes[1]-reference_eyes[0];ref_distance=np.linalg.norm(axis);axis/=ref_distance;vertical=np.array([-axis[1],axis[0]])
def align(p):
 p=np.array(p)-ref_mid;return eye_mid+np.c_[p@axis,p@vertical]*eye_distance/ref_distance
# Each visible cheek/jaw boundary is read independently. Accuracy is limited
# by the 680 x 390 source and its slight head pose; do not treat this as a scan.
ref_outline=np.array([[289,185],[492,185],[294,210],[487,210],[304,235],[479,235],[323,260],[457,260],[348,280],[425,280],[365,295],[401,295]],float)
targets=align(ref_outline);chin_target=align([[383,305]])[0]
knots=np.array([-.52,-.43,-.25,0,.20,.40,.62,.77,.84]);widths=np.array([.018,.19,.33,.423,.452,.455,.37,.21,.015]);fronts=np.array([-.30,-.405,-.48,-.495,-.48,-.44,-.345,-.18,-.03]);backs=np.array([.10,.20,.36,.49,.55,.55,.48,.29,.04])
def interp(values,z):
 slopes=np.r_[(values[1]-values[0])/(knots[1]-knots[0]),(values[2:]-values[:-2])/(knots[2:]-knots[:-2]),(values[-1]-values[-2])/(knots[-1]-knots[-2])]
 return CubicHermiteSpline(knots,values,slopes)(np.clip(z,knots[0],knots[-1]))
def shift_z(z,p):
 t=np.maximum(.17-z,0);positive=np.where(t<.08,t*t/.16,t-.04);return z+p[0]*positive
def width_at(z,p):return interp(widths,z)*(1+p[1]*np.exp(-((z+.37)/.17)**2)+p[2]*np.exp(-((z+.10)/.20)**2)+(p[3] if len(p)>3 else 0)*np.exp(-((z+.49)/.06)**2))
def face_y(x,z,p,new_nose=True):
 w=np.maximum(.025,width_at(z,p));fz=interp(fronts,z);bz=interp(backs,z);center=(fz+bz)/2;u=np.minimum(.999,abs(x)/w);y=center-(center-fz)*np.sqrt(1-u**4)
 y-=.057*np.exp(-(x/.052)**2-((z-.085)/.10)**2) if new_nose else .060*np.exp(-(x/.065)**2-((z+.035)/.115)**2)
 y-=.021*np.exp(-(x/.12)**2-((z+.245)/.065)**2)
 return y
def make_face(p,new_nose=True):
 z=np.repeat(np.linspace(-.52,.84,112),160);angle=np.tile(np.arange(160)*2*np.pi/160,112);co=np.cos(angle);w=np.maximum(.01,width_at(z,p));x=w*np.sin(angle);fz=interp(fronts,z);bz=interp(backs,z);center=(fz+bz)/2
 y=np.where(co>=0,face_y(x,z,p,new_nose),center+(bz-center)*(-co));jaw=(1-co)*.5*np.maximum(0,(-z-.20)/.32)*.18
 result=np.c_[x,y,shift_z(z+jaw,p)];return np.vstack([result,[0,-.10,shift_z(-.43,p)],[0,0,.84]])
assert len(make_face([0,0,0]))==len(face_ids)
face_lookup=np.full(len(world),-1);face_lookup[face_ids]=np.arange(len(face_ids));tri=source['faces'];tri=face_lookup[tri[np.all(face_lookup[tri]>=0,axis=1)]]
def contour(uv,rows):
 points=uv[tri];start=points.reshape(-1,2);end=np.roll(points,-1,axis=1).reshape(-1,2);dy=end[:,1]-start[:,1];result=[]
 for row in rows:
  k=(abs(dy)>1e-9)&(row>=np.minimum(start[:,1],end[:,1]))&(row<=np.maximum(start[:,1],end[:,1]));x=start[k,0]+(row-start[k,1])*(end[k,0]-start[k,0])/dy[k]
  result.append([x.min(),x.max()] if len(x) else [eye_mid[0],eye_mid[0]])
 return np.array(result)
def residual(p):
 uv=project(mapped(make_face(p)));bounds=contour(uv,targets[:,1]);pred=np.where(np.arange(len(targets))%2==0,bounds[:,0],bounds[:,1]);return np.r_[(pred-targets[:,0]),(uv[:,1].max()-chin_target[1])*2,p[1:]*8]
fit=least_squares(residual,[.075,0,0,.15],bounds=([0,-.14,-.14,0],[.16,.14,.14,.7]),xtol=1e-11,ftol=1e-11,gtol=1e-11);p=fit.x
after=world.copy();after[face_ids]=mapped(make_face(p));changed=['Clean facial surface']
for name,ids in groups.items():
 short=name.replace('Head part :: ','')
 if not any(x in short for x in ['sclera','limbus','iris','pupil','catchlight','lashes','lower lid','eyebrow','eyelash','nostril','mouth']):continue
 ids=np.array(ids);v=orig[ids].copy()
 if any(x in short for x in ['upper lashes','eyelash','mouth']):
  rings=v.reshape(-1,8,3);centers=rings.mean(axis=1,keepdims=True);relative=rings-centers
  if 'mouth' in short:
   relative[:,:,2]*=4.5;mouth_tooth=(abs(rings[:,:,0])<.045)&(relative[:,:,2]>.004)&(relative[:,:,1]<-.0005)
  else:relative*=1.65 if 'upper lashes' in short else 1.4
  v=(centers+relative).reshape(-1,3)
 base_offset=v[:,1]-face_y(v[:,0],v[:,2],[0,0,0],False)
 # White aperture narrows while its upper/lower arcs become taller; the iris
 # keeps its reference-scaled diameter and receives a narrower black pupil.
 if short.startswith(('right ','left ')):
  cx=-.224 if short.startswith('right ') else .224;cz=.17
  if any(x in short for x in ['sclera','lashes','lower lid','eyelash']):v[:,0]=cx+(v[:,0]-cx)*.82;v[:,2]=cz+(v[:,2]-cz)*1.14
  if 'pupil' in short:v[:,0]=cx+(v[:,0]-cx)*.76
 if 'nostril' in short:v[:,2]+=.070;v[:,0]*=.85
 if 'mouth' in short:v[:,0]*=.9
 v[:,1]=face_y(v[:,0],v[:,2],p)+base_offset;v[:,2]=shift_z(v[:,2],p);after[ids]=mapped(v);changed.append(short)
def bezier(points,t):
 a,b,c,d=np.array(points);return (1-t)**3*a+3*(1-t)**2*t*b+3*(1-t)*t*t*c+t**3*d
def lock(controls,width,depth=.018):
 result=[]
 for side in [-1,1]:
  for t in np.linspace(0,1,40):
   center=bezier(controls,t);tangent=bezier(controls,min(1,t+.001))-bezier(controls,max(0,t-.001));trans=np.array([tangent[2],0,-tangent[0]]);trans/=np.linalg.norm(trans);breadth=width*(.45+.55*np.sin(np.pi*t*.82))*(1-t**3)+.0004
   for u in np.linspace(-1,1,12):
    q=center+trans*u*breadth/2;q[1]=face_y(q[0],min(q[2],.832),p)-.030+side*depth*(.45+.55*(1-u*u));result.append(q)
 return np.array(result)
hair_changes={
 'Fine right forelock':([[-.20,-.33,.81],[-.25,-.54,.65],[-.21,-.58,.41],[-.11,-.54,.33]],.046),
 'Central pointed bang':([[-.20,-.34,.81],[-.08,-.61,.68],[.09,-.60,.45],[.12,-.55,.255]],.16),
 'Middle pointed bang':([[-.15,-.33,.80],[.12,-.63,.64],[.23,-.60,.48],[.225,-.53,.29]],.17),
 'Left pointed bang':([[-.09,-.32,.79],[.23,-.57,.63],[.31,-.57,.44],[.36,-.45,.30]],.18),
 'Swept right temple':([[-.20,-.32,.80],[-.37,-.48,.68],[-.48,-.48,.46],[-.44,-.39,.32]],.13)
}
for name,(controls,width) in hair_changes.items():
 ids=np.array(groups['Head part :: '+name]);after[ids]=mapped(lock(controls,width));changed.append(name)
# Raise only the frontal hairline on the exposed temple side. Back scalp,
# ponytail, pins, ear geometry and side locks retain the v35 vertices exactly.
ids=np.array(groups['Head part :: Smooth hair cap']);v=orig[ids].copy();theta=np.tile(np.arange(144)*2*np.pi/144,64);wrapped=(theta+np.pi)%(2*np.pi)-np.pi;rows=np.repeat(np.linspace(0,1,64),144)
delta=.18*np.exp(-((wrapped+.52)/.43)**2)*np.clip(np.cos(theta),0,1)*rows**2;v[:,2]+=delta
z=v[:,2];sf=np.sqrt(np.maximum(0,1-((z-.25)/.645)**2));blend=np.clip((z-.43)/.15,0,1);blend=blend*blend*(3-2*blend)
cw=(np.maximum(.018,interp(widths,np.minimum(z,.84)))+.035)*(1-blend)+.51*sf*blend
front=(interp(fronts,np.minimum(z,.84))-.034)*(1-blend)+(.045-.525*sf)*blend;back=(interp(backs,np.minimum(z,.84))+.034)*(1-blend)+(.045+.575*sf)*blend;mid=(front+back)/2
v[:,0]=cw*np.sin(theta);v[:,1]=np.where(np.cos(theta)>=0,mid-(mid-front)*np.sqrt(np.maximum(0,1-np.sin(theta)**4)),mid+(back-mid)*(-np.cos(theta)))
after[ids]=mapped(v);changed.append('Smooth hair cap frontal hairline')
# Matrix round-off is not a geometry edit: restore the untouched cap vertices.
untouched_cap=delta<1e-8;after[ids[untouched_cap]]=world[ids[untouched_cap]]
np.savez_compressed(O/'face-fit-v36.npz',before=world,after=after,ponytailMask=a['ponytailMask'],mouthToothVertices=np.array(groups['Head part :: Quiet mouth line'])[mouth_tooth.ravel()])
uv=project(after[face_ids]);bounds=contour(uv,targets[:,1]);actual=np.where(np.arange(len(targets))%2==0,bounds[:,0],bounds[:,1]);report={'revision':36,'reference':'reference-suzume-official-face.jpg','referenceSize':[680,390],'referenceEyeCenters':reference_eyes.tolist(),'referenceOutlinePoints':ref_outline.tolist(),'referenceChin':[383,305],'landmarkUncertaintyPixels':3,'alignment':'Eye distance and eye-line angle; portrait pose/depth remains uncertain.','lowerFaceFitParameters':p.tolist(),'outlineTargetInStudioPixels':targets.tolist(),'outlineActualX':actual.tolist(),'outlineMeanErrorInStudioPixels':float(abs(actual-targets[:,0]).mean()),'outlineMaxErrorInStudioPixels':float(abs(actual-targets[:,0]).max()),'chinTargetStudioY':float(chin_target[1]),'chinActualStudioY':float(uv[:,1].max()),'eyeWhiteWidthScale':.82,'eyeWhiteHeightScale':1.14,'noseBumpSourceZ':.085,'nostrilSourceZShift':.07,'pupilWidthScale':.76,'changedParts':changed,'ponytailUnchanged':bool(np.array_equal(after[a['ponytailMask']],world[a['ponytailMask']])),'oneToOneComplete':False}
report.update({'upperLashRadiusScale':1.65,'outerEyelashRadiusScale':1.4,'mouthVerticalReliefScale':4.5,'mouthWidthScale':.9,'mouthRepresentation':'Shallow curved 3D relief with dark opening and upper tooth material; hidden oral anatomy is not reconstructed.'})
(O/'fit-v36.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
