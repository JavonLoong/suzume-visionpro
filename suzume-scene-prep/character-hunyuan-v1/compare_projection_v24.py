"""Comparable geometric observations, not an image-similarity score."""
import json,math,numpy as np
from projection_geometry_v24 import R,O,F
old=json.loads((R/'movie-calibration-v20/courtyard-fit-v20.json').read_text(encoding='utf-8'));p=old['parameters'];C=np.array(old['depthScaleCenter']);k=old['depthScale']
bays=json.loads((R/'movie-bays-v23/bay-fit-v23.json').read_text(encoding='utf-8'))['bays']
bays.append(dict(json.loads((R/'movie-windows-v21/window-fit-v21.json').read_text(encoding='utf-8')),index=16))
def projection(v):
    x,y,z=np.array(v)-C;c,s=np.cos(.01),np.sin(.01);d=y*c-z*s
    return np.array([1276+1380*x/d,828-1380*(y*s+z*c)/d])
def world(b,x,z,ground=False):
    a=b['angle']+p['yaw'];r=b['chordRadius'];v=np.array([r*np.sin(a)+x*np.cos(a)+p['translateX'],r*np.cos(a)-x*np.sin(a)+p['translateY'],z*p['heightScale']+p['heightOffset']]);v=C+k*(v-C)
    if ground:v[2]=.05
    return v
def at_u(b,u,z,ground=False):
    # The image is monotonic along a single facade; solve its horizontal ray.
    low,high=-12.,12.
    for _ in range(60):
        mid=(low+high)/2
        if projection(world(b,mid,z,ground))[0]<u:low=mid
        else:high=mid
    return projection(world(b,(low+high)/2,z,ground))
rows=[]
for obs in F['observations']:
    if 'world' in obs:
        uv=projection(obs['world']);target=np.array(obs['target']);before=float(np.linalg.norm(uv-target));rows.append({'name':obs['name'],'beforePixels':before,'afterPixels':obs['errorPixels']})
for index,u,z,target,label,ground in [(13,530,4.66,270,'arcade base',False),(15,1660,4.66,285,'arcade base',False),(13,530,6.52,56,'upper roof',False),(15,1660,6.52,56,'upper roof',False),(13,530,0,860,'water contact',True),(16,2230,0,855,'water contact',True)]:
    b=next(b for b in bays if b['index']==index);uv=at_u(b,u,z,ground);name=f'bay {index} {label}';a=next(a for a in F['observations'] if a['name']==name);rows.append({'name':name,'beforePixels':abs(float(uv[1]-target)),'afterPixels':a['errorPixels']})
result={'rows':rows,'foregroundMeanBefore':float(np.mean([r['beforePixels'] for r in rows[:12]])),'foregroundMeanAfter':float(np.mean([r['afterPixels'] for r in rows[:12]])),'selectedArchitectureMeanBefore':float(np.mean([r['beforePixels'] for r in rows[12:]])),'selectedArchitectureMeanAfter':float(np.mean([r['afterPixels'] for r in rows[12:]])),'notAWholeSceneFidelityScore':True,'oneToOneComplete':False}
(O/'projection-comparison-v24.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
