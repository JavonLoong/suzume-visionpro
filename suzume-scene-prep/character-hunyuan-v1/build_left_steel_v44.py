"""Trace complete left members, then lift and sweep closed steel sections."""
from pathlib import Path
import ast,json,hashlib,numpy as np
from scipy.interpolate import PchipInterpolator
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
R=Path(__file__).parent;O=R/'poster-left-steel-v44';V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
camera=json.loads((R/'poster-v38/restoration-v38.json').read_text())['posterCamera'];M=np.array(camera['matrixWorld']);C=M[:3,3];f=camera['lens']/36*1000
tree=ast.parse((R/'build_poster_steel_v39.py').read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['section','cap_triangles']],type_ignores=[]),'closed section helpers','exec'))
def project(p):
    q=(np.asarray(p)-C)@M[:3,:3];return np.c_[354+f*q[:,0]/-q[:,2],500-f*q[:,1]/-q[:,2]]
def lift(uv):
    uv=np.asarray(uv,float);ray=np.c_[(uv[:,0]-354)/f,(500-uv[:,1])/f,-np.ones(len(uv))]@M[:3,:3].T
    origin=(C-[0,0,5.75])/[20.3,20.3,12];direction=ray/[20.3,20.3,12];a=np.sum(direction**2,1);b=2*np.sum(direction*origin,1);c=np.dot(origin,origin)-1
    assert np.all(b*b-4*a*c>0);t=(-b+np.sqrt(b*b-4*a*c))/(2*a);p=C+t[:,None]*ray;below=p[:,2]<5.75
    aa=np.sum(ray[:,:2]**2,1);bb=2*np.sum(ray[:,:2]*C[:2],1);cc=np.dot(C[:2],C[:2])-20.3**2;tt=(-bb+np.sqrt(bb*bb-4*aa*cc))/(2*aa);p[below]=C+tt[below,None]*ray[below]
    return p
def corrugated_section(w,d,web,flange):
    low=-d/2+flange;high=d/2-flange
    band=np.array([low,low*.72,low*.45,low*.18,high*.15,high*.43,high*.70,high])
    center=np.array([0,.045,.045,-.040,-.040,.045,.045,0])
    shape=[[-w/2,-d/2],[w/2,-d/2],[w/2,low]]+[[a+web/2,b] for a,b in zip(center,band)]+[[w/2,high],[w/2,d/2],[-w/2,d/2],[-w/2,high]]+[[a-web/2,b] for a,b in zip(center[::-1],band[::-1])]+[[-w/2,low]]
    return np.array(shape)
def sweep(points,shape,name,kind,meta=None,taper=None):
    p=np.asarray(points);t=np.gradient(p,axis=0);t/=np.linalg.norm(t,axis=1)[:,None]
    if kind=='post':
        radial=np.c_[p[:,:2],np.zeros(len(p))];radial/=np.linalg.norm(radial,axis=1)[:,None];a=np.cross(radial,t);a/=np.linalg.norm(a,axis=1)[:,None];b=np.cross(t,a)
    else:
        a=np.c_[p[:,:2],np.zeros(len(p))];a-=np.sum(a*t,axis=1)[:,None]*t;a/=np.linalg.norm(a,axis=1)[:,None];b=np.cross(t,a);flip=b[:,2]<0;a[flip]*=-1;b[flip]*=-1
    scale=np.ones(len(p)) if taper is None else np.asarray(taper);offset=(a[:,None,:]*shape[None,:,0,None]+b[:,None,:]*shape[None,:,1,None])*scale[:,None,None];v=(p[:,None,:]+offset).reshape(-1,3);faces=[];roles=[];n=len(shape)
    if name=='outer splayed I-column':
        # The photographed broken end is nearly level across the corrugated
        # section. Blend an axial warp into that measured oblique cut plane.
        slope=.19;target_v=360.5;target_u=42;k=(500-target_v-slope*(354-target_u))/f;normal=M[:3,1]+slope*M[:3,0]+k*M[:3,2]
        cut_shift=-((v-np.repeat(p,n,axis=0))@normal)/np.repeat(t@normal,n)
        center_v=project(p)[:,1];blend=np.clip((405-center_v)/(405-target_v),0,1);blend=blend*blend*(3-2*blend)
        v+=np.repeat(t,n,axis=0)*(cut_shift*np.repeat(blend,n))[:,None]
    for j in range(len(p)-1):
        for k in range(n):
            x=j*n+k;y=j*n+(k+1)%n;faces.extend([[x,y,y+n],[x,y+n,x+n]])
            if n==12:role=1 if k in [1,5,7,11] else (2 if k in [3,9] else 0)
            else:role=1 if (np.linalg.norm(shape[(k+1)%n]-shape[k])<.065 or k in [4,8,17,21]) else (2 if k in [5,7,18,20] else 0)
            roles.extend([role,role])
    for tri in cap_triangles(shape):faces.append(tri[::-1]);faces.append([k+(len(p)-1)*n for k in tri]);roles.extend([2,2])
    faces=np.array(faces);volume=np.einsum('ij,ij->i',v[faces[:,0]],np.cross(v[faces[:,1]],v[faces[:,2]])).sum()/6
    if volume<0:faces=faces[:,::-1];volume=-volume
    edges=np.sort(np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]),axis=1);_,counts=np.unique(edges,axis=0,return_counts=True);assert np.all(counts==2) and volume>0
    return {'name':'Poster left '+name+' v44','kind':kind,'verticesNative':v.round(7).tolist(),'triangles':faces.tolist(),'materialIndices':roles,'centerlineNative':p.round(7).tolist(),'section':shape.tolist(),'signedVolume':float(volume),'closed':True,**(meta or {})}
members=[]
posts=[('outer splayed I-column',[[42,360.5],[38,375],[32.5,390],[29.7,400],[23,425],[16,450],[8,480],[-.5,510],[-12,553],[-23,600],[-34,650],[-42,704]],.19,.83),('middle bowed I-column',[[180,473],[178.6,491],[176,522],[175.5,546],[172.5,572],[171,602],[168,637],[166.4,670],[166,701]],.23,.33),('back I-column',[[261.5,488],[262.4,520],[263.3,552],[262.8,582],[264.4,617],[263.8,657],[263.5,703]],.235,.34)]
for index,(name,pixels,w,d) in enumerate(posts):
    uv=np.array(pixels,float);height=np.linspace(uv[-1,1],uv[0,1],170);path=np.c_[PchipInterpolator(uv[:,1],uv[:,0])(height),height];p=lift(path);scale=np.ones(len(p))
    if index==0:scale=1+.24*np.clip((400-height)/39.5,0,1)
    meta={'referencePixels708':pixels,'measurementUncertaintyPixels':1.5,'tipSplayInferredFromVisibleWidth':index==0,'referenceDepthInferred':True}
    shape=section(w,d,.032,.035) if index else corrugated_section(w,d,.033,.037)
    rec=sweep(p,shape,name,'post',meta,scale);members.append(rec)
    base=p[0].copy();cap=max(.24,float(base[2])+.04);foot=sweep([[base[0],base[1],-.15],[base[0],base[1],cap]],np.array([[-.25,-.25],[.25,-.25],[.25,.25],[-.25,.25]]),name+' footing','post',{'foundation':True});foot['materialIndices']=[3]*len(foot['triangles']);members.append(foot)
observed=[
 ('upper broken tie',[[-36,403],[0,411],[29,419],[59,425],[86,429],[112,432]],.27,.22,.028,.035,'beam'),
 ('long upper tie',[[-42,451],[0,463],[60,474],[120,483],[178,489],[221,491],[264,493]],.28,.21,.028,.032,'beam'),
 ('long lower tie',[[-40,505],[0,514],[65,524],[124,530],[175,534],[220,536],[264,538]],.29,.24,.028,.036,'beam'),
 ('upper right curved bracket',[[16,449],[24,439],[38,431],[57,426],[79,427]],.075,.067,.014,.016,'brace'),
 ('upper left curved bracket',[[21,431],[9,427],[-5,425],[-20,424]],.075,.067,.014,.016,'brace'),
 ('upper cross brace',[[-9,425],[14,429],[39,434]],.058,.052,.012,.015,'brace'),
 ('upper left diagonal',[[-3,428],[13,416]],.050,.047,.012,.013,'brace'),
 ('upper center diagonal',[[29,419],[39,434]],.050,.047,.012,.013,'brace'),
 ('upper right upright',[[45,423],[40,434]],.050,.047,.012,.013,'brace'),
 ('first broken bowed beam',[[43,610],[62,599],[91,587],[122,580],[148,578],[171,579],[184,582]],.33,.205,.047,.031,'beam'),
 ('second broken bowed beam',[[151,610],[173,597],[194,587],[217,581.5],[242,582],[262,585],[274,590]],.32,.205,.047,.031,'beam'),
 ('hanging upper rod',[[43,471],[41,483],[39,500],[35,518]],.025,.025,.007,.007,'hanger'),
 ('first bowed upright',[[58,560],[59,574],[63,588],[67,597]],.04,.052,.010,.012,'hanger'),
 ('second bowed upright',[[120,560],[121,571],[124,580]],.035,.046,.010,.011,'hanger'),
]
attachments={
 'upper right curved bracket':[(0,'outer splayed I-column'),(-1,'upper broken tie')],
 'upper left curved bracket':[(0,'outer splayed I-column')],
 'upper cross brace':[(-1,'upper right curved bracket')],
 'upper left diagonal':[(0,'upper cross brace'),(-1,'upper broken tie')],
 'upper center diagonal':[(0,'upper broken tie'),(-1,'upper cross brace')],
 'upper right upright':[(0,'upper broken tie'),(-1,'upper cross brace')],
 'hanging upper rod':[(0,'long upper tie'),(-1,'long lower tie')],
 'first bowed upright':[(-1,'first broken bowed beam')],
 'second bowed upright':[(-1,'first broken bowed beam')]
}
for name,pixels,w,d,web,flange,kind in observed:
    uv=np.array(pixels,float);t=np.r_[0,np.cumsum(np.linalg.norm(np.diff(uv,axis=0),axis=1))];t/=t[-1];count=max(12,int(np.linalg.norm(np.diff(uv,axis=0),axis=1).sum()/2));curve=PchipInterpolator(t,uv,axis=0)(np.linspace(0,1,count));p=lift(curve);extensions=[]
    for endpoint,target in attachments.get(name,[]):
        other=np.array(next(q['centerlineNative'] for q in members if q['name']=='Poster left '+target+' v44'));delta=other-p[endpoint];nearest=other[np.argmin(np.linalg.norm(delta,axis=1))];length=np.linalg.norm(nearest-p[endpoint]);extensions.append({'endpoint':endpoint,'target':'Poster left '+target+' v44','extensionMeters':float(length)})
        p=np.vstack([nearest,p]) if endpoint==0 else np.vstack([p,nearest])
    members.append(sweep(p,section(w,d,web,flange),name,kind,{'referencePixels708':pixels,'measurementUncertaintyPixels':1.5,'weldExtensions':extensions,'referenceDepthInferred':True}))
report={'revision':44,'sourceNativeSha256':json.loads((O/'source-steel-v44.json').read_text())['sourceNativeSha256'],'camera':camera,'reference':'reference-hires.jpg','referenceCoordinateFrame':[708,1000],'members':members,'triangles':sum(len(q['triangles']) for q in members),'scope':'Complete observed left-member centerlines and closed swept sections. Depth follows an inferred dome/cylinder; unseen section detail, joint weathering and footing extents remain inferred.','oneToOneComplete':False}
(O/'steel-geometry-v44.json').write_text(json.dumps(report,separators=(',',':')),encoding='utf-8')
fig,ax=plt.subplots(figsize=(8,11));ax.imshow(Image.open(V/'reference-hires.jpg').resize((708,1000)))
for q in members:
    uv=project(q['centerlineNative']);ax.plot(uv[:,0],uv[:,1],lw=1,color='#ff3892' if q['kind']=='post' else '#18ff8b',alpha=.8)
ax.set_xlim(-12,300);ax.set_ylim(725,340);ax.set_title('Reference / reconstructed member centerlines');fig.tight_layout();fig.savefig(O/'new-centerlines-v44.png',dpi=150)
print('LEFT_STEEL_44_BUILT',len(members),report['triangles'],flush=True)
