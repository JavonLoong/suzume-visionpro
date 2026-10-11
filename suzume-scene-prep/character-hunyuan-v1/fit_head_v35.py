"""Fit a true volumetric head to manually read movie silhouette landmarks.

All coordinates below are in the original 2552 x 1656 movie reference. These
few manually read outlines are constraints, not evidence of whole-model fidelity.
"""
from pathlib import Path
import json,numpy as np
from scipy.optimize import least_squares
from scipy.interpolate import PchipInterpolator
R=Path(__file__).parent;O=R/'movie-head-v35';a=np.load(O/'head-source-v35.npz')
w=a['world'];local=a['local'];faces=a['faces'];groups=json.loads((O/'groups-v35.json').read_text())
C=np.array([.15354844661181763,-11.7300315454759,2.8782074998654252]);pitch=.07098138634927482
forward=np.array([0,np.cos(pitch),-np.sin(pitch)]);up=np.array([0,np.sin(pitch),np.cos(pitch)]);f=86.54434612692005/36*1656
def project(v):
 d=v-C;depth=d@forward
 return np.column_stack([1276+f*d[:,0]/depth,828-f*(d@up)/depth])
def unproject(uv,depth):return C+depth[:,None]*forward+(uv[:,0]-1276)[:,None]*depth[:,None]/f*np.array([1,0,0])+(828-uv[:,1])[:,None]*depth[:,None]/f*up
cap=np.array(groups['Head part :: Smooth hair cap']);neck=np.array(groups['Head part :: Clean neck']);pony=np.array(sorted(i for k,ids in groups.items() if 'Solid ponytail lock' in k for i in ids));pm=np.zeros(len(w),bool);pm[pony]=True
pivot=w[cap].mean(axis=0)
target_cap=np.array([1127,1222,515,635.])
def transform(v,p):return (v-pivot)*np.array([p[0],.90,p[1]])+pivot+np.array([p[2],0,p[3]])
def cap_bounds(v):
 u=project(v[cap]);return np.array([u[:,0].min(),u[:,0].max(),u[:,1].min(),u[:,1].max()])
fit=least_squares(lambda p:cap_bounds(transform(w,p))-target_cap,[.86,.90,-.02,-.08],bounds=([.75,.75,-.1,-.2],[1.05,1.05,.1,.05]),xtol=1e-12,ftol=1e-12,gtol=1e-12)
after=transform(w,fit.x)
# Blend only the neck attachment. Its bottom ring remains exactly at the collar.
z=local[neck,2];t=np.clip((z-z.min())/(np.quantile(z,.68)-z.min()),0,1);t=t*t*(3-2*t)
after[neck]=w[neck]+(after[neck]-w[neck])*t[:,None]
# The reference tufts rise above the scalp. Keep their attachment fixed while
# lengthening the existing closed geometry, rather than adding a camera card.
tuft_targets={'First small crown tuft':493.0,'Second small crown tuft':501.5}
for name,top in tuft_targets.items():
 ids=np.array(groups['Head part :: '+name]);uv=project(after[ids]);vmin,vmax=uv[:,1].min(),uv[:,1].max();t=np.clip((vmax-uv[:,1])/(vmax-vmin),0,1);uv[:,1]-=(vmin-top)*t**1.2;after[ids]=unproject(uv,(after[ids]-C)@forward)
# A measured outline at multiple heights: a narrow root, broad shoulder-length
# middle, one short left point, and the long central tip.
outline=np.array([
 [542,1176.5,1176.5],[543,1171,1182],[546,1168,1185],
 [550,1166.5,1187],[560,1165,1188.5],[575,1163.5,1190.5],
 [600,1161.5,1193.5],[625,1158,1197],[650,1156,1201],
 [675,1156,1202],[690,1156,1202],[705,1156,1202],
 [720,1156,1202],[726,1157,1201],[731,1159,1199.5],
 [734,1165.5,1198.5],[740,1170,1196],[750,1175,1190],
 [760,1179.5,1187],[765,1182,1185],[772,1183.5,1183.5]
],float)
uv=project(after);depth=(after-C)@forward
vmin,vmax=uv[pony,1].min(),uv[pony,1].max();source_rows=542+(uv[pony,1]-vmin)/(vmax-vmin)*(772-542)
# Sweep closed overlapping volumes instead of stretching disconnected surface
# strands to the envelope. The core keeps the middle filled in every view.
sample_rows=np.linspace(542,772,12);sample_depth=[]
for row in sample_rows:
 nearest=np.argsort(abs(source_rows-row))[:160];sample_depth.append(float(np.median(depth[pony[nearest]])))
center_depth=PchipInterpolator(sample_rows,sample_depth)
core=outline.copy();core[core[:,0]==705,1]=1158;core[core[:,0]==720,1]=1164;core[core[:,0]==726,1]=1164.3;core[core[:,0]==731,1]=1164.8
left=PchipInterpolator(core[:,0],core[:,1]);right=PchipInterpolator(core[:,0],core[:,2])
short_profile=np.array([[542,1176.5,.08],[560,1171,6],[600,1169,7.5],[650,1168,12],[690,1168,12],[705,1166,10],[720,1164,8],[726,1161,4],[731,1160.2,1.2],[733,1159.5,.08]])
short_center=PchipInterpolator(short_profile[:,0],short_profile[:,1]);short_radius=PchipInterpolator(short_profile[:,0],short_profile[:,2])
for k in range(6):
 ids=np.array(groups['Head part :: Solid ponytail lock '+str(k)]);assert len(ids)==48*20
 rows=np.linspace(542,733 if k==0 else 772,48);params=np.linspace(0,1,48);verts=[]
 for row,t in zip(rows,params):
  lo,hi=float(left(row)),float(right(row));mid=(lo+hi)/2;half=max(.08,(hi-lo)/2);radius_depth=.036*np.sin(np.pi*t)**.40+.0004
  if k==0:mid=float(short_center(row));half=float(short_radius(row));radius_depth*=.75;depth_offset=-.013*np.sin(np.pi*t)
  elif k==5:depth_offset=0
  else:
   # Four shallow overlapping lobes add physical strand relief to the core.
   side=-1 if k in [1,2] else 1;mid+=side*.40*half;half*=.60
   depth_offset=(-1 if k in [1,3] else 1)*radius_depth*.62;radius_depth*=.66
  for j in range(20):
   angle=2*np.pi*j/20;u=mid+half*np.cos(angle);dep=float(center_depth(row))+depth_offset+radius_depth*np.sin(angle)
   verts.append(unproject(np.array([[u,row]]),np.array([dep]))[0])
 after[ids]=verts
uv=project(after)
pf=faces[np.all(pm[faces],axis=1)]
def contour_at_rows(uv,rows):
 tri=uv[pf];starts=tri.reshape(-1,2);ends=np.roll(tri,-1,axis=1).reshape(-1,2);y0=starts[:,1];y1=ends[:,1];dy=y1-y0;valid=abs(dy)>1e-9
 out=[]
 for y in rows:
  ok=valid&(y>=np.minimum(y0,y1)-1e-8)&(y<=np.maximum(y0,y1)+1e-8)
  xs=starts[ok,0]+(y-y0[ok])*(ends[ok,0]-starts[ok,0])/dy[ok]
  out.append([xs.min(),xs.max()] if len(xs) else [np.nan,np.nan])
 return np.array(out)
check_rows=outline[3:-1,0];actual=contour_at_rows(project(after),check_rows);desired=outline[3:-1,1:];err=np.abs(actual-desired)
np.savez_compressed(O/'head-fit-v35.npz',before=w,after=after,ponytailMask=pm)
report={'revision':35,'reference':'reference-opening-50525.jpg','referenceSize':[2552,1656],'landmarkUncertaintyPixels':3,'capBoundsBefore':cap_bounds(w).tolist(),'capBoundsTarget':target_cap.tolist(),'capBoundsFitted':cap_bounds(after).tolist(),'headScaleXYZ':[float(fit.x[0]),.9,float(fit.x[1])],'headTranslationXZ':fit.x[2:].tolist(),'neckBottomPreserved':True,'tuftTopTargets':tuft_targets,'ponytailOutlineTargets':outline.tolist(),'ponytailRowMeasurements':np.column_stack([check_rows,actual,desired,err]).tolist(),'maximumPonytailBoundaryResidualPixels':float(err.max()),'completeOneToOne':False}
(O/'fit-v35.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
