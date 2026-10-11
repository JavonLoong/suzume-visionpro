from pathlib import Path
import numpy as np,json
from scipy.interpolate import CubicSpline
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix,diags
from scipy.sparse.csgraph import dijkstra
from scipy.sparse.linalg import spsolve
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).parent;O=R/'movie-collar-v37';a=np.load(O/'body-source-v37.npz');topo=np.load(O/'collar-topology-v37.npz');w=a['world'];faces=a['faces'];weld=topo['weldedVertices'];order=topo['collarOrder'];loop=weld[order]
# Parameterize by projected seam length, so the vertical sawteeth do not consume
# disproportionate seam length. Periodic harmonics preserve the front opening.
dist=np.linalg.norm(np.diff(np.vstack([loop[:,:2],loop[0,:2]]),axis=0),axis=1);t=np.r_[0,np.cumsum(dist[:-1])]/dist.sum();angle=t*2*np.pi
columns=[np.ones(len(t))]
for n in range(1,7):columns.extend([np.cos(n*angle),np.sin(n*angle)])
X=np.array(columns).T;penalty=np.diag([0]+[.002*n**4 for n in range(1,7) for _ in range(2)])
weights=np.maximum((dist+np.roll(dist,1))/2,.0001);weights/=weights.mean()
coef=np.linalg.solve(X.T@(weights[:,None]*X)+penalty,X.T@(weights[:,None]*loop));target=X@coef
delta=target-loop;tree=cKDTree(loop);nearest,indices=tree.query(w,k=5);d=nearest[:,0];weight=np.exp(-(nearest/.012)**2);weighted=(delta[indices]*weight[:,:,None]).sum(1)/np.maximum(weight.sum(1),1e-20)[:,None]
blend=np.clip(1-d/.035,0,1);blend=blend*blend*(3-2*blend);after=w+weighted*blend[:,None]
# Every duplicate UV vertex of a seam location follows the same target.
for i,j in enumerate(order):after[topo['inverse']==j]=target[i]
direct_after=after.copy()
# Spread seam movement through the connected cloth, not through nearby but
# unrelated surfaces. A positive graph Laplacian gives a smooth displacement.
wf=topo['faces'];edges=np.unique(np.sort(np.concatenate([wf[:,[0,1]],wf[:,[1,2]],wf[:,[2,0]]]),axis=1),axis=0);edges=edges[edges[:,0]!=edges[:,1]]
length=np.linalg.norm(weld[edges[:,0]]-weld[edges[:,1]],axis=1);row=np.r_[edges[:,0],edges[:,1]];col=np.r_[edges[:,1],edges[:,0]]
graph=coo_matrix((np.r_[length,length],(row,col)),shape=(len(weld),len(weld))).tocsr();distance=dijkstra(graph,directed=False,indices=order,min_only=True,limit=.055)
movable=np.flatnonzero((distance<.055)&~np.isin(np.arange(len(weld)),order));fixed_delta=np.zeros_like(weld);fixed_delta[order]=delta
weight=np.r_[1/np.maximum(length,.0001),1/np.maximum(length,.0001)];adj=coo_matrix((weight,(row,col)),shape=graph.shape).tocsr();lap=diags(np.asarray(adj.sum(axis=1)).ravel())-adj
rhs=adj[movable]@fixed_delta;displacement=fixed_delta.copy();displacement[movable]=spsolve(lap[movable][:,movable].tocsc(),rhs)
after=w+displacement[topo['inverse']]
# Keep triangle orientation while the sawteeth flatten. Most corrections move
# adjacent cloth vertices; boundary-only slivers may move by a fraction of a mm.
working=weld+displacement;free=distance<.055;mobility=free.astype(float);mobility[order]=.01
active=np.flatnonzero(np.any(free[wf],axis=1));old_tri=weld[wf[active]];old_normals=np.cross(old_tri[:,1]-old_tri[:,0],old_tri[:,2]-old_tri[:,0]);old_area=np.linalg.norm(old_normals,axis=1);reference_normal=old_normals/np.maximum(old_area[:,None],1e-20);target_area=np.maximum(.025*old_area,1e-11)
for iteration in range(240):
 tri=working[wf[active]];signed=(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])*reference_normal).sum(1);bad=np.flatnonzero((signed<target_area*.99)&(old_area>1e-10))
 if not len(bad):break
 for k in bad:
  ids=wf[active[k]];p0,p1,p2=working[ids];normal=reference_normal[k];signed=np.dot(np.cross(p1-p0,p2-p0),normal);gradient=np.cross(np.array([p1-p2,p2-p0,p0-p1]),normal);m=mobility[ids];denom=np.sum(m[:,None]*gradient*gradient)
  if denom<1e-20:continue
  step=m[:,None]*gradient*(target_area[k]-signed)/denom;peak=np.linalg.norm(step,axis=1).max()
  if peak>.003:step*=.003/peak
  working[ids]+=step
displacement=working-weld;after=w+displacement[topo['inverse']];boundary_correction=np.linalg.norm(working[order]-target,axis=1);target=working[order]
changed=np.linalg.norm(after-w,axis=1)>1e-9
def normals(p):
 tri=p[faces];return np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
n0=normals(w);n1=normals(after);areas=np.linalg.norm(n1,axis=1)/2;normdot=(n0*n1).sum(1)/np.maximum(np.linalg.norm(n0,axis=1)*np.linalg.norm(n1,axis=1),1e-20);modified=np.any(changed[faces],axis=1)
report={'revision':37,'seamVertices':len(loop),'changedVertices':int(changed.sum()),'modifiedTriangles':int(modified.sum()),'maximumDisplacement':float(np.linalg.norm(after-w,axis=1).max()),'maximumSeamDisplacement':float(np.linalg.norm(delta,axis=1).max()),'flippedModifiedTriangles':int((modified&(normdot<0)).sum()),'almostDegenerateModifiedTriangles':int((modified&(areas<1e-10)).sum()),'seamBeforeBounds':[loop.min(0).tolist(),loop.max(0).tolist()],'seamAfterBounds':[target.min(0).tolist(),target.max(0).tolist()],'oneToOneComplete':False}
report['deformation']='Harmonic displacement in a 55 mm geodesic collar band';report['harmonicInteriorVertices']=len(movable)
report['orientationRepairIterations']=iteration;report['maximumSubmillimetreSeamCorrection']=float(boundary_correction.max());assert report['flippedModifiedTriangles']==0,report
np.savez_compressed(O/'collar-fit-v37.npz',before=w,after=after,changedMask=changed,seamBefore=loop,seamAfter=target,seamOrder=order,seamParameter=t)
(O/'fit-v37.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
fig,ax=plt.subplots(1,3,figsize=(12,4))
for axis,(x,y,label) in zip(ax,[(0,1,'Top'),(0,2,'Front'),(1,2,'Side')]):
 axis.plot(np.r_[loop[:,x],loop[0,x]],np.r_[loop[:,y],loop[0,y]],color='#b17965',lw=.8,label='Existing cut');axis.plot(np.r_[target[:,x],target[0,x]],np.r_[target[:,y],target[0,y]],color='#187e81',lw=1.6,label='Smooth seam');axis.set_title(label);axis.set_aspect('equal');axis.grid(alpha=.2)
ax[0].legend();fig.suptitle('Collar boundary fit — native world coordinates (m)');fig.tight_layout();fig.savefig(O/'collar-boundary-fit-v37.png',dpi=160);plt.close(fig)
