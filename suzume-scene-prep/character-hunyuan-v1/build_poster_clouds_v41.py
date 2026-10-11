"""Restore the lower cloud field as dense closed contour-constrained solids.

The existing v9 segmentation defines the observed silhouettes. Unknown depths
are inferred from a union of medial ellipsoids; no camera-facing card is used.
"""
from pathlib import Path
import ast,json,hashlib
import numpy as np,cv2,trimesh
from scipy.ndimage import gaussian_filter,distance_transform_edt
from skimage.measure import marching_cubes
R=Path(__file__).parent;O=R/'poster-clouds-v41';O.mkdir(exist_ok=True)
V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
# Execute only the existing read-only segmentation setup, stopping before its
# generation loop and file writes. This keeps the existing reference windows.
tree=ast.parse((V/'build_distant_clouds_v9.py').read_text());prefix=[]
for node in tree.body:
    if isinstance(node,ast.For) and isinstance(node.target,ast.Tuple) and ast.unparse(node.target).startswith('(order,'):break
    prefix.append(node)
else:raise RuntimeError('Cannot locate the legacy segmentation boundary')
context={'__file__':str(V/'build_distant_clouds_v9.py')};exec(compile(ast.Module(body=prefix,type_ignores=[]),'legacy cloud segmentation','exec'),context)
mask=context['mask'];labels=context['labels'];components=context['components'];stats=context['stats'];rgb=context['rgb'];invalid=context['invalid'];source=context['source']
H,W=rgb.shape[:2];width=708
raw=rgb[:source.shape[0]].astype(float)
# Exclude steel and residual warm foreground samples from cloud pigments.
invalid=cv2.dilate(invalid,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(45,45)))
known=(source>0)&(invalid==0)&(raw[:,:,0]<=raw[:,:,1]+3)&(raw[:,:,1]<=raw[:,:,2]+3)
profile=np.interp(np.arange(W),np.array(context['top'])[:,0],np.array(context['top'])[:,1]);known &= np.arange(source.shape[0])[:,None]<profile[None,:]-20
_,nearest=distance_transform_edt(~known,return_indices=True)
official=cv2.cvtColor(cv2.imread(str(V/'reference-official.jpg')),cv2.COLOR_BGR2RGB)/255
# Official colors are authoritative. Preserve only subtle high-frequency
# detail from the larger reference; do not inherit its brighter color grade.
official_large=cv2.resize(official,(W,H),interpolation=cv2.INTER_CUBIC)
hi=rgb.astype(float)/255;detail=hi-gaussian_filter(hi,(4,4,0))
pigments=np.clip(official_large+detail*.38,0,1)
# A nearest valid color creates Voronoi stripes behind widened steel masks.
# Use it only to seed a continuous cloud-only color extension, then solve the
# masked gaps with Navier-Stokes inpainting before baking fixed vertex colors.
seed=np.rint(pigments[nearest[0],nearest[1]]*255).astype(np.uint8)
near_cloud=cv2.dilate((source>0).astype(np.uint8),cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(61,61)))>0
fill_mask=((~known)&near_cloud).astype(np.uint8)*255
pigments=cv2.inpaint(seed,fill_mask,5,cv2.INPAINT_NS).astype(float)/255
occlusion_confidence=np.clip(distance_transform_edt(invalid==0)/18,0,1)
occlusion_small=cv2.resize((invalid>0).astype(np.float32),(708,round(invalid.shape[0]*708/W)),interpolation=cv2.INTER_AREA)
camera=json.loads((R/'poster-v38/restoration-v38.json').read_text())['posterCamera'];M=np.array(camera['matrixWorld']);C=M[:3,3];rotation=M[:3,:3];f=camera['lens']/camera['sensorHeight']*1000
def native_ray(u,v):
    return np.c_[(u-354)/f,(500-v)/f,-np.ones(len(u))]@rotation.T
def project(world):
    v=(world-C)@rotation;return np.c_[354+f*v[:,0]/(-v[:,2]),500-f*v[:,1]/(-v[:,2])]
def raster(vertices,faces):
    uv=project(vertices);im=np.zeros((1000,708),np.uint8)
    for tri in np.rint(uv[faces]).astype(np.int32):cv2.fillConvexPoly(im,tri,1)
    return im>0
arrays={};records=[];rng=np.random.default_rng(90517)
for order,idx in enumerate(components):
    x,y,w,h,area=stats[idx];pad=6;local=np.pad((labels[y:y+h,x:x+w]==idx).astype('u1'),pad);distance=distance_transform_edt(local);free=local.copy();yy,xx=np.mgrid[:local.shape[0],:local.shape[1]];balls=[]
    for j in range(500):
        score=distance*free;cy,cx=np.unravel_index(score.argmax(),score.shape);rad=float(distance[cy,cx])
        if rad<.7:break
        balls.append([cx,cy,rad,rng.uniform(.8,1.2)]);free[(xx-cx)**2+(yy-cy)**2<(rad*.78)**2]=0
    if not balls:raise RuntimeError('Missing cloud '+str(order))
    pitch=.60;maxr=max(b[2] for b in balls);xs=np.arange(-2,local.shape[1]+2,pitch);ys=np.arange(-2,local.shape[0]+2,pitch);zs=np.arange(-maxr*1.3-3,maxr*1.3+4,pitch)
    field=np.full((len(xs),len(ys),len(zs)),-3,dtype=np.float32)
    # Local bounding boxes avoid evaluating each ellipsoid across empty sky.
    for cx,cy,rad,depth in balls:
        margin=rad+3;ix=np.flatnonzero(abs(xs-cx)<margin);iy=np.flatnonzero(abs(ys-cy)<margin);iz=np.flatnonzero(abs(zs)<margin*depth)
        if not(len(ix) and len(iy) and len(iz)):continue
        sl=np.s_[ix[0]:ix[-1]+1,iy[0]:iy[-1]+1,iz[0]:iz[-1]+1]
        q=np.sqrt((xs[ix,None,None]-cx)**2+(ys[None,iy,None]-cy)**2+(zs[None,None,iz]/depth)**2)
        np.maximum(field[sl],rad-q,out=field[sl])
    field=gaussian_filter(field,.55)
    # The old binary inpaint produced straight cut edges along occluding steel.
    # Infer small billows only within that unknown strip, preserving observed
    # contours elsewhere. The displacement fades away from the zero surface.
    nx=np.clip(np.rint(xs+x-pad).astype(int),0,707);ny=np.clip(np.rint(ys+y-pad).astype(int),0,occlusion_small.shape[0]-1)
    occ=occlusion_small[ny[None,:],nx[:,None]]
    if np.max(occ)>.01:
        turbulence=gaussian_filter(np.random.default_rng(4100+order).normal(size=field.shape).astype(np.float32),3)
        turbulence/=max(float(turbulence.std()),1e-6)
        field+=turbulence*.55*np.exp(-field*field/2)*occ[:,:,None]
    vertices,faces,_,_=marching_cubes(field,0,spacing=(pitch,)*3,allow_degenerate=False);vertices+=np.array([xs[0],ys[0],zs[0]])
    u=vertices[:,0]+x-pad;v=vertices[:,1]+y-pad;D=245+order*2.4;scale=D/f
    world=C+(D-vertices[:,2]*scale)[:,None]*native_ray(u,v)
    mesh=trimesh.Trimesh(world,faces[:,::-1],process=True);mesh.update_faces(mesh.nondegenerate_faces());mesh.update_faces(mesh.unique_faces());mesh.remove_unreferenced_vertices();mesh.fix_normals()
    # Resolve sub-float32 edge collapses before either native or WebGL export.
    mesh.vertices=np.asarray(mesh.vertices,dtype=np.float32);mesh.merge_vertices(digits_vertex=7);mesh.update_faces(mesh.nondegenerate_faces());mesh.update_faces(mesh.unique_faces());mesh.remove_unreferenced_vertices();mesh.fix_normals()
    assert mesh.is_watertight and mesh.volume>0,(order,mesh.is_watertight,mesh.volume)
    uv=project(mesh.vertices);pu=uv[:,0]*W/708;pv=uv[:,1]*H/1000;ix=np.clip(np.rint(pu).astype(int),0,W-1);iy=np.clip(np.rint(pv).astype(int),0,source.shape[0]-1)
    front=pigments[iy,ix]
    delta=mesh.vertices-C;view=-delta/np.linalg.norm(delta,axis=1)[:,None];facing=np.einsum('ij,ij->i',mesh.vertex_normals,view)
    weight=np.clip((facing+.23)/.38,0,1);weight=weight*weight*(3-2*weight)
    weight*=occlusion_confidence[iy,ix]
    sun=np.array([-21.,-16.,32.]);sun/=np.linalg.norm(sun);illum=np.maximum(mesh.vertex_normals@sun,0)
    back=np.clip(np.array([.50,.65,.75])+illum[:,None]*np.array([.42,.31,.23]),0,1)
    colors=np.clip(front*weight[:,None]+back*(1-weight[:,None]),0,1)
    key='cloud'+str(order);arrays[key+'_world']=np.asarray(mesh.vertices,dtype=np.float32);arrays[key+'_faces']=np.asarray(mesh.faces,dtype=np.uint32);arrays[key+'_rgb']=np.asarray(colors,dtype=np.float32)
    rendered=raster(mesh.vertices,mesh.faces);target=np.zeros((1000,708),bool);target[:labels.shape[0]]=labels==idx
    intersection=np.count_nonzero(rendered&target);union=np.count_nonzero(rendered|target)
    records.append({'index':order,'name':'Distant reference closed cloud '+str(order)+'.001','key':key,'sourceBounds708':[int(x),int(y),int(w),int(h)],'vertices':len(mesh.vertices),'triangles':len(mesh.faces),'closed':True,'signedVolume':float(mesh.volume),'medialEllipsoids':len(balls),'samplingPitchPixels':pitch,'silhouetteIoU':intersection/union,'projectionBounds708':[uv.min(0).tolist(),uv.max(0).tolist()],'sourceAreaPixels':int(area),'projectedAreaPixels':int(rendered.sum())})
    print('CLOUD',order,len(mesh.vertices),len(mesh.faces),'IoU',round(intersection/union,4),flush=True)
np.savez_compressed(O/'cloud-geometry-v41.npz',**arrays)
report={'revision':41,'sourceNativeSha256':'208af91831d845af7c4ce9e394f69bbe62caa737a3392f0207242c0527790b20','method':'Dense closed implicit unions of medial ellipsoids constrained by the existing lower-cloud mask. Source-calibrated fixed vertex pigments blend to inferred back colors. No plane or billboard.','occludedSurfaceTreatment':'Continuous cloud-only color extension; blend to inferred geometric lighting within the steel mask and its 18-pixel confidence transition. Add shallow 3D billows only within the uncertain occlusion strip.','occlusionBillowAmplitudeIn708FramePixels':.55,'clouds':records,'triangles':sum(q['triangles'] for q in records),'unknownDepthInferred':True,'referenceMaskLimitations':'The inherited v9 mask inpaints occluded steel and excludes very small fragments; its contours are constraints, not full-scene ground truth.','oneToOneComplete':False}
(O/'cloud-geometry-v41.json').write_text(json.dumps(report,indent=2),encoding='utf-8');ok,encoded=cv2.imencode('.png',mask*255);assert ok;(O/'source-mask-v41.png').write_bytes(encoded.tobytes());print('CLOUD_41_GEOMETRY_DONE',report['triangles'],flush=True)
