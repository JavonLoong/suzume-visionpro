"""Joint foreground camera and complete circular courtyard fit.

Manual image landmarks are observations with uncertainty, not exact survey
data. Keep physical window heights shared and the circle radius at its source
scale, rather than hiding camera errors in an enlarged/stretched podium.
"""
from pathlib import Path
import json, math
import numpy as np
from scipy.optimize import least_squares

R=Path(__file__).parent; O=R/'movie-projection-v24'; O.mkdir(exist_ok=True)
W,H=2552,1656
pose=json.loads((R/'pose-calibration-v16.json').read_text(encoding='utf-8'))['measurements']
foreground=[]
for row in pose:
    if row['name']=='head_top': continue # Superseded by the independent head.
    foreground.append(dict(name=row['name'],world=row['world'],target=row['target'],sigma=22))
for name,p,t in [
    ('header left',[-.93341,-.161,3.8125],[923,226]),
    ('header right',[.93341,-.161,3.8125],[1541,226]),
    ('sill left',[-.86737,-.13,.20],[919,1454]),
    ('sill right',[.86737,-.13,.20],[1546,1454])]:
    foreground.append(dict(name=name,world=p,target=t,sigma=18))

# f, distance, cameraX, cameraZ, pitch, courtyardX/Y, window sill,
# arcade base, high roof, low roof, and six consecutive bay boundaries.
names=['lensMm','distance','cameraX','cameraZ','pitch','courtyardX','courtyardY',
       'windowSill','arcadeBase','highRoof','lowRoof']+[f'edge{i}' for i in range(12,18)]
init=[82,11,.15,2.85,.07,0,0,1.7,5.05,7.05,5.10,-.72,-.46,-.15,.06,.245,.51]
lower=[25,3,-.5,1.5,-.04,-10,-10,.8,4.2,6.1,4.2,-1.3,-.85,-.50,-.20,.03,.20]
upper=[160,24,.6,5,.20,10,10,2.5,6.5,8.5,6.5,-.3,-.18,.12,.38,.68,.94]

def project(a,q):
    a=np.asarray(a)-[q[2],-q[1],q[3]]
    x,y,z=a[...,0],a[...,1],a[...,2];c,s=np.cos(q[4]),np.sin(q[4])
    d=y*c-z*s;f=H*q[0]/36
    return np.stack((W/2+f*x/d,H/2-f*(y*s+z*c)/d),axis=-1)

def bay_basis(index,q):
    e=q[11:];lo,hi=e[index-12:index-10];a=(lo+hi)/2;r=23.5*np.cos((hi-lo)/2)
    return np.array([r*np.sin(a)+q[5],r*np.cos(a)+q[6],0]),np.array([np.cos(a),-np.sin(a),0])

def at_u(index,u,z,q,front=0):
    p,t=bay_basis(index,q);a=np.arctan2(-t[1],t[0]);p-=front*np.array([np.sin(a),np.cos(a),0]);p[2]=z
    rel=p-[q[2],-q[1],q[3]];f=H*q[0]/36;c,s=np.cos(q[4]),np.sin(q[4]);v=(u-W/2)/f
    x=(v*(rel[1]*c-rel[2]*s)-rel[0])/(t[0]-v*t[1]*c)
    return p+x*t

def observations(q):
    rows=[]
    for a in foreground:
        uv=project(a['world'],q)
        rows.append(dict(**a,projected=uv.tolist()))
    for idx,u,sigma in [(13,195,10),(14,892,10),(15,1430,40),(16,1908,10),(17,2544,20)]:
        angle=q[11+idx-12];p=[23.5*np.sin(angle)+q[5],23.5*np.cos(angle)+q[6],2.4]
        rows.append(dict(name=f'pier {idx}',target=[u,None],sigma=sigma,projected=project(p,q).tolist()))
    for idx,us,top in [(13,[259,420,470,648],441),(15,[1509,1668,1700,1858],440),(16,[1960,2230],444)]:
        for u in us:
            for z,v,name in [(q[7],674,'sill'),(q[7]+2.14,top,'top')]:
                rows.append(dict(name=f'bay {idx} window {name} at {u}',target=[None,v],sigma=10,projected=project(at_u(idx,u,z,q),q).tolist()))
    for idx,u,z,v,name,sigma in [
        (13,530,q[8],270,'arcade base',15),(15,1660,q[8],285,'arcade base',15),
        (13,530,q[9],56,'upper roof',20),(15,1660,q[9],56,'upper roof',25),
        (16,2230,q[10],277,'lower roof',15),
        (13,530,.05,860,'water contact',18),(16,2230,.05,855,'water contact',18)]:
        rows.append(dict(name=f'bay {idx} {name}',target=[None,v],sigma=sigma,projected=project(at_u(idx,u,z,q),q).tolist()))
    return rows

def residual(q):
    values=[]
    for a in observations(q):
        values.extend((a['projected'][i]-v)/a['sigma'] for i,v in enumerate(a['target']) if v is not None)
    values.extend([q[5]/8,q[6]/8,(q[7]-1.65)/.7,(q[8]-4.95)/1.0,(q[9]-6.9)/1.2,
                   (q[12]-q[11]-.235)/.04])
    for gap in np.diff(q[11:]): values.append(max(0,.09-gap)*100)
    values.append(max(0,np.hypot(q[5],q[6])-18)*10)
    return values

fit=least_squares(residual,init,bounds=(lower,upper),loss='soft_l1',f_scale=1.5,max_nfev=4000)
q=fit.x
rows=observations(q)
for r in rows:r['errorPixels']=float(np.linalg.norm([r['projected'][i]-v for i,v in enumerate(r['target']) if v is not None]))
result={'revision':24,'reference':'reference-opening-50525.jpg','dimensions':[W,H],
    'parameters':dict(zip(names,q.tolist())),'parameterVector':q.tolist(),'radius':23.5,
    'observations':rows,'foregroundMeanError':float(np.mean([r['errorPixels'] for r in rows[:len(foreground)]])),
    'backgroundMeanError':float(np.mean([r['errorPixels'] for r in rows[len(foreground):]])),
    'solverSuccess':bool(fit.success),'oneToOneComplete':False,
    'assumptions':['Circle radius 23.5 and common window height 2.14 set the architectural scale.',
       'Door corners and other landmarks are manually annotated; image reconstruction remains ambiguous.',
       'Camera has no roll or horizontal yaw; the courtyard is free to translate and its bay spans can change.',
       'Independent head is excluded from superseded v16 landmark data.'],
    'validationStatus':'Projection fit only; no claim of render improvement until candidate reviewed.'}
(O/'joint-fit-v24.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='observations'},indent=2))
print(json.dumps([{'name':r['name'],'uv':r['projected'],'error':r['errorPixels']} for r in rows],indent=2))

