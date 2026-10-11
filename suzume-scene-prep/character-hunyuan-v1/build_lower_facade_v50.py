from pathlib import Path
import json,numpy as np,trimesh
from shapely.geometry import Polygon,box,LineString
from shapely.ops import triangulate
R=Path(__file__).parent;O=R/'poster-lower-facade-v50';S=json.loads((O/'source-lower-facade-v50.json').read_text());A=np.load(O/'source-lower-facade-v50.npz');C=np.array(S['camera']['position']);rot=np.array(S['camera']['rotation']);f=S['camera']['focalPixels'];plans={q['key']:np.zeros(q['triangles'],'u1') for q in S['objects']};members=[]
edges=(np.arange(33)-16.5)*np.pi/16;edges[13:21]=[-.745387,-.567705,-.415142,-.217486,.006904,.147421,.411245,.678266];bays={}
for i in [13,14,15]:
 a0,a1=edges[i:i+2];a=(a0+a1)/2;h=(a1-a0)/2;rad=np.array([np.sin(a),np.cos(a),0]);t=np.array([np.cos(a),-np.sin(a),0]);chord=23.5*np.cos(h);w=47*np.sin(h)+.022;bays[i]={'rad':rad,'t':t,'center':chord*rad,'chord':chord,'w':w,'half':h}
 for row in S['objects']:
  p=A[row['key']+'_vertices'][A[row['key']+'_faces']];x=(p-chord*rad)@t;d=-(p-chord*rad)@rad;z=p[:,:,2]
  sel=(abs(x)<=w/2+.13).all(1)&(d>=-.46002).all(1)&(d<= (2.01 if i==14 else .95)).all(1)&(z.max(1)<=4.44002)&(z.max(1)>.90002)
  plans[row['key']][sel]=2
  if i==14:
   # Old entrance steps and rails, including their lower portions.
   steps=(abs(x)<=1.54).all(1)&(d>=-.25002).all(1)&(d<=2.01002).all(1)&(z.min(1)>=.049)&(z.max(1)<=.901)
   plans[row['key']][steps]=1
   # The old room slab sits above the observed threshold. Replace this bay's
   # complete wedge slabs rather than burying the new door in the old floor.
   for front,back,top,bottom in [(.26,-4.53,.73,-.22),(.50,-4.55,.865,.675)]:
    inside=(abs(x)<= (chord-d)*np.tan(h)+.01203).all(1)&(d>=back-2e-5).all(1)&(d<=front+2e-5).all(1)&(z>=bottom-2e-5).all(1)&(z<=top+2e-5).all(1)
    plans[row['key']][inside]=1

cut_volumes=[]
# The third observed large window extends across the former 15/16 division.
# Extend the flat facade and trim the intersecting old wall/partition surfaces.
b=bays[15];cut={'x':[b['w']/2-.45,b['w']/2+.35],'d':[-.65,.70],'z':[.20,4.44002],'center':b['center'].tolist(),'tangent':b['t'].tolist(),'radial':b['rad'].tolist()};cut_volumes.append(cut)
for row in S['objects']:
 p=A[row['key']+'_vertices'][A[row['key']+'_faces']];x=(p-b['center'])@b['t'];d=-(p-b['center'])@b['rad'];z=p[:,:,2]
 candidate=(x.max(1)>=cut['x'][0])&(x.min(1)<=cut['x'][1])&(d.max(1)>=cut['d'][0])&(d.min(1)<=cut['d'][1])&(z.max(1)>=cut['z'][0])&(z.min(1)<=cut['z'][1])
 plans[row['key']][candidate&(plans[row['key']]==0)]=3

# Identify the complete original bench and old staircase by welded component
# boundaries, including bevel/rotated vertices beyond their nominal boxes.
components=json.loads((O/'lower-fixture-components-v50.json').read_text())
bench_ids=[1018,1025,1027,1028,1029,1030,1031,1035,1036,1037,1038,1039,1040,1058,1059,1072]
stair_ids=[1088,1101,1102,1103,1104,1105,1147]
for component in components:
 if component['component'] not in bench_ids+stair_ids:continue
 for key,ids in component['parts'].items():plans[key][ids]=1
# Retain the original geometric footprint audit as a cross-check.
bench_counts={}
for row in S['objects']:
 p=A[row['key']+'_vertices'][A[row['key']+'_faces']]-np.array([-13,16,.16]);a=-.6;x=p[:,:,0]*np.cos(a)+p[:,:,1]*np.sin(a);y=-p[:,:,0]*np.sin(a)+p[:,:,1]*np.cos(a);z=p[:,:,2]
 selected=(abs(x)<=.91).all(1)&(y>=-.40).all(1)&(y<=.36).all(1)&(z>=-.001).all(1)&(z<=1.201).all(1)&(z.max(1)>.08)
 if selected.any():plans[row['key']][selected]=1;bench_counts[row['key']]=int(selected.sum())

def world(p,b,d):
 p=np.asarray(p);return b['center']+p[...,0,None]*(b['chord']-d)/b['chord']*b['t']-d*b['rad']+np.stack([np.zeros(p.shape[:-1]),np.zeros(p.shape[:-1]),p[...,1]],axis=-1)
def lift(u,v,b):
 ray=np.array([(u-354)/f,(500-v)/f,-1])@rot.T;p=C+ray*np.dot(b['center']-C,b['rad'])/np.dot(ray,b['rad']);return np.array([np.dot(p-b['center'],b['t']),p[2]])
def add(name,poly,b,front,back,kind,meta=None,frontmat=0,side=1,subdiv=0):
 assert poly.is_valid and poly.geom_type=='Polygon' and poly.area>1e-8,(name,poly)
 vv=[];ff=[];mi=[];lookup={}
 def vid(p,d):
  v=world(np.asarray(p),b,d);key=tuple(np.round(v,9))
  if key not in lookup:lookup[key]=len(vv);vv.append(v)
  return lookup[key]
 tris=[t for t in triangulate(poly) if poly.covers(t)];assert abs(sum(t.area for t in tris)-poly.area)<1e-7,(name,'cap triangulation')
 for tri in tris:
  points=np.array(tri.exterior.coords)[:3]
  for d,mat in [(front,frontmat),(back,side)]:ff.append([vid(p,d) for p in points]);mi.append(mat)
 for ring in [poly.exterior,*poly.interiors]:
  p=np.array(ring.coords)
  for a,c in zip(p[:-1],p[1:]):
   ids=[vid(a,front),vid(c,front),vid(c,back),vid(a,back)];ff.extend([[ids[0],ids[1],ids[2]],[ids[0],ids[2],ids[3]]]);mi.extend([side,side])
 mesh=trimesh.Trimesh(vv,ff,process=False);mesh.fix_normals();assert mesh.is_watertight and mesh.volume>0,(name,mesh.is_watertight,mesh.volume)
 for _ in range(subdiv):mesh=mesh.subdivide();mi=np.repeat(mi,4).tolist()
 members.append({'name':name,'kind':kind,'verticesNative':mesh.vertices.round(8).tolist(),'triangles':mesh.faces.tolist(),'materialIndices':mi,'bay':next(i for i,q in bays.items() if q is b),**(meta or {})})
def rect(name,b,x0,x1,z0,z1,front,back,kind='frame',**kwargs):add(name,box(x0,z0,x1,z1),b,front,back,kind,**kwargs)
def bar(name,b,points,width,front=.025,back=-.035,kind='mullion'):add(name,LineString(points).buffer(width/2,cap_style=2,join_style=2),b,front,back,kind)
def arch(x,a,z0,zt,rise,n=48):
 spring=zt-rise;th=np.linspace(np.pi,0,n+1);return Polygon([[x-a,z0],*np.c_[x+a*np.cos(th),spring+rise*np.sin(th)].tolist(),[x+a,z0]])
records=[]
# bounds are observed image coordinates at 708 x 1000, including partially
# occluded endpoints. Depths and unseen backs are reconstructed assumptions.
inputs=[('left rectangular window',13,'rect',[-8,29.3,630.4,674.7,None]),('left arched window',13,'arch',[43.3,64.0,631.0,674.0,641.1]),('entrance',14,'door',[104.0,142.4,636.6,689.1,652.8]),('wide window 0',15,'rect',[170.8,198.2,635.5,675.4,None]),('wide window 1',15,'rect',[204.0,231.0,636.1,675.7,None]),('wide window 2',15,'rect',[237.0,264.0,636.8,676.0,None])]
holes={i:[] for i in bays};probes=[]
for name,i,kind,obs in inputs:
 b=bays[i];u0,u1,vt,vb,vs=obs;u=(u0+u1)/2;mid=(vt+vb)/2;left=lift(u0,mid,b)[0];right=lift(u1,mid,b)[0];left=max(left,-b['w']/2+.12);right=min(right,b['w']/2+(.19 if i==15 else -.12));x=(left+right)/2;a=(right-left)/2
 if name!='left rectangular window':x=lift(u,mid,b)[0];left=x-a;right=x+a
 zt=lift(u,vt,b)[1];z0=lift(u,vb,b)[1];rise=zt-lift(u,vs,b)[1] if vs else 0
 poly=arch(x,a,z0,zt,rise) if kind in ['arch','door'] else box(left,z0,right,zt);holes[i].append(poly);rec={'id':name,'bay':i,'kind':kind,'x':x,'halfWidth':a,'z':[z0,zt],'rise':rise,'reference':obs};records.append(rec);tag='Poster '+name+' v50'
 inset=.115 if kind=='door' else .042
 outer=arch(x,a+inset,z0-.025,zt+(.16 if kind=='door' else inset),rise+(.13 if kind=='door' else inset)) if kind in ['arch','door'] else box(left-inset,z0-inset,right+inset,zt+inset)
 add(tag+' surround',outer.difference(poly),b,.075,-.12,'surround',{'opening':name},subdiv=1)
 if kind=='door':
  spring=zt-rise
  fan=poly.intersection(box(left-1,spring,right+1,zt+1));add(tag+' fan glazing',fan,b,-.13,-.146,'glass',{'opening':name},side=2,subdiv=2)
  # A concentric grille follows the observed fanlight, instead of ten heavy
  # straight spokes meeting on a pure black hole.
  th=np.linspace(np.pi,0,49)
  for j,scale in enumerate([.97,.63]):bar(tag+f' fan curved rail {j}',b,np.c_[x+a*scale*np.cos(th),spring+rise*scale*np.sin(th)],.017,-.072,-.115)
  for j in range(1,6):
   theta=j*np.pi/6;bar(tag+f' fan spoke {j}',b,[[x,spring],[x+a*.975*np.cos(theta),spring+rise*.975*np.sin(theta)]],.014,-.066,-.11)
  rect(tag+' transom',b,left,right,spring-.030,spring+.030,-.035,-.14)
  split=z0+(spring-z0)*.39
  for k,(xl,xr) in enumerate([(left+.02,x-.009),(x+.009,right-.02)]):
   panel=box(xl,z0,xr,split);add(tag+f' leaf {k} lower panel',panel,b,-.065,-.17,'doorPanel',{'opening':name},subdiv=2)
   add(tag+f' leaf {k} glazing',box(xl,split,xr,spring-.03),b,-.128,-.143,'glass',{'opening':name},side=2,subdiv=2)
   for side,xx in enumerate([xl,xr]):rect(tag+f' leaf {k} stile {side}',b,xx-.025,xx+.025,z0,spring,-.030,-.19)
   for j,z in enumerate([z0+.04,split,spring-.025]):rect(tag+f' leaf {k} rail {j}',b,xl,xr,z-.025,z+.025,-.025,-.18)
   for j in range(1,5):bar(tag+f' leaf {k} grille upright {j}',b,[[xl+(xr-xl)*j/5,split],[xl+(xr-xl)*j/5,spring-.06]],.012,-.040,-.075)
   for j in range(1,4):bar(tag+f' leaf {k} grille crossbar {j}',b,[[xl,split+(spring-split)*j/4],[xr,split+(spring-split)*j/4]],.012,-.039,-.078)
   # Shallow rectangular lower-panel molding has real depth on both leaves.
   inner=box(xl+.07,z0+.10,xr-.07,split-.075);add(tag+f' leaf {k} lower panel molding',inner.buffer(.018,join_style=2).difference(inner),b,-.022,-.072,'doorMolding')
   hx=x+(-.085 if k==0 else .085);hz=split+.19;bar(tag+f' leaf {k} pull handle',b,[[hx,hz-.09],[hx-.018,hz-.065],[hx-.018,hz+.065],[hx,hz+.09]],.022,.025,-.035,'handle')
  # Three treads and low side cheeks match the narrow observed stair run.
  treadhalf=a*.56;stepx=x+a*.20
  for j in range(3):rect(tag+f' step {j}',b,stepx-treadhalf,stepx+treadhalf,z0-j*.125-.16,z0-j*.125,.35+j*.35,-.17,'step',subdiv=1)
  for side in [-1,1]:
   xx=stepx+side*(treadhalf+.045);vv=[]
   for depth,lo,hi in [(-.15,z0-.13,z0+.045),(1.12,z0-.45,z0-.26)]:
    for px,pz in [(xx-.045,lo),(xx+.045,lo),(xx+.045,hi),(xx-.045,hi)]:vv.append(world(np.array([px,pz]),b,depth))
   ff=[[0,1,2],[0,2,3],[4,6,5],[4,7,6]]
   for j in range(4):k=(j+1)%4;ff.extend([[j,k,k+4],[j,k+4,j+4]])
   mesh=trimesh.Trimesh(vv,ff,process=False);mesh.fix_normals();assert mesh.is_watertight and mesh.volume>0
   members.append({'name':tag+f' stair cheek {side}','kind':'step','verticesNative':mesh.vertices.round(8).tolist(),'triangles':mesh.faces.tolist(),'materialIndices':[0]*len(mesh.faces),'bay':i})
  # Lowered interior floor spans the original wedge footprint.
  rect(tag+' interior floor',b,-b['w']/2,b['w']/2,z0-.24,z0,.30,-4.55,'floor',frontmat=1,side=1)
  rect(tag+' back wall foot',b,-b['w']/2,b['w']/2,z0,.801,-4.36,-4.68,'partition',frontmat=1,side=1)
  for side in [-1,1]:rect(tag+f' side wall foot {side}',b,side*b['w']/2-.11,side*b['w']/2+.11,z0,.851,0,-4.55,'partition',frontmat=1,side=1)
 else:
  add(tag+' glazing',poly,b,-.125,-.14,'glass',{'opening':name},side=2,subdiv=2)
  transom=zt-rise if kind=='arch' else zt-.39
  for j in range(1,4):bar(tag+f' upright {j}',b,[[left+(right-left)*j/4,z0],[left+(right-left)*j/4,transom]],.027 if j==2 else .015)
  for j in range(1,4):bar(tag+f' crossbar {j}',b,[[left,z0+(transom-z0)*j/4],[right,z0+(transom-z0)*j/4]],.020)
  rect(tag+' transom',b,left,right,transom-.030,transom+.030,.035,-.10)
  if kind=='arch':
   for j in [1,2,3]:
    theta=j*np.pi/4;bar(tag+f' fan spoke {j}',b,[[x,transom],[x+a*np.cos(theta),transom+rise*np.sin(theta)]],.015)
  else:
   for j in range(1,6):bar(tag+f' transom upright {j}',b,[[left+(right-left)*j/6,transom],[left+(right-left)*j/6,zt]],.018)
   bar(tag+' transom crossbar',b,[[left,(zt+transom)/2],[right,(zt+transom)/2]],.015)
  rect(tag+' sill',b,left-.065,right+.065,z0-.12,z0-.035,.22,-.18,'sill')
 for xf in [.25,.5,.75]:
  for zf in [.25,.55]:probes.append({'opening':name,'point':world(np.array([left+(right-left)*xf,z0+(zt-z0)*zf]),b,.5).tolist(),'direction':b['rad'].tolist(),'distance':.82})

for i,b in bays.items():
 poly=box(-b['w']/2,.20,b['w']/2+(.31 if i==15 else 0),4.44)
 for hole in holes[i]:poly=poly.difference(hole)
 add(f'Poster lower facade wall bay {i} v50',poly,b,0,-.46,'wall',subdiv=2)
 # The broad panel above each window group is bounded by a projecting sill.
 if i in [13,15]:
  selected=[q for q in records if q['bay']==i and q['kind']=='rect'];xl=min(q['x']-q['halfWidth'] for q in selected);xr=max(q['x']+q['halfWidth'] for q in selected);top=max(q['z'][1] for q in selected)
  rect(f'Poster window group hood bay {i} v50',b,xl-.12,xr+.12,top+.11,top+.24,.34,-.12,'hood')
  rect(f'Poster window group hood drip bay {i} v50',b,xl-.14,xr+.14,top+.23,top+.27,.38,-.12,'hood')
 else:
  rec=next(q for q in records if q['kind']=='door');top=rec['z'][1]+.75
  rect('Poster entrance lintel ledge v50',b,-b['w']/2+.34,b['w']/2-.34,top-.14,top,.31,-.10,'hood')
 # Continuous upper fascia at the transition to the rebuilt arch storey.
 rect(f'Poster lower-storey upper molding bay {i} v50',b,-b['w']/2,b['w']/2,4.27,4.40,.28,-.12,'cornice')
 for side in [-1,1]:
  # Only create one shared pier at each seam.
  if side==-1 and i>13:continue
  x=side*(b['w']/2-.045)+(.31 if i==15 and side==1 else 0);rect(f'Poster lower pier bay {i} side {side} v50',b,x-.22,x+.22,.70,4.30,.26,-.10,'pier')
  rect(f'Poster lower pier base bay {i} side {side} v50',b,x-.28,x+.28,.66,1.02,.37,-.10,'pier')
  rect(f'Poster lower pier capital bay {i} side {side} v50',b,x-.30,x+.30,4.08,4.31,.40,-.10,'pier')

np.savez_compressed(O/'lower-facade-removal-v50.npz',**plans)
out={'revision':50,'sourceNativeSha256':S['sourceNativeSha256'],'sourceObjects':S['objects'],'sourceGeometryFile':'poster-lower-facade-v50/source-lower-facade-v50.npz','camera':S['camera'],'clipHeight':.20,'openings':records,'members':members,'structuralProbeSpecifications':probes,'removedBenchTriangles':bench_counts,'changes':{k:{'clip':int((p==2).sum()),'remove':int((p==1).sum())} for k,p in plans.items() if p.any()},'materials':['Reference-calibrated upper facade pigments v48','Poster upper window recessed faces v48','Poster upper window glazing edge v48'],'referenceMeasurementUncertaintyPixels':1.5,'oneToOneComplete':False,'scope':'Left lower facade openings, entrance and steps; hidden room construction and glazing remain inferred.'}
out['removedOriginalComponents']={'bench':bench_ids,'oldStair':stair_ids}
out['cutVolumes']=cut_volumes
(O/'lower-facade-geometry-v50.json').write_text(json.dumps(out,separators=(',',':')));print('LOWER_FACADE_50_BUILT',len(members),sum(len(q['triangles']) for q in members),'triangles',out['changes'],'bench',bench_counts)
