from pathlib import Path
import json,numpy as np,trimesh
from scipy.optimize import least_squares

R=Path(__file__).parent;O=R/'poster-rooftops-v45';S=json.loads((O/'source-rooftops-v45.json').read_text());C=np.array(S['camera']['position']);rot=np.array(S['camera']['rotation']);f=S['camera']['focalPixels']
def project(v):
    q=(np.array(v)-C)@rot;return np.stack((354+f*q[...,0]/-q[...,2],500-f*q[...,1]/-q[...,2]),axis=-1)
def plane(u,radius):
    ray=np.array([(u-354)/f,0,-1])@rot.T
    aa=np.dot(ray[:2],ray[:2]);bb=2*np.dot(C[:2],ray[:2]);cc=np.dot(C[:2],C[:2])-radius**2;t=(-bb+np.sqrt(bb*bb-4*aa*cc))/(2*aa)
    p=C+t*ray;return float(np.arctan2(p[0],p[1]))
records=[];fitrecords=[]
def frame(angle,radius=24.25):
    radial=np.array([np.sin(angle),np.cos(angle),0]);tangent=np.array([np.cos(angle),-np.sin(angle),0]);up=np.array([0,0,1]);return radial*radius,np.stack([tangent,radial,up],axis=1)
def add(name,parts,origin,matrix):
    vs=[];fs=[];mi=[];offset=0
    for mesh,material in parts:
        mesh.fix_normals();vs.append(np.asarray(mesh.vertices)@matrix.T+origin);fs.append(np.asarray(mesh.faces)+offset);mi.extend([material]*len(mesh.faces));offset+=len(mesh.vertices)
    v=np.concatenate(vs);faces=np.concatenate(fs);records.append({'name':'Poster rooftop '+name+' v45','verticesNative':v.round(8).tolist(),'triangles':faces.tolist(),'materialIndices':mi,'parts':len(parts),'boundsImage':[project(v).min(0).tolist(),project(v).max(0).tolist()]})
def box(size,position,material):
    m=trimesh.creation.box(extents=size);m.apply_translation(position);return m,material
def rod(a,b,radius,material=2,sections=12):
    a=np.array(a);b=np.array(b);m=trimesh.creation.cylinder(radius=radius,segment=np.array([a,b]),sections=sections);return m,material
def lathe(profile,center=(0,0,0),material=0,n=64):
    # Closed solid of revolution. End disks are explicit and use single centers.
    verts=[]
    for rad,z in profile:
        for k in range(n):
            angle=2*np.pi*k/n;verts.append([center[0]+rad*np.cos(angle),center[1]+rad*np.sin(angle),center[2]+z])
    faces=[]
    for j in range(len(profile)-1):
        for k in range(n):
            a=j*n+k;b=j*n+(k+1)%n;c=(j+1)*n+(k+1)%n;d=(j+1)*n+k;faces.extend([[a,b,c],[a,c,d]])
    for j,reverse in [(0,True),(len(profile)-1,False)]:
        ci=len(verts);verts.append([center[0],center[1],center[2]+profile[j][1]])
        for k in range(n):
            a=j*n+k;b=j*n+(k+1)%n;faces.append([ci,b,a] if reverse else [ci,a,b])
    m=trimesh.Trimesh(vertices=verts,faces=faces,process=False);m.fix_normals();assert m.is_watertight;return m,material
def shed(label,targets,depth):
    target=np.array(targets,float);guess=[plane(target[:,0].mean(),24.25),2.8,8.6]
    def corners(x):
        a,w,h=x;origin,M=frame(a);return np.array([[-w/2,0,h],[w/2,0,h]])@M.T+origin
    fit=least_squares(lambda x:(project(corners(x))-target).ravel(),guess,xtol=1e-13,ftol=1e-13,gtol=1e-13)
    angle,width,top=fit.x;origin,M=frame(angle);base=6.50;height=top-base;parts=[box([width,depth,height],[0,depth/2,base+height/2],0)]
    # Thin capping, vertical seam ribs, and a small base curb are actual solids.
    parts += [box([width+.07,depth+.07,.09],[0,depth/2,top+.025],1),box([width+.08,depth+.06,.10],[0,depth/2,base+.015],1)]
    for x in [-width/2+.035,-width*.06,width/2-.035]:parts.append(box([.037,.065,height],[x,-.030,base+height/2],1))
    # Ladder rises past the cap, with feet continuing down onto the roof.
    lx=-width*.29;ladder_y=-.13
    for x in [lx-.16,lx+.16]:parts.append(rod([x,ladder_y,6.50],[x,ladder_y,top+.28],.017,2))
    for z in np.arange(6.57,top+.08,.25):parts.append(rod([lx-.17,ladder_y,z],[lx+.17,ladder_y,z],.013,2))
    for z in [6.65,top-.20]:
        for x in [lx-.16,lx+.16]:parts.append(rod([x,ladder_y,z],[x,.02,z],.013,2))
    # A visible right-side pipe emerges at the upper corner and bends down.
    x=width/2+.07;y=depth*.46
    path=[[width/2-.02,y,top-.17],[x+.16,y,top-.17],[x+.30,y,top-.25],[x+.40,y,top-.42],[x+.40,y,6.51]]
    for a,b in zip(path[:-1],path[1:]):parts.append(rod(a,b,.075,2))
    if label=='right service house':parts=[(mesh,3 if material==0 else material) for mesh,material in parts]
    add(label,parts,origin,M);fitrecords.append({'name':label,'observedTopFrontCorners708x1000':targets,'fittedTopCorners':project(corners(fit.x)).tolist(),'pixelRMS':float(np.sqrt(np.mean(fit.fun**2))),'angle':float(angle),'widthMeters':float(width),'topNativeZ':float(top),'frontRadiusMeters':24.25,'depthMeters':depth,'baseNativeZ':base})
shed('left service house',[[43.8,508.8],[104.4,514.3]],1.62)
shed('right service house',[[187.7,521.0],[240.8,524.0]],1.66)
def tank(label,u,radius,top_image_y,cap=True):
    offset=.40 if cap else .22
    def center(x):
        origin,_=frame(x[0],24.77);return project(origin+np.array([0,0,x[1]+offset]))
    fit=least_squares(lambda x:center(x)-np.array([u,top_image_y]),[plane(u,24.77),8.1],xtol=1e-13,ftol=1e-13,gtol=1e-13)
    angle,bodytop=fit.x;origin,M=frame(angle,24.77);base=6.52;parts=[]
    parts.append(lathe([(radius*.96,base),(radius,base+.045),(radius,bodytop-.07),(radius*.99,bodytop)],material=0))
    # Shallow dished roof and the raised flattened inspection cover.
    parts.append(lathe([(radius,bodytop-.025),(radius*.97,bodytop+.065),(radius*.82,bodytop+.14),(radius*.54,bodytop+.20),(radius*.22,bodytop+.22)],material=0))
    for z in [base+.09,base+.24,bodytop-.045]:parts.append(lathe([(radius+.014,z-.018),(radius+.035,z),(radius+.014,z+.022)],material=1))
    if cap:
        parts.append(lathe([(.18,bodytop+.18),(.18,bodytop+.38)],material=2))
        parts.append(lathe([(radius*.55,bodytop+.34),(radius*.60,bodytop+.37),(radius*.60,bodytop+.43),(radius*.53,bodytop+.46)],material=1))
    if cap:
        ladder_y=-radius-.09
        for x in [-radius*.70,-radius*.22]:
            path=[[x,ladder_y,6.52],[x,ladder_y,bodytop+.30],[x,ladder_y+.22,bodytop+.46]]
            for a,b in zip(path[:-1],path[1:]):parts.append(rod(a,b,.015,2))
        for z in np.arange(6.61,bodytop+.31,.25):parts.append(rod([-radius*.71,ladder_y,z],[-radius*.21,ladder_y,z],.012,2))
    add(label,parts,origin,M)
    fitrecords.append({'name':label,'observedTopCenter708x1000':[u,top_image_y],'fittedTopCenter':center(fit.x).tolist(),'radiusMeters':radius,'bodyTopNativeZ':float(bodytop),'baseNativeZ':base,'inferredDepth':True})
tank('central water tank',152.3,.77,519.9)
tank('partly visible left water tank',3.5,.70,519.0,False)
data={'revision':45,'sourceNativeSha256':S['sourceNativeSha256'],'scope':'Four solid left rooftop assemblies: two service houses and two tanks. Front contours observed; depth and hidden rear structure inferred.','materialRoles':['weathered blue grey casing','pale metal rims','dark pipes and ladder','right house grey casing'],'fits':fitrecords,'members':records,'oneToOneComplete':False}
(O/'rooftop-geometry-v45.json').write_text(json.dumps(data,separators=(',',':')),encoding='utf-8')
print('ROOF_45_BUILT',len(records),sum(len(q['triangles']) for q in records),json.dumps(fitrecords,indent=2))
