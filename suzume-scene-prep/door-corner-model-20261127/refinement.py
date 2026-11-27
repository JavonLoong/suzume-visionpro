"""Local inner-corner expert; global detection remains the source of candidate doors."""
from pathlib import Path
import sys,math,json,random,functools
import numpy as np,cv2,torch
from torch import nn
from torch.nn import functional as F
sys.path.insert(0,'D:/虚拟C盘/JavonLoongSkill/suzume-scene-prep/door-keypoint-model-20261118')
from common import imread_gray,pyramid

SIZE=64
SIGNS=np.array([[1,-1],[-1,-1],[1,1],[-1,1]],np.float32) # canonical interior points down/right

def cbr(a,b):return nn.Sequential(nn.Conv2d(a,b,3,padding=1,bias=False),nn.BatchNorm2d(b),nn.ReLU(inplace=True))
class CornerNet(nn.Module):
 def __init__(self):
  super().__init__();self.a=nn.Sequential(cbr(1,8),cbr(8,8));self.b=nn.Sequential(cbr(8,16),cbr(16,16))
  self.c=nn.Sequential(cbr(16,24),cbr(24,24));self.d=nn.Sequential(cbr(40,16),cbr(16,16));self.e=nn.Sequential(cbr(24,8),cbr(8,8))
  self.heat=nn.Conv2d(8,1,1);self.off=nn.Conv2d(8,2,1);nn.init.constant_(self.heat.bias,-2.19)
 def forward(self,x):
  a=self.a(x);b=self.b(F.avg_pool2d(a,2));c=self.c(F.avg_pool2d(b,2))
  d=self.d(torch.cat([F.interpolate(c,scale_factor=2,mode='nearest'),b],1))
  e=self.e(torch.cat([F.interpolate(d,scale_factor=2,mode='nearest'),a],1))
  return torch.cat([torch.sigmoid(self.heat(e)),self.off(e)],1)

def patch_scale(points):
 width=(np.linalg.norm(points[1]-points[0])+np.linalg.norm(points[3]-points[2]))/2
 return np.clip(width*.5,12,160)/SIZE

def crop(gray,centre,k,index):
 signs=SIGNS[index];A=np.array([[k*signs[0],0,0],[0,k*signs[1],0]],np.float64)
 A[:,2]=np.array(centre)-A[:,:2]@np.array([SIZE/2,SIZE/2])
 level=int(np.clip(math.floor(math.log2(max(k,1e-6))),0,5));pyr=pyramid(gray,level);level=len(pyr)-1;f=1/(1<<level)
 M=A*f;M[:,2]=(A[:,:2]@np.array([.5,.5])+A[:,2])*f-.5
 patch=cv2.warpAffine(pyr[level],M,(SIZE,SIZE),flags=cv2.INTER_LINEAR|cv2.WARP_INVERSE_MAP,borderMode=cv2.BORDER_REPLICATE)
 return patch,A

def runtime_crop(gray,centre,k,index):
 """Continuous bilinear sampler used by the Unity implementation; no 8-bit crop rounding."""
 signs=SIGNS[index];A=np.array([[k*signs[0],0,0],[0,k*signs[1],0]],np.float64)
 A[:,2]=np.array(centre)-A[:,:2]@np.array([SIZE/2,SIZE/2])
 wanted=int(np.clip(math.floor(math.log2(max(k,1e-6))),0,5));g=gray;level=0
 while level<wanted and min(g.shape)>=2:
  h,w=g.shape[0]//2*2,g.shape[1]//2*2
  sums=g[:h:2,:w:2].astype(np.uint16)+g[1:h:2,:w:2]+g[:h:2,1:w:2]+g[1:h:2,1:w:2]
  g=((sums+2)//4).astype(np.uint8);level+=1
 f=1/(1<<level);ys,xs=np.mgrid[0:SIZE,0:SIZE]
 sx=np.clip((A[0,0]*(xs+.5)+A[0,2])*f-.5,0,g.shape[1]-1)
 sy=np.clip((A[1,1]*(ys+.5)+A[1,2])*f-.5,0,g.shape[0]-1)
 xa=sx.astype(int);ya=sy.astype(int);xb=np.minimum(xa+1,g.shape[1]-1);yb=np.minimum(ya+1,g.shape[0]-1)
 tx=sx-xa;ty=sy-ya
 top=g[ya,xa].astype(float)*(1-tx)+g[ya,xb]*tx;bottom=g[yb,xa].astype(float)*(1-tx)+g[yb,xb]*tx
 return ((1-ty)*top+ty*bottom).astype(np.float32),A

def decode(out):
 points=[];scores=[]
 for item in out:
  y,x=divmod(int(item[0].argmax()),SIZE);points.append([x+.5+item[1,y,x],y+.5+item[2,y,x]]);scores.append(item[0,y,x])
 return np.asarray(points),np.asarray(scores)

@functools.lru_cache(maxsize=512)
def read_image(path):return imread_gray(path)

def items(root):
 out=[]
 for p in sorted((root/'labels').glob('*.json')):
  l=json.loads(p.read_text(encoding='utf-8'))
  if l['split']!='train' or not l.get('door_present',True):continue
  points=np.array(l['keypoints'],np.float32);indices=np.flatnonzero(points[:,2]==2)
  if len(indices):out.append((str(root/l['image']),points[:,:2],indices,l.get('leaf_angle_deg',0)))
 return out

def training_sample(item,rng,geometric=False):
 path,points,visible,_=item;index=int(rng.choice(visible));gray=read_image(path)
 k=float(patch_scale(points)*rng.uniform(.8,1.25));scale=k*SIZE
 centre=points[index]+rng.uniform(-.18,.18,2)*scale
 image,A=crop(gray,centre,k,index);target=np.linalg.solve(A[:,:2],points[index]-A[:,2])
 image=image.astype(np.float32)/255
 if geometric:
  angle=rng.uniform(-14,14)*math.pi/180;c,s=math.cos(angle),math.sin(angle)
  linear=np.array([[c,-s],[s,c]])@np.array([[rng.uniform(.9,1.1),rng.uniform(-.10,.10)],[rng.uniform(-.10,.10),rng.uniform(.9,1.1)]])
  offset=np.array([32.,32.])-linear@np.array([32.,32.]);target=linear@target+offset
  matrix=np.c_[linear,offset+linear@np.array([.5,.5])-.5]
  image=cv2.warpAffine(image,matrix,(SIZE,SIZE),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)
 if rng.rand()<.5:image=cv2.GaussianBlur(image,(0,0),rng.uniform(.25,1.25))
 image=np.clip(image,0,1)**rng.uniform(.7,1.4)
 image=np.clip((image-.5)*rng.uniform(.7,1.3)+.5+rng.uniform(-.12,.12)+rng.normal(0,rng.uniform(0,.02),image.shape),0,1)
 return image[None].astype(np.float32),target.astype(np.float32)

def loss_fn(output,target):
 yy,xx=torch.meshgrid(torch.arange(SIZE,device=output.device),torch.arange(SIZE,device=output.device),indexing='ij')
 cell=torch.floor(target);dx=xx[None]-cell[:,0,None,None];dy=yy[None]-cell[:,1,None,None]
 heat=torch.exp(-(dx*dx+dy*dy)/(2*1.5**2));positive=(dx==0)&(dy==0)
 probability=output[:,0].float().clamp(1e-4,1-1e-4)
 hl=-(positive*(1-probability)**2*probability.log()+(~positive)*(1-heat)**4*probability**2*(1-probability).log()).sum()/len(target)
 offset=torch.stack([target[:,0,None,None]-(xx[None]+.5),target[:,1,None,None]-(yy[None]+.5)],dim=1)
 mask=((dx.abs()<=1)&(dy.abs()<=1))[:,None]
 ol=(F.smooth_l1_loss(output[:,1:].float(),offset,reduction='none',beta=.1)*mask).sum()/(mask.sum()*2)
 return hl+2*ol
