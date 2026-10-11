"""Lift observed poster members onto the existing dome and build closed sections."""
from pathlib import Path
import json,math,numpy as np
from scipy.interpolate import PchipInterpolator
R=Path(__file__).parent;O=R/'poster-steel-v39';O.mkdir(exist_ok=True)
V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
camera=json.loads((R/'poster-v38/restoration-v38.json').read_text())['posterCamera'];M=np.array(camera['matrixWorld']);C=M[:3,3];f=camera['lens']/36*2824
cal=json.loads((V/'dome-calibration-v7.json').read_text())
inner_pixels=np.array([[1404,1027],[1415,1120],[1434,1238],[1450,1352],[1462,1480],[1472,1620],[1478,1745],[1483,1870],[1483,1970]],float)
outer_pixels=np.array([[1647,712],[1678,800],[1712,900],[1749,1000],[1784,1100],[1812,1200],[1840,1300],[1864,1400],[1885,1500],[1898,1600],[1898,1620]],float)
inner_x=PchipInterpolator(inner_pixels[:,1],inner_pixels[:,0],extrapolate=True)
outer_x=PchipInterpolator(outer_pixels[:,1],outer_pixels[:,0],extrapolate=True)
def project(p):
    q=(np.asarray(p)-C)@M[:3,:3];return np.stack([1000+f*q[...,0]/-q[...,2],1412-f*q[...,1]/-q[...,2]],axis=-1)
def raw_lift(uv):
    uv=np.asarray(uv);q=np.c_[(uv[:,0]-1000)/f,(1412-uv[:,1])/f,-np.ones(len(uv))]@M[:3,:3].T
    origin=(C-[0,0,5.75])/[20.3,20.3,12];ray=q/[20.3,20.3,12]
    a=np.sum(ray*ray,axis=1);b=2*np.sum(ray*origin,axis=1);c=np.dot(origin,origin)-1
    t=(-b+np.sqrt(b*b-4*a*c))/(2*a)
    p=C+t[:,None]*q
    below=p[:,2]<5.75
    if below.any():
        aa=np.sum(q[:,:2]*q[:,:2],axis=1);bb=2*np.sum(q[:,:2]*C[:2],axis=1);cc=np.dot(C[:2],C[:2])-20.3**2
        tc=(-bb+np.sqrt(bb*bb-4*aa*cc))/(2*aa);p[below]=C+tc[below,None]*q[below]
    return p
roof=next(q for q in json.loads((O/'roof-attachment-v39.json').read_text()) if q['pixel']==[1898,1620])
roof_distance=np.linalg.norm(np.array(roof['roofWorld'])-C)+.22
outer_depth_offset=roof_distance-np.linalg.norm(raw_lift([[1898,1620]])[0]-C)
def lift(uv):
    uv=np.asarray(uv,float);p=raw_lift(uv);ray=p-C;ray/=np.linalg.norm(ray,axis=1)[:,None]
    # A common depth field keeps all observed members together. The outer rib
    # seats inside the actual roof mesh hit, rather than ending in mid-air.
    v=uv[:,1];left=inner_x(v);right=outer_x(v);weight=np.clip((uv[:,0]-left)/np.maximum(right-left,80),0,1)
    down=np.clip((v-712)/(1620-712),0,1)**1.5
    return p+ray*(weight*down*outer_depth_offset)[:,None]
def section(w,d,web,flange):
    return np.array([[-w/2,-d/2],[w/2,-d/2],[w/2,-d/2+flange],[web/2,-d/2+flange],[web/2,d/2-flange],[w/2,d/2-flange],[w/2,d/2],[-w/2,d/2],[-w/2,d/2-flange],[-web/2,d/2-flange],[-web/2,-d/2+flange],[-w/2,-d/2+flange]])
def cap_triangles(shape):
    ids=list(range(len(shape)));tri=[]
    cross=lambda a,b:float(a[0]*b[1]-a[1]*b[0])
    while len(ids)>3:
        found=False
        for j,b in enumerate(ids):
            a=ids[j-1];c=ids[(j+1)%len(ids)]
            if cross(shape[b]-shape[a],shape[c]-shape[b])<=1e-12:continue
            inside=False
            for k in ids:
                if k in [a,b,c]:continue
                signs=[cross(shape[y]-shape[x],shape[k]-shape[x]) for x,y in [(a,b),(b,c),(c,a)]]
                if min(signs)>=-1e-12:inside=True;break
            if inside:continue
            tri.append([a,b,c]);ids.pop(j);found=True;break
        assert found,'Invalid section triangulation'
    return tri+[ids]
def geometry(points,shape,name,kind,metadata=None):
    p=np.asarray(points);t=np.gradient(p,axis=0);t/=np.linalg.norm(t,axis=1)[:,None]
    if kind=='post':
        normal=np.c_[p[:,:2],np.zeros(len(p))];normal/=np.linalg.norm(normal,axis=1)[:,None]
        a=np.cross(normal,t);a/=np.linalg.norm(a,axis=1)[:,None];b=np.cross(t,a)
    else:
        a=np.c_[p[:,:2],np.zeros(len(p))];a-=np.sum(a*t,axis=1)[:,None]*t;a/=np.linalg.norm(a,axis=1)[:,None];b=np.cross(t,a)
        reverse=b[:,2]<0;a[reverse]*=-1;b[reverse]*=-1
    vertices=(p[:,None,:]+a[:,None,:]*shape[None,:,0,None]+b[:,None,:]*shape[None,:,1,None]).reshape(-1,3)
    faces=[];roles=[];n=len(shape)
    for j in range(len(p)-1):
        for k in range(n):
            aa=j*n+k;bb=j*n+(k+1)%n;faces.extend([[aa,bb,bb+n],[aa,bb+n,aa+n]])
            # Flange edge paint is an actual exposed steel surface.
            role=1 if n==12 and k in [1,5,7,11] else (2 if n==12 and k in [3,9] else 0)
            roles.extend([role,role])
    for q in cap_triangles(shape):faces.append(q[::-1]);faces.append([k+(len(p)-1)*n for k in q]);roles.extend([2,2])
    faces=np.array(faces);vol=np.einsum('ij,ij->i',vertices[faces[:,0]],np.cross(vertices[faces[:,1]],vertices[faces[:,2]])).sum()/6
    if vol<0:faces=faces[:,::-1];vol=-vol
    edges=np.sort(np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]),axis=1);_,counts=np.unique(edges,axis=0,return_counts=True);assert np.all(counts==2)
    return {'name':name,'kind':kind,'verticesNative':vertices.round(7).tolist(),'triangles':faces.tolist(),'materialIndices':roles,'centerlineNative':p.round(7).tolist(),'section':shape.tolist(),'signedVolume':float(vol),'closed':True,**(metadata or {})}
members=[]
for i in [2,3]:
    uv=inner_pixels if i==2 else outer_pixels
    heights=np.linspace(uv[-1,1],uv[0,1],160);curve=np.c_[PchipInterpolator(uv[:,1],uv[:,0])(heights),heights];points=lift(curve)
    members.append(geometry(points,section(.23,.34,.027,.032),'Poster right I-section post '+str(i),'post',{'ribIndex':i,'referencePixels':uv.tolist(),'liftedReferencePoints':lift(uv).round(7).tolist(),'tipReference':uv[0].tolist(),'rootMode':'grounded footing' if i==2 else 'inside existing roof mesh','measurementUncertaintyPixels':4}))
root=np.array(members[0]['centerlineNative'][0]);foot=geometry([[root[0],root[1],-.22],[root[0],root[1],root[2]]],np.array([[-.25,-.25],[.25,-.25],[.25,.25],[-.25,.25]]),'Poster inner grounded footing','post',{'foundation':True})
foot['materialIndices']=[3]*len(foot['triangles']);members.append(foot)
observed=[
 ('Upper continuous tie',[[1420,1092],[1510,1070],[1630,1040],[1755,1006],[1850,981],[1925,968],[2030,976]],.23,.17,.024,.025,'beam'),
 ('Bent broken central beam',[[1214,1364],[1241,1334],[1268,1296],[1286,1255],[1294,1252],[1420,1234],[1540,1213],[1680,1183],[1810,1153],[1894,1146],[2010,1155]],.28,.19,.025,.03,'beam'),
 ('Short broken right tie',[[1703,1325],[1736,1323],[1775,1315],[1850,1302],[1940,1282],[2030,1259]],.22,.15,.022,.023,'beam'),
 ('Lower broken ring beam',[[1320,1501],[1340,1499],[1380,1503],[1475,1496],[1600,1481],[1750,1460],[1880,1437],[2020,1412]],.24,.145,.022,.024,'beam'),
 ('Curved left supporting bracket',[[1443,1352],[1424,1327],[1388,1295],[1348,1273],[1305,1255]],.09,.07,.014,.015,'brace'),
 ('Curved right supporting bracket',[[1443,1352],[1455,1321],[1474,1291],[1508,1257],[1554,1221],[1576,1208]],.09,.07,.014,.015,'brace'),
 ('Bracket horizontal brace',[[1388,1287],[1440,1283],[1486,1278]],.055,.05,.012,.013,'brace'),
 ('Bracket left upright',[[1377,1256],[1380,1284]],.05,.05,.011,.013,'brace'),
 ('Bracket diagonal brace',[[1382,1284],[1410,1252]],.055,.05,.012,.013,'brace'),
 ('Bracket right diagonal',[[1456,1244],[1486,1268]],.055,.05,.012,.013,'brace'),
 ('Bracket right upright',[[1480,1247],[1487,1266]],.05,.05,.011,.013,'brace'),
 ('Hanging central tie',[[1708,1189],[1719,1230],[1731,1270],[1735,1301]],.026,.024,.007,.007,'hanger'),
 ('Hanging lower tie',[[1541,1506],[1545,1552],[1547,1610]],.026,.024,.007,.007,'hanger'),
]
for name,pixels,w,d,web,flange,kind in observed:
    uv=np.asarray(pixels,float);q=np.r_[0,np.cumsum(np.linalg.norm(np.diff(uv,axis=0),axis=1))];q/=q[-1]
    n=max(8,int(np.linalg.norm(np.diff(uv,axis=0),axis=1).sum()/5));uvs=PchipInterpolator(q,uv,axis=0)(np.linspace(0,1,n))
    points=lift(uvs)
    attachments={
        'Curved left supporting bracket':[(0,'right I-section post 2')],
        'Bracket horizontal brace':[(0,'Curved left supporting bracket'),(-1,'Curved right supporting bracket')],
        'Bracket left upright':[(0,'Bent broken central beam'),(-1,'Bracket horizontal brace')],
        'Bracket diagonal brace':[(0,'Bracket horizontal brace'),(-1,'Bent broken central beam')],
        'Bracket right diagonal':[(0,'Bent broken central beam'),(-1,'Curved right supporting bracket')],
        'Bracket right upright':[(0,'Bent broken central beam'),(-1,'Curved right supporting bracket')],
        'Hanging central tie':[(0,'Bent broken central beam')],
        'Hanging lower tie':[(0,'Lower broken ring beam')],
    }
    corrections=[]
    for endpoint,target in attachments.get(name,[]):
        center=np.array(next(q['centerlineNative'] for q in members if q['name']=='Poster '+target));p=points[endpoint].copy();best=center[np.argmin(np.linalg.norm(center-p,axis=1))]
        # Extend inside the solid that receives the weld; the exposed part of
        # a hanger starts at the beam surface, not at its internal endpoint.
        if endpoint==0:points=np.vstack([best,points])
        else:points=np.vstack([points,best])
        corrections.append({'endpoint':endpoint,'target':target,'extensionMeters':float(np.linalg.norm(best-p)),'projectedExtensionPixels':float(np.linalg.norm(project([best])[0]-project([p])[0]))})
    rec=geometry(points,section(w,d,web,flange),'Poster '+name,kind,{'referencePixels':pixels,'liftedReferencePoints':lift(uv).round(7).tolist(),'measurementUncertaintyPixels':4,'weldExtensions':corrections})
    rec['referenceRoundtripMaximumPixels']=float(np.max(np.linalg.norm(project(lift(uv))-uv,axis=1)));members.append(rec)
out={'revision':39,'sourceNative':'poster-v38/Suzume_dual_scene_v38.blend','reference':'reference-hires.jpg','referenceDimensions':[2000,2824],'camera':camera,'domeRadius':20.3,'domeRise':12,'domeSpringHeight':5.75,'outerDepthAdjustmentMeters':outer_depth_offset,'outerRoofAttachment':roof,'replacementRibIndices':[2,3],'removeRingAngularInterval':[cal['angles'][2],cal['angles'][3]],'members':members,'limits':['Centerline image observations constrain projections; depth starts from the inferred dome and moves the outer rib onto the existing roof.','Occluded contact details and weathering remain approximations.'],'oneToOneComplete':False}
(O/'steel-geometry-v39.json').write_text(json.dumps(out,separators=(',',':')),encoding='utf-8')
print(json.dumps({'members':len(members),'triangles':sum(len(m['triangles']) for m in members),'closed':all(m['closed'] for m in members),'maxReferenceRoundtrip':max(m.get('referenceRoundtripMaximumPixels',0) for m in members)},indent=2))
