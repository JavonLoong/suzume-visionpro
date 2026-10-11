"""Sample four existing reference textures onto the generated 3D vertices.

This writes mesh attributes, not altered reference images. Sampling uses the
source-view silhouettes to register orthographic views and surface normals to
blend the visible sides; the resulting colors are portable glTF vertex colors.
"""
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt, binary_fill_holes
H=Path(__file__).parent
data=np.load(H/'head-paint-geometry.npz')
P,N=data['positions'],data['normals']
bounds=np.array([P.min(axis=0),P.max(axis=0)])
output=np.zeros_like(P,dtype=np.float32)
weight_sum=np.zeros(len(P),dtype=np.float32)
for name,axis,sign,normal_axis,normal_sign in [('front',0,1,1,-1),('left',1,1,0,1),('back',0,-1,1,1),('right',1,-1,0,-1)]:
    rgb=np.asarray(Image.open(H/f'{name}.png').convert('RGB'),dtype=np.float32)
    rgb/=255
    mask=binary_fill_holes(((rgb.max(axis=2)-rgb.min(axis=2))>.075)|(rgb.max(axis=2)<.72))
    yy,xx=np.where(mask)
    xmin,xmax,ymin,ymax=xx.min(),xx.max(),yy.min(),yy.max()
    coords=P[:,axis]*sign
    cmin,cmax=(bounds[:,axis]*sign).min(),(bounds[:,axis]*sign).max()
    u=xmin+(coords-cmin)/(cmax-cmin)*(xmax-xmin)
    v=ymax-(P[:,2]-bounds[0,2])/(bounds[1,2]-bounds[0,2])*(ymax-ymin)
    u=np.clip(u,0,rgb.shape[1]-1);v=np.clip(v,0,rgb.shape[0]-1)
    # Edge samples use the nearest source foreground texel instead of white.
    nearest=distance_transform_edt(~mask,return_distances=False,return_indices=True)
    ix,iy=np.rint(u).astype(int),np.rint(v).astype(int)
    outside=~mask[iy,ix]
    ix[outside],iy[outside]=nearest[1,iy[outside],ix[outside]],nearest[0,iy[outside],ix[outside]]
    sampled=rgb[iy,ix]
    pin_red=(sampled[:,0]>sampled[:,1]*1.5)&(sampled[:,0]>sampled[:,2]*1.45)
    pin_gold=(sampled[:,0]>sampled[:,1]*1.25)&(sampled[:,1]>sampled[:,2]*1.7)
    sampled[(pin_red|pin_gold)&(P[:,2]>.25)&(P[:,0]>.08)]=[.27,.245,.23]
    # Smooth head-centered direction avoids texture changes at every tiny hair
    # ridge. Geometry normals are unsuitable for projection-camera selection.
    direction=P[:,normal_axis].copy()
    if normal_axis==1: direction+=.03
    weight=np.maximum(0,direction*normal_sign)**5
    # Upward/downward polygons still need a stable color.
    weight+=.00001
    output+=sampled*weight[:,None]
    weight_sum+=weight
    del rgb,nearest,mask
output/=weight_sum[:,None]
# Pins become separate physical geometry, so remove duplicate red/gold pigment
# only from the top-left hair region of these vertex attributes.
hair_volume=(P[:,2]>.74)|((P[:,1]>.40)&(P[:,2]<.35))|((P[:,1]>.30)&(P[:,2]>.35))
stray_light=hair_volume&(output.max(axis=1)>.42)
output[stray_light]=[.27,.245,.23]
linear=np.where(output<=.04045,output/12.92,((output+.055)/1.055)**2.4)
np.save(H/'head-vertex-colors-linear.npy',linear.astype(np.float32))
print('FOUR_VIEW_VERTEX_COLORS',len(output),flush=True)
