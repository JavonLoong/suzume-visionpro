from pathlib import Path
import json,hashlib,numpy as np,trimesh
from scipy.ndimage import gaussian_filter,distance_transform_edt,map_coordinates
from skimage.measure import marching_cubes
R=Path(__file__).parent;O=R/'poster-lower-clouds-v43';a=np.load(O/'lower-bands-v43.npz');spec=json.loads((O/'lower-bands-v43.json').read_text())
camera=json.loads((R/'poster-v38/restoration-v38.json').read_text())['posterCamera'];M=np.array(camera['matrixWorld']);C=M[:3,3];rotation=M[:3,:3];f=camera['lens']/camera['sensorHeight']*1000
def ray(u,v):return np.c_[(u-354)/f,(500-v)/f,-np.ones(len(u))]@rotation.T
def project(world):
    d=(world-C)@rotation;return np.c_[354+f*d[:,0]/(-d[:,2]),500-f*d[:,1]/(-d[:,2])]
arrays={};records=[]
for q in spec['bands']:
    i=q['index'];rng=np.random.default_rng(430100+i);u=np.arange(-120,829);ys=np.arange(526,641)
    top=np.array(q['upper']);bottom=np.array(q['lower']);upper=np.interp(u,top[:,0],top[:,1]);lower=np.interp(u,bottom[:,0],bottom[:,1])
    # Continue the cloud volume outside the reference frame and taper its ends.
    taper=np.sqrt(np.clip(1-(np.maximum(0,np.maximum(-u,u-708))/120)**2,0,1));mid=(upper+lower)/2;half=(lower-upper)/2*taper
    mask=(ys[:,None]>=mid[None,:]-half[None,:])&(ys[:,None]<=mid[None,:]+half[None,:]);mask[:,[0,-1]]=False
    pad=6;local=np.pad(mask,pad);dist=distance_transform_edt(local);free=local.copy();yy,xx=np.mgrid[:local.shape[0],:local.shape[1]];balls=[]
    for _ in range(1300):
        score=dist*free;cy,cx=np.unravel_index(score.argmax(),score.shape);radius=float(dist[cy,cx])
        if radius<.8:break
        balls.append([cx,cy,radius,rng.uniform(1.35,2.1)]);free[(xx-cx)**2+(yy-cy)**2<(radius*.80)**2]=False
    pitch=.75;maxr=max(b[2]*b[3] for b in balls);gx=np.arange(-2,local.shape[1]+2,pitch);gy=np.arange(-2,local.shape[0]+2,pitch);gz=np.arange(-maxr-14,maxr+15,pitch);field=np.full((len(gx),len(gy),len(gz)),-3,dtype='f4')
    for cx,cy,r,d in balls:
        ix=np.flatnonzero(abs(gx-cx)<r+3);iy=np.flatnonzero(abs(gy-cy)<r+3);iz=np.flatnonzero(abs(gz)<(r+3)*d)
        sl=np.s_[ix[0]:ix[-1]+1,iy[0]:iy[-1]+1,iz[0]:iz[-1]+1]
        distance=np.sqrt((gx[ix,None,None]-cx)**2+(gy[None,iy,None]-cy)**2+(gz[None,None,iz]/d)**2);np.maximum(field[sl],r-distance,out=field[sl])
    field=gaussian_filter(field,.6)
    # The medial cover is regular inside a uniform inferred strip. Blend its
    # ridges and add smooth three-dimensional turbulence only where the source
    # does not constrain the surface, preventing a row of identical lobes.
    sample_x=np.clip((gx-pad-120)*2,0,1415);sample_y=np.clip((gy-pad+526)*2,0,1999)
    confidence=a['confidence'+str(i)]
    inferred=1-map_coordinates(confidence,np.array(np.meshgrid(sample_y,sample_x,indexing='xy')),order=1,mode='nearest')
    smoothed=gaussian_filter(field,2.4);field=field*(1-inferred[:,:,None])+smoothed*inferred[:,:,None]
    rough=gaussian_filter(np.random.default_rng(43600+i).normal(size=field.shape).astype('f4'),8)
    rough/=max(float(rough.std()),1e-6)
    field+=np.clip(rough,-2,2)*1.8*np.exp(-(field/3)**2)*inferred[:,:,None]
    boundary_max=max(float(face.max()) for face in [field[0],field[-1],field[:,0],field[:,-1],field[:,:,0],field[:,:,-1]])
    assert boundary_max<0,(i,'expanded field must contain the full surface',boundary_max)
    vertices,faces,_,_=marching_cubes(field,0,spacing=(pitch,)*3,allow_degenerate=False);vertices+=np.array([gx[0],gy[0],gz[0]])
    pu=vertices[:,0]-pad-120;pv=vertices[:,1]-pad+526;depth=q['depth'];world=C+(depth-vertices[:,2]*depth/f)[:,None]*ray(pu,pv)
    mesh=trimesh.Trimesh(world,faces[:,::-1],process=True);mesh.update_faces(mesh.nondegenerate_faces());mesh.update_faces(mesh.unique_faces());mesh.remove_unreferenced_vertices();mesh.fix_normals()
    assert mesh.is_watertight,(i,'pre-quantization boundary')
    origin=mesh.vertices.mean(0);mesh.vertices=np.asarray(mesh.vertices-origin,'f4').astype(float)+origin;mesh.merge_vertices(digits_vertex=7);mesh.update_faces(mesh.nondegenerate_faces());mesh.remove_unreferenced_vertices();mesh.fix_normals()
    if not mesh.is_watertight:
        # Float32 can collapse tiny marching-cubes slivers. Repair only the
        # resulting triangle/quad boundaries, then re-check the entire solid.
        trimesh.repair.fill_holes(mesh);mesh.fix_normals()
    assert mesh.is_watertight and mesh.volume>0,(i,mesh.is_watertight,mesh.volume)
    uv=project(mesh.vertices);coords=np.array([np.clip(uv[:,1]*2,0,1999),np.clip(uv[:,0]*2,0,1415)])
    pigment=a['rgb'+str(i)];front=np.stack([map_coordinates(pigment[:,:,j],coords,order=1,mode='nearest') for j in range(3)],axis=1)
    delta=mesh.vertices-C;facing=np.einsum('ij,ij->i',mesh.vertex_normals,-delta/np.linalg.norm(delta,axis=1)[:,None]);weight=np.clip((facing+.20)/.36,0,1);weight=weight*weight*(3-2*weight)
    # Fade beyond the observed image limits to inferred all-direction lighting.
    border=np.clip((uv[:,0]+75)/75,0,1)*np.clip((783-uv[:,0])/75,0,1)
    confidence=map_coordinates(a['confidence'+str(i)],coords,order=1,mode='nearest')
    # Hidden front surfaces must not inherit a constant nearest foreground
    # pigment. Their color comes from inferred three-dimensional illumination.
    weight*=border*confidence
    sun=np.array([-21.,-16.,32.]);sun/=np.linalg.norm(sun);illum=np.sqrt(np.maximum(mesh.vertex_normals@sun,0));back=np.clip(np.array([.50,.61,.70])+illum[:,None]*np.array([.18,.15,.10]),0,1)
    rgb=np.clip(front*weight[:,None]+back*(1-weight[:,None]),0,1)
    key='bank'+str(i);arrays[key+'_world']=mesh.vertices.astype('f8');arrays[key+'_local']=(mesh.vertices-origin).astype('f4');arrays[key+'_origin']=origin;arrays[key+'_faces']=mesh.faces.astype('u4');arrays[key+'_rgb']=rgb.astype('f4')
    records.append({'index':i,'key':key,'name':q['name'],'vertices':len(mesh.vertices),'triangles':len(mesh.faces),'closed':True,'signedWorldVolume':float(mesh.volume),'parts':len(mesh.split(only_watertight=False)),'worldBounds':mesh.bounds.tolist(),'inferredDepthMeters':depth,'maximumEllipsoidDepthRadiusMeters':float(maxr*depth/f),'referencePixelBounds':[[float(uv[:,0].min()),float(uv[:,1].min())],[float(uv[:,0].max()),float(uv[:,1].max())]]})
    print('LOWER_CLOUD_BUILT',i,len(mesh.vertices),len(mesh.faces),flush=True)
np.savez_compressed(O/'lower-cloud-geometry-v43.npz',**arrays)
(O/'lower-cloud-geometry-v43.json').write_text(json.dumps({'revision':43,'sourceNativeSha256':hashlib.sha256((R/'poster-horizon-v42/Suzume_dual_scene_horizon_v42.blend').read_bytes()).hexdigest(),'clouds':records,'triangles':sum(q['triangles'] for q in records),'closedGeometry':True,'unknownDepthAndBacksInferred':True,'oneToOneComplete':False},indent=2),encoding='utf-8')
