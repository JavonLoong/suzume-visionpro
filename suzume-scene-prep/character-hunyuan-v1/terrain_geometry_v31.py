"""Spatial rolling terrain fitted to visible skyline points, with inferred depth."""
import numpy as np
from scipy.interpolate import PchipInterpolator

def smooth(a,b,x):
    t=np.clip((np.asarray(x)-a)/(b-a),0,1);return t*t*(3-2*t)

def height_field(x,y,q):
    x=np.asarray(x);y=np.asarray(y);r=np.hypot(x,y);a=np.arctan2(x,y)
    descent=-q['slope']*np.maximum(r-75,0)
    hidden_height=.35+.55*np.sin(a*3+.4)+.28*np.sin(a*7-1.2)
    projected_x=145*np.tan(np.clip(a,-1.4,1.4))
    front=PchipInterpolator(q['crestX'],q['crestZ'])(np.clip(projected_x,q['crestX'][0],q['crestX'][-1]))
    w=1-smooth(.18,.36,np.abs(a));crest=hidden_height*(1-w)+front*w
    radius=145+6*np.sin(a*3)*(1-w)
    amplitude=crest+q['slope']*(radius-75)
    ridge=amplitude*np.exp(-((r-radius)/q['ridgeWidth'])**2)
    rough=.045*np.sin(x*.37+y*.13)*np.sin(x*.19-y*.22)
    return descent+ridge+rough

def adjusted_ground(world,q):
    out=np.array(world,copy=True);w=smooth(q['unchangedNearRadius'],q['fullyAdjustedRadius'],np.hypot(world[:,0],world[:,1]));out[:,2]=world[:,2]*(1-w)+height_field(world[:,0],world[:,1],q)*w
    return out

def extension_mesh(q):
    count=q['angularSegments'];steps=q['radialSegments'];angles=np.arange(count)*2*np.pi/count;dx=np.sin(angles);dy=np.cos(angles);inner=198/np.maximum(abs(dx),abs(dy))
    u=(np.arange(steps+1)/steps)**1.1;r=inner[None,:]+u[:,None]*(q['outerRadius']-inner[None,:]);x=r*dx;y=r*dy;z=height_field(x,y,q)
    z-=.015*(1-smooth(198,202,np.maximum(abs(x),abs(y))))
    top=np.stack([x,y,z],-1).reshape(-1,3);bottom=top.copy();bottom[:,2]=-55;v=np.concatenate([top,bottom]);n=len(top);faces=[]
    for j in range(steps):
        for i in range(count):
            k=(i+1)%count;a=j*count+i;b=j*count+k;c=(j+1)*count+i;d=(j+1)*count+k
            faces.extend([(a,c,b),(b,c,d),(a+n,b+n,c+n),(b+n,d+n,c+n)])
    for i in range(count):
        k=(i+1)%count;faces.extend([(i,k,i+n),(k,k+n,i+n)])
        a=steps*count+i;b=steps*count+k;faces.extend([(a,a+n,b),(b,a+n,b+n)])
    return v,np.array(faces,dtype=np.int32)[:,[0,2,1]]
