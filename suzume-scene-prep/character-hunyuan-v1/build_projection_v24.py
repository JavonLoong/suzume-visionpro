"""Refit actual openings and reuse complete editable room construction."""
from pathlib import Path
import json, numpy as np
from scipy.optimize import least_squares
from projection_geometry_v24 import R,O,P,F,new_edges,bay_spec,height,center
q=np.array(F['parameterVector'])
def project(p):
    x,y,z=np.asarray(p)-[q[2],-q[1],q[3]];c,s=np.cos(q[4]),np.sin(q[4]);d=y*c-z*s;f=1656*q[0]/36
    return np.array([1276+f*x/d,828-f*(y*s+z*c)/d])
def local_project(spec,x,y):
    a=spec['angle'];r=spec['chordRadius']
    return project([np.sin(a)*r+x*np.cos(a)+center[0],np.cos(a)*r-x*np.sin(a)+center[1],y])
old=json.loads((R/'movie-bays-v23/bay-fit-v23.json').read_text(encoding='utf-8'))
bays=[]
for prior in old['bays']:
    i=prior['index'];b=bay_spec(i);b['openings']=[];w=b['bayWidth']
    for op in prior['openings']:
        target=np.array(op['targets']);isarch=op['type']=='arch'
        def points(v):
            x,y,width,h=v[:4]
            coords=[(x-width/2,y+h),(x+width/2,y+h),(x+width/2,y),(x-width/2,y)]
            if isarch:
                rise=v[4];coords=[(x,y+h),(x-width/2,y+h-rise),(x+width/2,y+h-rise),(x-width/2,y),(x+width/2,y)]
            return np.array([local_project(b,*c) for c in coords])
        result=least_squares(lambda v:(points(v)-target).ravel(),[0,P['windowSill'],1.5,2.14]+([.5] if isarch else []),
            bounds=([-w/2,1.2,.4,1.6]+([.2] if isarch else []),[w/2,2.1,w-.1,2.7]+([.8] if isarch else [])))
        x,y,width,h=result.x[:4];assert x-width/2>-w/2+.04 and x+width/2<w/2-.04,(i,result.x,w)
        new=dict(op,x=float(x),width=float(width),bottom=float(height(y,i,True)),height=float(height(y+h,i,True)-height(y,i,True)),
                 projected=points(result.x).tolist(),meanErrorPixels=float(np.linalg.norm(points(result.x)-target,axis=1).mean()))
        if isarch:new['rise']=float(height(y+h,i,True)-height(y+h-result.x[4],i,True))
        b['openings'].append(new)
    bays.append(b)
fit={'revision':24,'bays':bays,'jointFit':F,'facadeEdges':new_edges.tolist()}
(O/'bay-fit-v24.json').write_text(json.dumps(fit,indent=2),encoding='utf-8')
js=(R/'movie-bays-v23/build_bays.js').read_text(encoding='utf-8')
start="const facadeEdges=Array.from({length:N+1},(_,i)=>(i-N/2-.5)*step);"
js=js.replace(start,'const facadeEdges=fit.facadeEdges;')
line="const measuredPiers=[-.745387,-.567705,-.415142,-.217486,.006904,.147421,.411245,.678266];measuredPiers.forEach((a,k)=>facadeEdges[13+k]=a);"
assert line in js;js=js.replace(line,'')
(O/'build_bays.js').write_text(js,encoding='utf-8')
export=(R/'export_movie_bays_v23.cjs').read_text(encoding='utf-8').replace("'movie-bays-v23'","'movie-projection-v24'").replace('bay-fit-v23.json','bay-fit-v24.json').replace('bay-geometry-v23.json','bay-geometry-v24.json')
(R/'export_projection_bays_v24.cjs').write_text(export,encoding='utf-8')

# Right rectangle and oculus are refit to the same camera, with the same scale.
oldright=json.loads((R/'movie-windows-v21/window-fit-v21.json').read_text(encoding='utf-8'))
b=bay_spec(16)
def corners(v):
    x,y,w,h=v;return np.array([local_project(b,*c) for c in [(x-w/2,y+h),(x+w/2,y+h),(x+w/2,y),(x-w/2,y)]])
t=np.array([[1960,444],[2230,444],[2230,674],[1960,674]])
r=least_squares(lambda v:(corners(v)-t).ravel(),[-1,1.69,2.5,2.14]);x,y,w,h=r.x
b['rectangle']={'x':float(x),'bottom':float(height(y,16,True)),'width':float(w),'height':float(height(y+h,16,True)-height(y,16,True))}
def ellipse(v):
    x,y,rx,ry=v;return np.array([local_project(b,*c) for c in [(x,y+ry),(x+rx,y),(x,y-ry),(x-rx,y)]])
t=np.array([[2390,437],[2443,490],[2390,543],[2337,490]])
r=least_squares(lambda v:(ellipse(v)-t).ravel(),[1.5,3.4,.5,.5]);x,y,rx,ry=r.x
b['oculus']={'x':float(x),'centerY':float(height(y,16,True)),'radiusX':float(rx),'radiusY':float((height(y+ry,16,True)-height(y-ry,16,True))/2)}
b['roofY']=4.78;b['drainpipe']={**oldright['drainpipe'],'x':float((b['rectangle']['x']+b['rectangle']['width']/2+b['oculus']['x']-rx)/2),'top':4.45}
(O/'right-fit-v24.json').write_text(json.dumps(b,indent=2),encoding='utf-8')
js=(R/'movie-windows-v21/build_bay.js').read_text(encoding='utf-8')
js=js.replace('slab(.355,-4.595','slab(.12,-4.595').replace('roof+.11,.08,w,.085,.70','roof+.11,.025,w,.085,.30').replace('roof-.22,.035,w,.11,.55','roof-.22,.025,w,.11,.20')
(O/'build_right.js').write_text(js,encoding='utf-8')
print('FITTED_OPENINGS',[(b['index'],[(a['name'],round(a['meanErrorPixels'],2)) for a in b['openings']]) for b in bays])

