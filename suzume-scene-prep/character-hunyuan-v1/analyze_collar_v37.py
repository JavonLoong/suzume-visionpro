from pathlib import Path
import numpy as np,json
from collections import defaultdict,Counter
R=Path(__file__).parent;O=R/'movie-collar-v37';a=np.load(O/'body-source-v37.npz');w=a['world'];f=a['faces']
keys,unique,inv=np.unique(np.round(w,5),axis=0,return_index=True,return_inverse=True);weld=w[unique];wf=inv[f];edges=np.sort(np.concatenate([wf[:,[0,1]],wf[:,[1,2]],wf[:,[2,0]]]),axis=1);e,n=np.unique(edges,axis=0,return_counts=True);boundary=e[(n==1)&(e[:,0]!=e[:,1])]
adj=defaultdict(list)
for x,y in boundary:adj[int(x)].append(int(y));adj[int(y)].append(int(x))
seen=set();components=[]
for root in adj:
 if root in seen:continue
 stack=[root];seen.add(root);ids=[]
 while stack:
  i=stack.pop();ids.append(i)
  for j in adj[i]:
   if j not in seen:stack.append(j);seen.add(j)
 components.append(ids)
components.sort(key=lambda ids:weld[ids,2].max(),reverse=True)
report=[]
for i,ids in enumerate(components):
 if weld[ids,2].max()<2.3:continue
 report.append({'component':i,'vertices':len(ids),'degrees':dict(Counter(len(adj[j]) for j in ids)),'minimum':weld[ids].min(0).tolist(),'maximum':weld[ids].max(0).tolist(),'originalVertexCount':int(np.isin(inv,ids).sum())})
collar=components[0];assert min(weld[collar,2])>2.4
order=[collar[0]];prev=-1;cur=collar[0]
for _ in range(len(collar)):
 choices=[j for j in adj[cur] if j!=prev];assert len(choices) in [1,2];nxt=choices[0]
 if nxt==order[0]:break
 order.append(nxt);prev,cur=cur,nxt
assert len(order)==len(collar)
np.savez_compressed(O/'collar-topology-v37.npz',weldedVertices=weld,inverse=inv,faces=wf,boundaryEdges=boundary,collarOrder=order,originalUnique=unique)
(O/'boundary-inspection-v37.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
