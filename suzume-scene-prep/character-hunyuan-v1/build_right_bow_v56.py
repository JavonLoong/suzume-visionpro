"""Fit a closed I-section sweep to measured visible beam boundaries."""
from pathlib import Path
import ast, hashlib, json
import cv2
import numpy as np
from scipy.interpolate import PchipInterpolator
from scipy.optimize import least_squares
from PIL import Image,ImageDraw

R=Path(__file__).parent;O=R/'poster-right-bow-v56'
V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
source=json.loads((O/'source-right-bow-v56.json').read_text())
M=np.array(source['camera']['matrixWorld']);C=M[:3,3];f=source['camera']['lens']/36*1000
for n in ast.parse((R/'build_poster_steel_v39.py').read_text()).body:
 if isinstance(n,ast.FunctionDef) and n.name in ['section','cap_triangles']:
  exec(compile(ast.Module(body=[n],type_ignores=[]),'section helpers','exec'))

# Boundary observations are in the 708 x 1000 reference frame. The dark lower
# edge is followed separately from the background arcade/cornice behind it.
stations=np.array([[523,620.85],[526,619.90],[530,618.40],[540,615.35],
 [550,612.00],[560,609.10],[570,606.25],[580,603.65],[590,601.20],
 [600,598.95],[610,596.85],[620,594.90],[630,593.15],[640,591.75],
 [650,590.55],[660,589.55],[670,588.55],[680,587.80],[690,587.40],
 [700,587.05],[708,587.05],[712,587.10]],float)
bottom=PchipInterpolator(stations[:,0],stations[:,1],extrapolate=True)
width=PchipInterpolator([523,550,580,610,640,670,700,712],[3.3,3.3,3.6,3.6,3.25,3.3,3.35,3.35])
top=lambda u:bottom(u)-width(u)
def project(p):
 q=(np.asarray(p)-C)@M[:3,:3]
 return np.stack([354+f*q[...,0]/-q[...,2],500-f*q[...,1]/-q[...,2]],axis=-1)
def lift(uv):
 uv=np.atleast_2d(uv);q=np.c_[(uv[:,0]-354)/f,(500-uv[:,1])/f,-np.ones(len(uv))]@M[:3,:3].T
 a=(q[:,:2]**2).sum(1);b=2*(q[:,:2]*C[:2]).sum(1);c=(C[:2]**2).sum()-20.3**2
 t=(-b+np.sqrt(b*b-4*a*c))/(2*a)
 return C+t[:,None]*q

us=np.linspace(523,712,321);vs=(top(us)+bottom(us))/2
depth=np.full(len(us),.11);radial_width=.19
for iteration in range(3):
 p=lift(np.c_[us,vs]);t=np.gradient(p,axis=0);t/=np.linalg.norm(t,axis=1)[:,None]
 a=np.c_[p[:,:2],np.zeros(len(p))];a-=(a*t).sum(1)[:,None]*t;a/=np.linalg.norm(a,axis=1)[:,None]
 b=np.cross(t,a);flip=b[:,2]<0;a[flip]*=-1;b[flip]*=-1
 for i,u in enumerate(us):
  def residual(x):
   center=lift([[u,x[0]]])[0];shape=section(radial_width,x[1],.024,.014)
   ring=center+a[i]*shape[:,0,None]+b[i]*shape[:,1,None];q=project(ring)
   return [np.min(q[:,1]-top(q[:,0])),np.max(q[:,1]-bottom(q[:,0]))]
  fit=least_squares(residual,[vs[i],depth[i]],bounds=([vs[i]-3,.035],[vs[i]+3,.25]),xtol=1e-11,ftol=1e-11,gtol=1e-11)
  assert np.max(abs(fit.fun))<.002,(i,fit.fun);vs[i],depth[i]=fit.x
p=lift(np.c_[us,vs]);shape=np.array([section(radial_width,d,.024,.014) for d in depth])
vertices=(p[:,None,:]+a[:,None,:]*shape[:,:,0,None]+b[:,None,:]*shape[:,:,1,None]).reshape(-1,3)
faces=[];surface=[]
for i in range(len(us)-1):
 for k in range(12):
  aa=i*12+k;bb=i*12+(k+1)%12
  faces.extend([[aa,bb,bb+12],[aa,bb+12,aa+12]]);surface.extend([k,k])
for q in cap_triangles(shape[0]):faces.append(q[::-1]);surface.append(12)
for q in cap_triangles(shape[-1]):faces.append([k+(len(us)-1)*12 for k in q]);surface.append(13)
faces=np.array(faces);vol=np.einsum('ij,ij->i',vertices[faces[:,0]],np.cross(vertices[faces[:,1]],vertices[faces[:,2]])).sum()/6
if vol<0:faces=faces[:,::-1];vol=-vol
edges=np.sort(np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]),axis=1);_,counts=np.unique(edges,axis=0,return_counts=True);assert np.all(counts==2)
uv0=project(vertices);texture_uv=np.c_[(uv0[:,0]-523)/189,1-np.clip((uv0[:,1]-top(uv0[:,0]))/width(uv0[:,0]),.015,.985)]
# The unwrapped texture samples only the beam's own narrow strip. It cannot
# accidentally project neighboring architecture onto unseen flange surfaces.
photo=np.asarray(Image.open(V/'reference-hires.jpg').convert('RGB'))
tw,th=2048,64;u=np.linspace(523,712,tw);u=np.clip(u,528,707.8)
v=top(u)[None,:]+np.linspace(.035,.965,th)[:,None]*width(u)[None,:]
mx=np.tile(u*2000/708,(th,1)).astype('f4');my=(v*2.824).astype('f4')
strip=cv2.remap(photo,mx,my,cv2.INTER_CUBIC,borderMode=cv2.BORDER_REPLICATE)
fitmatrix=np.array(json.loads((R/'poster-right-facade-v54/surface-restoration-v54.json').read_text())['sourceBGRToGradedBGRMatrix'])
graded=np.clip(np.c_[strip[:,:,::-1].reshape(-1,3)/255,np.ones(tw*th)]@fitmatrix,0,1).reshape(th,tw,3)[:,:,::-1]
texture=(np.rint(graded*255)).astype('u1');Image.fromarray(texture).save(O/'right-bow-paint-v56.png')
uv=project(vertices).reshape(-1,12,2);lowerr=np.max(np.abs(np.min(uv[:,:,1]-top(uv[:,:,0]),axis=1)));upperr=np.max(np.abs(np.max(uv[:,:,1]-bottom(uv[:,:,0]),axis=1)))
report={'revision':56,'sourceNativeSha256':source['sourceNativeSha256'],'sourceReferenceSha256':hashlib.sha256((V/'reference-hires.jpg').read_bytes()).hexdigest(),
 'camera':source['camera'],'sourceObjects':[q for q in json.loads((O/'removal-v56.json').read_text()) if q['removedTriangles']],
 'name':'Poster measured right bowed I-beam v56','verticesNative':vertices.round(8).tolist(),'triangles':faces.tolist(),'faceSurfaceIndices':surface,
 'textureUV':texture_uv.tolist(),'centerlineNative':p.round(8).tolist(),'support':source['support'],'boundaryObservations708':stations.tolist(),
 'observationType':'Lower silhouette edge; upper edge follows measured local thickness of 3.25 to 3.6 pixels. Approximately 0.6 pixel boundary uncertainty.',
 'referenceCoordinateFrame':[708,1000],'inferredCylinderRadius':20.3,'inferredRadialSectionWidth':radial_width,'sectionDepthRangeMeters':[float(depth.min()),float(depth.max())],
 'webThicknessMeters':.024,'flangeThicknessMeters':.014,'surfaceMaterial':'Poster measured beam paint v56','texture':'right-bow-paint-v56.png',
 'textureSha256':hashlib.sha256((O/'right-bow-paint-v56.png').read_bytes()).hexdigest(),'signedVolume':float(vol),
 'maximumTopBoundaryErrorPixels':float(lowerr),'maximumBottomBoundaryErrorPixels':float(upperr),'closed':True,'oneToOneComplete':False,
 'limits':['Depth and unseen cross-section are inferred from the existing courtyard and support.', 'Hidden root and out-of-frame tip paint extend nearest visible colors. Reflected and oblique appearance still require review.']}
(O/'right-bow-geometry-v56.json').write_text(json.dumps(report,separators=(',',':')),encoding='utf-8')
ref=Image.open(O/'right-bow-reference-v56.png').convert('RGB');draw=ImageDraw.Draw(ref);xs=np.linspace(523,708,740)
for curve,color in [(top,(255,40,150)),(bottom,(20,220,250))]:draw.line([((u-500)*5,(float(curve(u))-570)*5) for u in xs],fill=color,width=1)
ref.save(O/'right-bow-boundary-fit-v56.png')
print(json.dumps({'triangles':len(faces),'closed':True,'depthRange':report['sectionDepthRangeMeters'],'maxUpperBoundaryError':float(lowerr),'maxLowerBoundaryError':float(upperr)},indent=2))
