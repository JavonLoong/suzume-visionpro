"""Shared numerical scene transformation; no Blender dependency."""
from pathlib import Path
import json, math
import numpy as np
R=Path(__file__).parent;O=R/'movie-projection-v24'
F=json.loads((O/'joint-fit-v24.json').read_text(encoding='utf-8'));P=F['parameters']
old_edges=(np.arange(33)-16.5)*math.pi/16
old_edges[13:21]=[-.745387,-.567705,-.415142,-.217486,.006904,.147421,.411245,.678266]
new_edges=np.zeros(33);new_edges[12:18]=[P[f'edge{i}'] for i in range(12,18)]
outside=(2*math.pi-new_edges[17]+new_edges[12])/(2*math.pi-old_edges[17]+old_edges[12])
for i in range(18,33):new_edges[i]=new_edges[17]+(old_edges[i]-old_edges[17])*outside
for i in range(12):new_edges[i]=new_edges[12]-(old_edges[12]-old_edges[i])*outside
assert np.all(np.diff(new_edges)>0) and abs(new_edges[32]-new_edges[0]-2*math.pi)<1e-8
center=np.array([P['courtyardX'],P['courtyardY'],0.])

def levels(index):
    if 7<=index<=15 or 18<=index<=26:
        return np.array([-.22,0,.73,.865,1.22,3.36,4.66,6.52]),np.array([-.22,0,1.33,1.47,P['windowSill'],P['windowSill']+2.14,P['arcadeBase'],P['highRoof']])
    return np.array([-.22,0,.73,.865,1.22,3.36,4.78]),np.array([-.22,0,1.33,1.47,P['windowSill'],P['windowSill']+2.14,P['lowRoof']])

def linear_extrapolate(z,x,y):
    z=np.asarray(z);i=np.clip(np.searchsorted(x,z,side='right')-1,0,len(x)-2)
    return y[i]+(z-x[i])*(y[i+1]-y[i])/(x[i+1]-x[i])

def height(z,index,inverse=False):
    x,y=levels(index)
    return linear_extrapolate(z,y,x) if inverse else linear_extrapolate(z,x,y)

def bay_spec(index):
    a,b=new_edges[index:index+2]
    return dict(index=index,edges=[float(a),float(b)],angle=float((a+b)/2),chordRadius=float(23.5*np.cos((b-a)/2)),bayWidth=float(47*np.sin((b-a)/2)+.022))

def map_source(a,architectural=True):
    a=np.array(a,dtype=float).reshape(-1,3);out=a.copy();angles=np.arctan2(a[:,0],a[:,1])
    angles=(angles-old_edges[0])%(2*math.pi)+old_edges[0]
    ids=np.clip(np.searchsorted(old_edges,angles,side='right')-1,0,31)
    for i in np.unique(ids):
        mask=ids==i;v=a[mask];oa=(old_edges[i]+old_edges[i+1])/2;na=(new_edges[i]+new_edges[i+1])/2
        oh=(old_edges[i+1]-old_edges[i])/2;nh=(new_edges[i+1]-new_edges[i])/2
        normal=np.array([np.sin(oa),np.cos(oa)]);tangent=np.array([np.cos(oa),-np.sin(oa)])
        old_r=v[:,:2]@normal;front=23.5*np.cos(oh)-old_r;new_r=23.5*np.cos(nh)-front
        local_x=v[:,:2]@tangent;local_x*=np.tan(nh)/np.tan(oh)*new_r/np.maximum(old_r,1e-6)
        out[mask,:2]=new_r[:,None]*[np.sin(na),np.cos(na)]+local_x[:,None]*[np.cos(na),-np.sin(na)]+center[:2]
        if architectural:
            blend=np.clip((np.linalg.norm(v[:,:2],axis=1)-21.7)/.8,0,1);blend=blend*blend*(3-2*blend)
            out[mask,2]=v[:,2]*(1-blend)+height(v[:,2],int(i))*blend
    return out

def place_new_bay(three,index):
    a=np.asarray(three).reshape(-1,3)[:,[0,2,1]]*[1,-1,1]
    a[:,2]=height(a[:,2],index);a+=center
    return a

