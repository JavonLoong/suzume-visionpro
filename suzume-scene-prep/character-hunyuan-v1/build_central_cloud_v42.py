"""Recover the continuous horizon bank through the incorrectly capped sky."""
from pathlib import Path
import ast,json,hashlib,cv2,numpy as np,trimesh
from scipy.ndimage import gaussian_filter,distance_transform_edt
from skimage.measure import marching_cubes
R=Path(__file__).parent;O=R/'poster-horizon-v42';O.mkdir(exist_ok=True)
tree=ast.parse((R/'build_poster_clouds_v41.py').read_text());stop=next(i for i,n in enumerate(tree.body) if isinstance(n,ast.For) and isinstance(n.target,ast.Tuple) and ast.unparse(n.target)=='(order, idx)')
c={'__file__':str(R/'build_poster_clouds_v41.py')};exec(compile(ast.Module(body=tree.body[:stop],type_ignores=[]),'cloud reference colors and projection','exec'),c)
native_ray=c['native_ray'];project=c['project'];C=c['C'];f=c['f'];W=c['W'];H=c['H'];pigments=c['pigments'];source=c['source'];confidence=c['occlusion_confidence'];occlusion=c['occlusion_small']
inspection=json.loads((O/'inspection-v42.json').read_text());assert len(inspection['affectedComponents'])==1;rec=inspection['affectedComponents'][0]
assert [q['cloudIndex'] for q in rec['overlapsOldClouds']]==[1,3]
a=np.load(O/'uncapped-mask-v42.npz');labels=a['labels'];idx=rec['uncappedComponent'];target=labels==idx;x,y,w,h=rec['bounds'];pad=6;local=np.pad(target[y:y+h,x:x+w].astype('u1'),pad)
assert y+h<labels.shape[0]-8,'Reject the cropped mask bottom as a cloud surface.'
# The recovered central pixels are above the door. Keeping the whole connected
# cloud joins them to the old left/right banks instead of leaving separate caps.
dist=distance_transform_edt(local);free=local.copy();yy,xx=np.mgrid[:local.shape[0],:local.shape[1]];balls=[];rng=np.random.default_rng(420171)
for j in range(800):
    score=dist*free;cy,cx=np.unravel_index(score.argmax(),score.shape);radius=float(dist[cy,cx])
    if radius<.7:break
    balls.append([cx,cy,radius,rng.uniform(.8,1.2)]);free[(xx-cx)**2+(yy-cy)**2<(radius*.78)**2]=0
pitch=.60;maxr=max(q[2] for q in balls);xs=np.arange(-2,local.shape[1]+2,pitch);ys=np.arange(-2,local.shape[0]+2,pitch);zs=np.arange(-maxr*1.3-3,maxr*1.3+4,pitch);field=np.full((len(xs),len(ys),len(zs)),-3,dtype=np.float32)
for cx,cy,radius,depth in balls:
    margin=radius+3;ix=np.flatnonzero(abs(xs-cx)<margin);iy=np.flatnonzero(abs(ys-cy)<margin);iz=np.flatnonzero(abs(zs)<margin*depth)
    if not(len(ix) and len(iy) and len(iz)):continue
    sl=np.s_[ix[0]:ix[-1]+1,iy[0]:iy[-1]+1,iz[0]:iz[-1]+1];d=np.sqrt((xs[ix,None,None]-cx)**2+(ys[None,iy,None]-cy)**2+(zs[None,None,iz]/depth)**2);np.maximum(field[sl],radius-d,out=field[sl])
field=gaussian_filter(field,.55);nx=np.clip(np.rint(xs+x-pad).astype(int),0,707);ny=np.clip(np.rint(ys+y-pad).astype(int),0,occlusion.shape[0]-1);occ=occlusion[ny[None,:],nx[:,None]]
turbulence=gaussian_filter(np.random.default_rng(4242).normal(size=field.shape).astype(np.float32),3);turbulence/=max(float(turbulence.std()),1e-6);field+=turbulence*.55*np.exp(-field*field/2)*occ[:,:,None]
v,faces,_,_=marching_cubes(field,0,spacing=(pitch,)*3,allow_degenerate=False);v+=np.array([xs[0],ys[0],zs[0]]);u=v[:,0]+x-pad;vv=v[:,1]+y-pad
# Match the original cloud-3 depth on the left and cloud-1 depth on the right.
# Smoothstep interpolation gives a continuous inferred bank between them.
t=np.clip((u-297)/(411-297),0,1);t=t*t*(3-2*t);depth=252.2*(1-t)+247.4*t
world=C+(depth-v[:,2]*depth/f)[:,None]*native_ray(u,vv)
mesh=trimesh.Trimesh(world,faces[:,::-1],process=True);mesh.update_faces(mesh.nondegenerate_faces());mesh.update_faces(mesh.unique_faces());mesh.remove_unreferenced_vertices();mesh.fix_normals()
# Use a nearby local origin: world-coordinate float32 quantization collapses
# very small edges in the narrow bridge, despite the original field being closed.
origin=mesh.vertices.mean(0);mesh.vertices=np.asarray(mesh.vertices-origin,np.float32).astype(float)+origin;mesh.merge_vertices(digits_vertex=7);mesh.update_faces(mesh.nondegenerate_faces());mesh.update_faces(mesh.unique_faces());mesh.remove_unreferenced_vertices();mesh.fix_normals()
assert mesh.is_watertight and mesh.volume>0
uv=project(mesh.vertices);px=np.clip(np.rint(uv[:,0]*W/708).astype(int),0,W-1);py=np.clip(np.rint(uv[:,1]*H/1000).astype(int),0,source.shape[0]-1);front=pigments[py,px]
d=mesh.vertices-C;view=-d/np.linalg.norm(d,axis=1)[:,None];facing=np.einsum('ij,ij->i',mesh.vertex_normals,view);weight=np.clip((facing+.23)/.38,0,1);weight=weight*weight*(3-2*weight)*confidence[py,px]
sun=np.array([-21.,-16.,32.]);sun/=np.linalg.norm(sun);illum=np.maximum(mesh.vertex_normals@sun,0);back=np.clip(np.array([.50,.65,.75])+illum[:,None]*np.array([.42,.31,.23]),0,1);colors=np.clip(front*weight[:,None]+back*(1-weight[:,None]),0,1)
parts=mesh.split(only_watertight=False);part_records=[]
for part in parts:
    p=project(part.vertices);part_records.append({'vertices':len(part.vertices),'triangles':len(part.faces),'closed':bool(part.is_watertight),'volume':float(part.volume),'projectionBounds708':[p.min(0).tolist(),p.max(0).tolist()]})
spanning=[q for q in part_records if q['projectionBounds708'][0][0]<297 and q['projectionBounds708'][1][0]>411];assert spanning and all(q['closed'] for q in part_records)
np.savez_compressed(O/'horizon-geometry-v42.npz',world=np.asarray(mesh.vertices,np.float64),local=np.asarray(mesh.vertices-origin,np.float32),origin=origin,faces=np.asarray(mesh.faces,np.uint32),rgb=np.asarray(colors,np.float32),targetMask=target)
report={'revision':42,'sourceNativeSha256':inspection['sourceNativeSha256'],'name':'Restored central horizon cloud bank v42','replaces':['Distant reference closed cloud 1.001','Distant reference closed cloud 3.001'],'vertices':len(mesh.vertices),'triangles':len(mesh.faces),'closed':True,'signedWorldVolume':float(mesh.volume),'parts':part_records,'continuousPartSpansFormerGap':True,'sourceBounds708':rec['bounds'],'recoveredPureSkyProbePixels':inspection['pureSkyProbeRestoredPixels'],'depthLeftMeters':252.2,'depthRightMeters':247.4,'depthInterpolationScreenRange':[297,411],'unknownDepthInferred':True,'sourceMaskLimitations':'Inherited segmentation and foreground inpainting are approximate; the recovered probe is above the door, and the cropped mask bottom was excluded.','oneToOneComplete':False};(O/'horizon-geometry-v42.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print('HORIZON_42_GEOMETRY',report['vertices'],report['triangles'],'parts',len(parts),flush=True)
