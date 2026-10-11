from pathlib import Path
import ast,json,numpy as np,trimesh
from shapely.geometry import Polygon,box,LineString,Point
from shapely import constrained_delaunay_triangles
R=Path(__file__).parent;O=R/'poster-right-facade-v54';S=json.loads((O/'source-right-facade-v54.json').read_text());A=np.load(O/'source-right-facade-v54.npz');C=np.array(S['camera']['position']);rot=np.array(S['camera']['rotation']);f=S['camera']['focalPixels'];plans={q['key']:np.zeros(q['triangles'],'u1') for q in S['objects']};members=[]
edges=(np.arange(33)-16.5)*np.pi/16;edges[13:21]=[-.745387,-.567705,-.415142,-.217486,.006904,.147421,.411245,.678266];bays={};cut_volumes=[]
for i in [17,18,19]:
 a0,a1=edges[i:i+2];a=(a0+a1)/2;h=(a1-a0)/2;rad=np.array([np.sin(a),np.cos(a),0]);t=np.array([np.cos(a),-np.sin(a),0]);chord=23.5*np.cos(h);w=47*np.sin(h)+.022;bays[i]={'rad':rad,'t':t,'center':chord*rad,'chord':chord,'w':w,'half':h}
 cut_volumes.append({'x':[-w/2-.14,w/2+.14],'d':[-.46002,2.01 if i==17 else .95002],'z':[-.20 if i==17 else .20,4.44002],'center':(rad*chord).tolist(),'tangent':t.tolist(),'radial':rad.tolist()})
 if i==17:
  for row in S['objects']:
   p=A[row['key']+'_vertices'][A[row['key']+'_faces']];x=(p-chord*rad)@t;d=-(p-chord*rad)@rad;z=p[:,:,2]
   for front,back,top,bottom in [(.26,-4.53,.73,-.22),(.50,-4.55,.865,.675)]:
    inside=(abs(x)<=(chord-d)*np.tan(h)+.01204).all(1)&(d>=back-2e-5).all(1)&(d<=front+2e-5).all(1)&(z>=bottom-2e-5).all(1)&(z<=top+2e-5).all(1);plans[row['key']][inside]=1
for row in S['objects']:
 p=A[row['key']+'_vertices'][A[row['key']+'_faces']]
 for cut in cut_volumes:
  x=(p-cut['center'])@np.array(cut['tangent']);d=-(p-cut['center'])@np.array(cut['radial']);z=p[:,:,2]
  candidate=(x.max(1)>=cut['x'][0])&(x.min(1)<=cut['x'][1])&(d.max(1)>=cut['d'][0])&(d.min(1)<=cut['d'][1])&(z.max(1)>=cut['z'][0])&(z.min(1)<=cut['z'][1]);plans[row['key']][candidate&(plans[row['key']]==0)]=3

# The established lower-facade extrusion helpers preserve wedge-shaped depth,
# closed backs and shared edges; use constrained cap triangulation for holes.
src=(R/'build_lower_facade_v50.py').read_text();tree=ast.parse(src)
for n in tree.body:
 if isinstance(n,ast.FunctionDef) and n.name in ['world','lift','add','rect','bar','arch']:
  code=ast.get_source_segment(src,n).replace('triangulate(poly)','constrained_delaunay_triangles(poly).geoms');exec(compile(code,'facade extrusion helpers','exec'))

inputs=[
 ('right entrance',17,'door',[373.2,430.8,636.0,689.3,653.2]),
 ('right narrow arch',18,'arch',[458.0,476.5,633.8,673.4,643.6]),
 ('right double window 0',18,'rect',[489.5,523.0,634.5,674.6,644.1]),
 ('right double window 1',18,'rect',[529.0,559.0,633.5,674.0,643.3]),
 ('right triple window 0',19,'rect',[577.7,612.1,629.4,674.3,641.3]),
 ('right triple window 1',19,'rect',[620.0,655.0,628.0,674.0,640.5]),
 ('right triple window 2',19,'rect',[663.3,700.0,626.8,673.5,639.3])]
holes={i:[] for i in bays};records=[];probes=[]
for name,i,kind,obs in inputs:
 b=bays[i];u0,u1,vt,vb,vs=obs;u=(u0+u1)/2;mid=(vt+vb)/2;left=lift(u0,mid,b)[0];right=lift(u1,mid,b)[0];x=(left+right)/2;a=(right-left)/2;zt=lift(u,vt,b)[1];z0=lift(u,vb,b)[1];transom=lift(u,vs,b)[1];rise=zt-transom if kind in ['arch','door'] else 0
 assert left>-b['w']/2+.08 and right<b['w']/2-.08,(name,left,right,b['w'])
 poly=arch(x,a,z0,zt,rise) if kind in ['arch','door'] else box(left,z0,right,zt);holes[i].append(poly);records.append({'id':name,'bay':i,'kind':kind,'x':x,'halfWidth':a,'z':[z0,zt],'rise':rise,'transomZ':transom,'reference':obs});tag='Poster '+name+' v54';inset=.115 if kind=='door' else .042
 outer=arch(x,a+inset,z0-.025,zt+(.13 if kind=='door' else inset),rise+(.11 if kind=='door' else inset)) if kind in ['arch','door'] else box(left-inset,z0-inset,right+inset,zt+inset)
 add(tag+' surround',outer.difference(poly),b,.075,-.12,'surround',{'opening':name},subdiv=1)
 if kind=='door':
  fan=poly.intersection(box(left-1,transom,right+1,zt+1));add(tag+' fan glazing',fan,b,-.13,-.146,'glass',{'opening':name},side=2,subdiv=2);th=np.linspace(np.pi,0,49)
  for j,scale in enumerate([.98,.48]):bar(tag+f' fan curved rail {j}',b,np.c_[x+a*scale*np.cos(th),transom+rise*scale*np.sin(th)],.022,-.045,-.09)
  for j in range(1,7):
   theta=j*np.pi/7;bar(tag+f' fan spoke {j}',b,[[x+a*.48*np.cos(theta),transom+rise*.48*np.sin(theta)],[x+a*.98*np.cos(theta),transom+rise*.98*np.sin(theta)]],.018,-.04,-.09)
  rect(tag+' transom',b,left,right,transom-.032,transom+.032,.01,-.14)
  split=lift(u,674.5,b)[1]
  for k,(xl,xr) in enumerate([(left+.02,x-.014),(x+.014,right-.02)]):
   add(tag+f' leaf {k} lower panel',box(xl,z0,xr,split),b,-.065,-.17,'doorPanel',{'opening':name},subdiv=2);add(tag+f' leaf {k} glazing',box(xl,split,xr,transom-.035),b,-.128,-.143,'glass',{'opening':name},side=2,subdiv=2)
   for side,xx in enumerate([xl,xr]):rect(tag+f' leaf {k} stile {side}',b,xx-.033,xx+.033,z0,transom,-.025,-.19)
   for j,z in enumerate([z0+.04,split,transom-.035]):rect(tag+f' leaf {k} rail {j}',b,xl,xr,z-.027,z+.027,-.022,-.18)
   midx=(xl+xr)/2;bar(tag+f' leaf {k} center glazing upright',b,[[midx,split],[midx,transom-.06]],.02,-.03,-.07)
   # Diamond-like grille segments visible in the narrow right door light.
   gz=split+(transom-split)*.57;gw=(xr-xl)*.43;gh=(transom-split)*.17
   bar(tag+f' leaf {k} glazing diamond',b,[[midx-gw,gz],[midx,gz+gh],[midx+gw,gz],[midx,gz-gh],[midx-gw,gz]],.023,-.025,-.075)
   hx=x+(-.07 if k==0 else .07);hz=split+.22;bar(tag+f' leaf {k} pull handle',b,[[hx,hz-.09],[hx-.018,hz-.06],[hx-.018,hz+.06],[hx,hz+.09]],.022,.025,-.035,'handle')
  step_center=x+.08;treadhalf=a*.87
  for j in range(3):rect(tag+f' step {j}',b,step_center-treadhalf,step_center+treadhalf,z0-j*.12-.16,z0-j*.12,.35+j*.33,-.17,'step',subdiv=1)
  rect(tag+' stair foundation',b,step_center-treadhalf-.025,step_center+treadhalf+.025,-.20,z0-.24-.16+.003,1.03,-.20,'foundation',frontmat=1,side=1)
  rect(tag+' interior floor',b,-b['w']/2,b['w']/2,z0-.24,z0,.30,-4.55,'floor',frontmat=1,side=1);rect(tag+' back wall foot',b,-b['w']/2,b['w']/2,z0,.801,-4.36,-4.68,'partition',frontmat=1,side=1)
  for side in [-1,1]:rect(tag+f' side wall foot {side}',b,side*b['w']/2-.11,side*b['w']/2+.11,z0,.851,0,-4.55,'partition',frontmat=1,side=1)
 else:
  add(tag+' glazing',poly,b,-.125,-.14,'glass',{'opening':name},side=2,subdiv=2);divisions=4 if kind=='arch' else 6
  for j in range(1,divisions):bar(tag+f' upright {j}',b,[[left+(right-left)*j/divisions,z0],[left+(right-left)*j/divisions,transom]],.058 if j==divisions//2 and kind=='rect' else .020)
  for j in range(1,4):bar(tag+f' crossbar {j}',b,[[left,z0+(transom-z0)*j/4],[right,z0+(transom-z0)*j/4]],.023)
  rect(tag+' transom',b,left,right,transom-.032,transom+.032,.038,-.10)
  if kind=='arch':
   for j in [1,2,3]:
    theta=j*np.pi/4;bar(tag+f' fan spoke {j}',b,[[x,transom],[x+a*np.cos(theta),transom+rise*np.sin(theta)]],.020)
  else:
   for j in range(1,7):bar(tag+f' transom upright {j}',b,[[left+(right-left)*j/7,transom],[left+(right-left)*j/7,zt]],.021)
   bar(tag+' transom crossbar',b,[[left,(zt+transom)/2],[right,(zt+transom)/2]],.020)
  rect(tag+' sill',b,left-.065,right+.065,z0-.13,z0-.035,.22,-.18,'sill')
 for xf in [.22,.5,.78]:
  for zf in [.22,.55]:probes.append({'opening':name,'point':world(np.array([left+(right-left)*xf,z0+(zt-z0)*zf]),b,.5).tolist(),'direction':b['rad'].tolist(),'distance':.82})

for i,b in bays.items():
 poly=box(-b['w']/2,.20,b['w']/2,4.44)
 for hole in holes[i]:poly=poly.difference(hole)
 add(f'Poster right lower facade wall bay {i} v54',poly,b,0,-.46,'wall',subdiv=2)
 if i in [18,19]:
  selected=[q for q in records if q['bay']==i and q['kind']=='rect'];xl=min(q['x']-q['halfWidth'] for q in selected);xr=max(q['x']+q['halfWidth'] for q in selected);top=max(q['z'][1] for q in selected)
  rect(f'Poster right window group hood bay {i} v54',b,xl-.12,xr+.12,top+.12,top+.27,.34,-.12,'hood');rect(f'Poster right hood drip bay {i} v54',b,xl-.15,xr+.15,top+.26,top+.31,.39,-.12,'hood')
  low=min(q['z'][0] for q in selected);rect(f'Poster right window group sill bay {i} v54',b,xl-.10,xr+.10,low-.26,low-.17,.32,-.12,'sill')
 else:
  rec=next(q for q in records if q['kind']=='door');top=rec['z'][1]+.68;rect('Poster right entrance lintel ledge v54',b,-b['w']/2+.12,b['w']/2-.12,top-.11,top,.29,-.10,'hood')
 rect(f'Poster right lower cornice bay {i} v54',b,-b['w']/2,b['w']/2,4.27,4.40,.28,-.12,'cornice')
 for side in [-1,1]:
  if side==-1 and i>17:continue
  x=side*(b['w']/2-.045);rect(f'Poster right lower pier bay {i} side {side} v54',b,x-.22,x+.22,.70,4.30,.26,-.10,'pier');rect(f'Poster right lower pier base bay {i} side {side} v54',b,x-.28,x+.28,.66,1.02,.37,-.10,'pier');rect(f'Poster right lower pier capital bay {i} side {side} v54',b,x-.30,x+.30,4.08,4.31,.40,-.10,'pier')
  for j in range(4):rect(f'Poster right pier capital groove bay {i} side {side} {j} v54',b,x-.15+j*.10-.01,x-.15+j*.10+.01,3.94,4.17,.275,.25,'groove',frontmat=1,side=1)

# The small circular fan is mounted in the first double-window transom.
b=bays[18];p=lift(493.8,638.3,b);circle=Point(*p).buffer(.092,quad_segs=24);add('Poster right window fan rim v54',circle.difference(Point(*p).buffer(.072,quad_segs=24)),b,.10,.025,'vent');add('Poster right window fan recess v54',Point(*p).buffer(.071,quad_segs=24),b,.022,-.018,'vent',frontmat=1,side=1)
for j in range(5):
 a=j*np.pi*2/5;points=np.array([[0,0],[.030,.006],[.062,.030],[.038,.044],[-.007,.023]]);M=np.array([[np.cos(a),-np.sin(a)],[np.sin(a),np.cos(a)]]);add(f'Poster right window fan blade {j} v54',Polygon(points@M.T+p),b,.06,.044,'vent')

np.savez_compressed(O/'right-facade-removal-v54.npz',**plans)
out={'revision':54,'sourceNativeSha256':S['sourceNativeSha256'],'sourceObjects':S['objects'],'sourceGeometryFile':'poster-right-facade-v54/source-right-facade-v54.npz','camera':S['camera'],'clipHeight':.20,'cutVolumes':cut_volumes,'openings':records,'members':members,'structuralProbeSpecifications':probes,'materials':['Reference-calibrated upper facade pigments v48','Poster upper window recessed faces v48','Poster upper window glazing edge v48'],'referenceMeasurementUncertaintyPixels':1.5,'oneToOneComplete':False,'scope':'Right lower-facade bays 17-19: partly hidden arched entrance, narrow arch, two and three rectangular windows; inferred depths and hidden room construction.'}
out['materials'][0]='Poster restored right facade pigments v54'
(O/'right-facade-geometry-v54.json').write_text(json.dumps(out,separators=(',',':')));print('RIGHT_FACADE_54_BUILT',len(members),sum(len(q['triangles']) for q in members),'triangles',{k:int((v>0).sum()) for k,v in plans.items() if v.any()})
