from pathlib import Path
import json,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).parent;O=R/'poster-steel-v39';D=json.loads((O/'steel-geometry-v39.json').read_text());members={q['name']:q for q in D['members']}
trees={};vertices={};bounds={}
for name,q in members.items():
    vertices[name]=np.array(q['verticesNative']);bounds[name]=[vertices[name].min(0),vertices[name].max(0)]
    trees[name]=BVHTree.FromPolygons(q['verticesNative'],q['triangles'],all_triangles=True)
direction=Vector((.237,.579,.780)).normalized()
def inside(name,p):
    origin=Vector(p);hits=0
    for i in range(32):
        loc,normal,index,dist=trees[name].ray_cast(origin,direction,100)
        if loc is None:break
        hits+=1;origin=loc+direction*1e-5
    return bool(hits%2)
def intersects(a,b):
    for source,target in [(a,b),(b,a)]:
        lo,hi=bounds[target];pts=vertices[source];pts=pts[np.all((pts>lo-1e-5)&(pts<hi+1e-5),axis=1)]
        for p in pts:
            if inside(target,p):return {'verified':True,'insidePoint':p.tolist(),'source':source,'inside':target}
    return {'verified':False}
pairs=[
 ('Upper continuous tie','right I-section post 2'),('Upper continuous tie','right I-section post 3'),
 ('Bent broken central beam','right I-section post 2'),('Bent broken central beam','right I-section post 3'),
 ('Short broken right tie','right I-section post 3'),('Lower broken ring beam','right I-section post 2'),('Lower broken ring beam','right I-section post 3'),
 ('Curved left supporting bracket','right I-section post 2'),('Curved right supporting bracket','right I-section post 2'),
 ('Curved left supporting bracket','Bent broken central beam'),('Curved right supporting bracket','Bent broken central beam'),
 ('Bracket horizontal brace','Curved left supporting bracket'),('Bracket horizontal brace','Curved right supporting bracket'),
 ('Hanging central tie','Bent broken central beam'),('Hanging lower tie','Lower broken ring beam'),
 ('Bracket left upright','Bent broken central beam'),('Bracket left upright','Bracket horizontal brace'),
 ('Bracket diagonal brace','Bent broken central beam'),('Bracket diagonal brace','Bracket horizontal brace'),
 ('Bracket right diagonal','Bent broken central beam'),('Bracket right diagonal','Curved right supporting bracket'),
 ('Bracket right upright','Bent broken central beam'),('Bracket right upright','Curved right supporting bracket')]
rows=[]
for a,b in pairs:
    result=intersects('Poster '+a,'Poster '+b);rows.append({'a':a,'b':b,**result})
(O/'connections-v39.json').write_text(json.dumps({'revision':39,'checks':rows,'allCheckedConnectionsIntersect':all(q['verified'] for q in rows),'method':'A mesh vertex lies inside the other closed member, using ray parity; contact-only joints may require separate checking.'},indent=2),encoding='utf-8')
print(json.dumps([{'a':q['a'],'b':q['b'],'verified':q['verified']} for q in rows],indent=2),flush=True)
