from pathlib import Path
import json,numpy as np,trimesh
from scipy.interpolate import PchipInterpolator
from scipy.ndimage import map_coordinates,gaussian_filter1d
from scipy.signal import find_peaks
from PIL import Image

R=Path(__file__).parent;O=R/'poster-railings-v46';V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
S=json.loads((O/'source-railings-v46.json').read_text());C=np.array(S['camera']['position']);rot=np.array(S['camera']['rotation']);f=S['camera']['focalPixels'];radius=23.5
def project(v):
    q=(np.asarray(v)-C)@rot;return np.stack((354+f*q[...,0]/-q[...,2],500-f*q[...,1]/-q[...,2]),axis=-1)
edges=(np.arange(33)-16.5)*np.pi/16
edges[13:21]=[-.745387,-.567705,-.415142,-.217486,.006904,.147421,.411245,.678266]
bays=[]
for i in range(12,16):
    a0,a1=edges[i:i+2];angle=(a0+a1)/2;half=(a1-a0)/2;rad=np.array([np.sin(angle),np.cos(angle),0]);t=np.array([np.cos(angle),-np.sin(angle),0]);center=rad*(radius*np.cos(half)+.02);width=2*radius*np.sin(half)+.022;bays.append({'index':i,'angle':angle,'rad':rad,'tangent':t,'center':center,'width':width})
# Upper surface of the pale handrail, manually read from the 2000px reference.
targets=np.array([[10,536.4],[35,539.1],[60,541.3],[85,543.3],[110,545.2],[140,547.4],[165,548.9],[190,550.5],[220,552.1],[247,553.4],[263,553.7]],float)
measured=[]
for u,v in targets:
    ray=np.array([(u-354)/f,(500-v)/f,-1])@rot.T;found=[]
    for b in bays:
        d=(np.dot(b['center']-C,b['rad']))/np.dot(ray,b['rad']);p=C+d*ray;x=np.dot(p-b['center'],b['tangent'])
        if abs(x)<=b['width']/2+.04:found.append((b,p,x))
    assert found,(u,v)
    b,p,x=found[0];measured.append({'u':u,'v':v,'bay':b['index'],'angle':float(np.arctan2(p[0],p[1])),'z':float(p[2]),'point':p.tolist()})
angles=np.array([x['angle'] for x in measured]);heights=np.array([x['z'] for x in measured]);top=PchipInterpolator(angles,heights,extrapolate=False)
def height(p):return float(top(np.clip(np.arctan2(p[0],p[1]),angles.min(),angles.max())))
# Estimate density from the unobstructed reference bars, not from the model.
im=np.asarray(Image.open(V/'reference-hires.jpg').convert('RGB'),float)/255;xs=np.linspace(52,104,1041);upper=np.interp(xs,targets[:,0],targets[:,1]);lower=upper+10
samples=[]
for t in np.linspace(.25,.78,12):
    ys=upper*(1-t)+lower*t;samples.append(map_coordinates(im.mean(2),[ys/1000*im.shape[0],xs/708*im.shape[1]],order=1))
signal=np.mean(samples,axis=0);detail=signal-gaussian_filter1d(signal,12);peaks,_=find_peaks(detail,distance=17,prominence=.008);screen_peaks=xs[peaks].copy();separations=np.diff(screen_peaks);valid=separations[(separations>1)&(separations<2.3)];pixel_spacing=float(np.median(valid));assert len(valid)>15
# At the measured left bay, convert observed image spacing to a metric interval.
b=bays[1];p=b['center']+np.array([0,0,6.95]);pp=project(np.array([p,p+b['tangent']*.1]));pixels_per_meter=(pp[1,0]-pp[0,0])/.1;spacing=float(np.clip(pixel_spacing/pixels_per_meter,.06,.11))
records=[];support=[];allparts=[]
def box_at(size,center,M,mat):
    mesh=trimesh.creation.box(extents=size);mesh.vertices=np.asarray(mesh.vertices)@M.T+center;return mesh,mat
for b in bays:
    parts=[];cent=b['center'];t=b['tangent'];rad=b['rad'];M=np.stack([t,rad,[0,0,1]],axis=1);w=b['width'];xs=np.linspace(-w/2,w/2,int(np.ceil(w/spacing))+1)
    # All bars pass through the lower rail and into the original cornice lip.
    for j,x in enumerate(xs):
        p=cent+t*x;zt=height(p)-.009;bottom=6.595;h=zt-bottom;thick=.040 if j in [0,len(xs)-1] else .0175
        parts.append(box_at([thick,.035,h],p+np.array([0,0,bottom+h/2]),M,0));support.append({'bay':b['index'],'point':(p+np.array([0,0,bottom])).tolist()})
    # Follow the measured height contour with solid overlapping rectangular links.
    tx=np.linspace(-w/2-.025,w/2+.025,max(4,int(w/.12)+1))
    for a,bb in zip(tx[:-1],tx[1:]):
        pa=cent+t*a;pb=cent+t*bb;za=height(pa)-.022;zb=height(pb)-.022;pa[2]=za;pb[2]=zb;direction=pb-pa;length=np.linalg.norm(direction);along=direction/length;normal=rad;up=np.cross(along,normal);MM=np.stack([along,normal,up],axis=1)
        parts.append(box_at([length+.006,.060,.044],(pa+pb)/2,MM,0))
    parts.append(box_at([w+.060,.056,.045],cent+np.array([0,0,6.643]),M,0))
    vertices=[];faces=[];indices=[];offset=0
    for mesh,material in parts:
        mesh.fix_normals();assert mesh.is_watertight and mesh.volume>0;vertices.append(mesh.vertices);faces.append(mesh.faces+offset);indices.extend([material]*len(mesh.faces));offset+=len(mesh.vertices)
    vv=np.concatenate(vertices);ff=np.concatenate(faces);records.append({'name':'Poster dense balcony rail bay '+str(b['index'])+' v46','bay':b['index'],'verticesNative':vv.round(8).tolist(),'triangles':ff.tolist(),'materialIndices':indices,'closedParts':len(parts),'uprights':len(xs),'actualSpacingMeters':float(w/(len(xs)-1)),'boundsImage':[project(vv).min(0).tolist(),project(vv).max(0).tolist()]})
data={'revision':46,'sourceNativeSha256':S['sourceNativeSha256'],'scope':'Observed left front balcony railing. Existing roof and cornice retained. Height curve constrained by visible reference upper edge; back detail inferred.','measurementUncertaintyPixels':1.5,'topReference':measured,'density':{'referenceInterval708x1000':[52,104],'detectedPeaks':screen_peaks.tolist(),'medianSpacingPixels':pixel_spacing,'pixelsPerMeter':float(pixels_per_meter),'targetSpacingMeters':spacing},'members':records,'supportPoints':support,'oneToOneComplete':False}
(O/'railing-geometry-v46.json').write_text(json.dumps(data,separators=(',',':')));print('RAIL_46_GEOMETRY',len(records),'uprights',len(support),'triangles',sum(len(q['triangles']) for q in records),'spacing',spacing,'sourcePixelSpacing',pixel_spacing);print('TOP_NATIVE_HEIGHTS',heights.tolist())
