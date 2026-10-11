from pathlib import Path
import json,numpy as np,trimesh
from shapely.geometry import Polygon,box,MultiPoint
from shapely.ops import triangulate
from scipy.interpolate import PchipInterpolator

R=Path(__file__).parent;O=R/'poster-arches-v49';S=json.loads((O/'source-arches-v49.json').read_text());A=np.load(O/'source-arches-v49.npz');C=np.array(S['camera']['position']);rot=np.array(S['camera']['rotation']);f=S['camera']['focalPixels'];plans={q['key']:np.zeros(q['triangles'],'u1') for q in S['objects']}
edges=(np.arange(33)-16.5)*np.pi/16;edges[13:21]=[-.745387,-.567705,-.415142,-.217486,.006904,.147421,.411245,.678266];bays={}
for i in [13,14,15]:
 a0,a1=edges[i:i+2];angle=(a0+a1)/2;half=(a1-a0)/2;rad=np.array([np.sin(angle),np.cos(angle),0]);t=np.array([np.cos(angle),-np.sin(angle),0]);chord=23.5*np.cos(half);w=2*23.5*np.sin(half)+.022;top=5.48 if i<15 else 5.64;bays[i]={'rad':rad,'t':t,'center':rad*chord,'chord':chord,'w':w,'half':half,'top':top}
 for q in S['objects']:
  points=A[q['key']+'_vertices'][A[q['key']+'_faces']];x=(points-bays[i]['center'])@t;d=-(points-bays[i]['center'])@rad;z=points[:,:,2]
  select=(abs(x)<=w/2+2e-5).all(1)&(d>=-.46002).all(1)&(d<=.301).all(1)&(z.max(1)<=top+2e-5)&(z.max(1)>4.44002)
  plans[q['key']][select]=2
  # The former sill projects .27 m into the courtyard, in front of the new
  # rectangular glazing. Remove its complete remaining shell in these bays.
  if i<15:
   sill=(abs(x)<=w/2+2e-5).all(1)&(d>=-.21002).all(1)&(d<=.27002).all(1)&(z>=5.59248).all(1)&(z<=5.66752).all(1)
   plans[q['key']][sill]=1

def project(p):
 q=(np.asarray(p)-C)@rot;return np.stack((354+f*q[...,0]/-q[...,2],500-f*q[...,1]/-q[...,2]),axis=-1)
def lift(u,v,b=None):
 ray=np.array([(u-354)/f,(500-v)/f,-1])@rot.T
 for i,bb in ([b] if b else bays.items()):
  dist=np.dot(bb['center']-C,bb['rad'])/np.dot(ray,bb['rad']);p=C+dist*ray;x=np.dot(p-bb['center'],bb['t'])
  if b or abs(x)<=bb['w']/2:return i,np.array([x,p[2]]),p
 raise ValueError((u,v))

# u, outer half-width, apex v, base v, spring-to-apex pixel rise, confidence.
tall=[[-4.8,5.7,575.9,590.6,5.2,'partly visible'],[35,5.9,578.8,593.3,5.0,'observed'],[47,5.9,579.9,594.2,5.0,'observed'],[59,5.8,580.6,595.0,5.0,'observed'],
 [111.5,5.8,584.7,598.6,4.6,'observed'],[123.5,5.8,585.1,599.1,4.6,'observed'],[135.5,5.8,585.6,599.7,4.6,'observed'],
 [183.3,5.0,587.1,602.1,4.5,'partly occluded'],[194.5,5.0,587.8,602.5,4.5,'inferred behind beam'],[205.7,5.0,588.4,602.9,4.5,'inferred behind beam'],
 [235,5.4,589.1,603.8,4.8,'observed'],[246.5,5.2,589.4,604.0,4.8,'observed'],[257,5.0,589.6,604.2,4.8,'partly occluded']]
small=[[5,1.25,585.5,591.4],[11.2,1.20,585.9,591.9],[18.2,1.25,586.8,592.4],[24.7,1.20,587.3,592.9],
 [72,1.20,589.6,595.7],[78.4,1.20,590.2,596.0],[84.8,1.20,590.8,596.7],[94,1.20,591.7,597.7],[101.8,1.20,592.1,598.0],
 [145,1.15,594.3,600.1],[151,1.15,594.7,600.3],[157.5,1.15,595.0,600.7],[163.6,1.15,595.3,601.0],
 [213.1,1.30,596.4,603.0],[218.5,1.25,596.7,603.2],[224.5,1.20,596.9,603.4]]
records=[]
for kind,rows in [('pointed',tall),('small',small)]:
 for j,row in enumerate(rows):
  u,half,apexv,basev=row[:4];i,center,_=lift(u,(apexv+basev)/2);b=bays[i];_,apex,_=lift(u,apexv,(i,b));_,base,_=lift(u,basev,(i,b));_,left,_=lift(u-half,(apexv+basev)/2,(i,b));_,right,_=lift(u+half,(apexv+basev)/2,(i,b));a=(right[0]-left[0])/2;x=(right[0]+left[0])/2
  rise=apex[1]-lift(u,apexv+row[4],(i,b))[1][1] if kind=='pointed' else a
  records.append({'id':kind+' '+str(j),'kind':kind,'bay':i,'x':float(x),'halfWidth':float(a),'apex':float(apex[1]),'base':float(base[1]),'rise':float(rise),'reference':[u,half,apexv,basev],'evidence':row[5] if kind=='pointed' else ('partly occluded' if 65<u<95 or u>156 else 'observed')})

def contour(rec,inset=0):
 a=rec['halfWidth']-inset;z0=rec['base']+inset*.20;zt=rec['apex']-inset;rise=max(rec['rise']-inset*.25,a*.45);spring=zt-rise;x=rec['x'];pts=[[x-a,z0],[x-a,spring]]
 if rec['kind']=='pointed':
  p=np.array([[-a,spring],[-a,spring+rise*.68],[-a*.32,zt-rise*.16],[0,zt]])
  u=np.linspace(0,1,17)[1:];q=(1-u[:,None])**3*p[0]+3*(1-u[:,None])**2*u[:,None]*p[1]+3*(1-u[:,None])*u[:,None]**2*p[2]+u[:,None]**3*p[3];cap=np.vstack([q,np.c_[-q[:-1,0][::-1],q[:-1,1][::-1]],[a,spring]])
 else:
  theta=np.linspace(np.pi,0,25)[1:];cap=np.c_[a*np.cos(theta),spring+rise*np.sin(theta)]
 pts.extend((cap+[x,0]).tolist());pts.append([x+a,z0]);return np.array(pts)

members=[]
def world(p,b,depth):
 p=np.asarray(p);return b['center']+p[...,0,None]*(b['chord']-depth)/b['chord']*b['t']-b['rad']*depth+np.stack([np.zeros(p.shape[:-1]),np.zeros(p.shape[:-1]),p[...,1]],axis=-1)
def add(name,m,materials,kind,subdiv=0,meta=None):
 m.fix_normals();assert m.is_watertight and m.volume>0,(name,m.is_watertight,m.volume);mi=np.array(materials,int)
 for _ in range(subdiv):m=m.subdivide();mi=np.repeat(mi,4)
 assert len(m.faces)==len(mi) and m.is_watertight
 members.append({'name':name,'kind':kind,'verticesNative':m.vertices.round(8).tolist(),'triangles':m.faces.tolist(),'materialIndices':mi.tolist(),**(meta or {})})
def extrude(poly,b,front,back,backmat=1):
 verts=[];faces=[];mi=[];lookup={}
 def vertex(p,d):
  v=world(np.asarray(p),b,d);key=tuple(np.round(v,9))
  if key not in lookup:lookup[key]=len(verts);verts.append(v)
  return lookup[key]
 tris=[t for t in triangulate(poly) if poly.covers(t)];assert abs(sum(t.area for t in tris)-poly.area)<1e-7,('unfilled cap',poly.area,sum(t.area for t in tris))
 for tri in tris:
  pts=np.asarray(tri.exterior.coords)[:3]
  for depth,mat in [(front,0),(back,backmat)]:faces.append([vertex(p,depth) for p in pts]);mi.append(mat)
 for ring in [poly.exterior,*poly.interiors]:
  pts=np.asarray(ring.coords)
  for p,q in zip(pts[:-1],pts[1:]):
   ids=[vertex(p,front),vertex(q,front),vertex(q,back),vertex(p,back)];faces.extend([[ids[0],ids[1],ids[2]],[ids[0],ids[2],ids[3]]]);mi.extend([1,1])
 return trimesh.Trimesh(verts,faces,process=False),mi

holes={i:[] for i in bays};probe_specs=[]
for rec in records:
 b=bays[rec['bay']];inset=.044 if rec['kind']=='pointed' else .013
 outer=contour(rec);inner=contour(rec,inset);poly=Polygon(inner);limit=box(-b['w']/2,4.44,b['w']/2,b['top']);hole=poly.intersection(limit);assert hole.area>0 and hole.geom_type=='Polygon';holes[rec['bay']].append(hole)
 # Profiled stone surround with two raised beveled faces and a recessed reveal.
 rings=[]
 for t,d in [(0,.008),(.22,.062),(.72,.058),(1,-.018),(1,-.105),(0,-.105)]:rings.append(world(outer*(1-t)+inner*t,b,d))
 vv=np.concatenate(rings);n=len(outer);ff=[];mi=[]
 for k in range(len(rings)):
  kk=(k+1)%len(rings)
  for j in range(n):
   jj=(j+1)%n;ff.extend([[k*n+j,k*n+jj,kk*n+jj],[k*n+j,kk*n+jj,kk*n+j]]);mi.extend([0 if k<3 else 1]*2)
 add('Poster '+rec['id']+' molded surround v49',trimesh.Trimesh(vv,ff,process=False),mi,'surround',0,{'archId':rec['id'],'bay':rec['bay']})
 # Gray inserts are shallow blind panels; the dark first group is treated as
 # glazing. Both are real closed solids, not painted over the original wall.
 glazed=rec['kind']=='pointed' and rec['reference'][0]<70
 insert=hole.buffer(.005,join_style=2).intersection(limit);m,mat=extrude(insert,b,-.075,-.083 if glazed else -.12,2 if glazed else 1);add('Poster '+rec['id']+(' glazing' if glazed else ' recessed infill')+' v49',m,mat,'insert',1,{'archId':rec['id'],'bay':rec['bay'],'infillInterpretation':'glazing' if glazed else 'blind panel inferred from gray appearance'})
 probe_specs.append({'archId':rec['id'],'bay':rec['bay'],'point':world(np.array([rec['x'],(rec['base']+rec['apex'])/2]),b,.03).tolist(),'direction':b['rad'].tolist()})

for i,b in bays.items():
 poly=box(-b['w']/2,4.44,b['w']/2,b['top'])
 for hole in holes[i]:poly=poly.difference(hole)
 assert poly.geom_type=='Polygon'
 m,mat=extrude(poly,b,0,-.46);add(f'Poster arched clerestory wall bay {i} v49',m,mat,'wall',2,{'bay':i})

# The observed lower line is not level under the inferred circular facade.
# Preserve its smooth visual grade instead of creating steps at bay seams.
base_samples=[]
for rec in records:
 b=bays[rec['bay']];p=world(np.array([rec['x'],rec['base']]),b,0);base_samples.append([np.arctan2(p[0],p[1]),rec['base']])
base_samples=np.array(sorted(base_samples));baseline=PchipInterpolator(base_samples[:,0],base_samples[:,1])
section=np.array([[-.04,.018],[.12,.018],[.15,.005],[.15,-.055],[.30,-.073],[.32,-.102],[.28,-.140],[.12,-.170],[-.04,-.170]])
cap=[np.array(t.exterior.coords)[:3] for t in triangulate(Polygon(section)) if Polygon(section).covers(t)];cap_ids=[[int(np.argmin(np.linalg.norm(section-q,axis=1))) for q in t] for t in cap]
for i,b in bays.items():
 xs=np.linspace(-b['w']/2-.007,b['w']/2+.007,max(10,int(b['w']/.08)));verts=[];faces=[];mi=[]
 for x in xs:
  p=world(np.array([x,0]),b,0);z=float(baseline(np.clip(np.arctan2(p[0],p[1]),*base_samples[[0,-1],0])))
  for depth,dz in section:verts.append(world(np.array([x,z+dz]),b,depth))
 n=len(section)
 for k in range(len(xs)-1):
  for j in range(n):
   jj=(j+1)%n;faces.extend([[k*n+j,k*n+jj,(k+1)*n+jj],[k*n+j,(k+1)*n+jj,(k+1)*n+j]]);mi.extend([0 if j<7 else 1]*2)
 for tri in cap_ids:faces.extend([tri,[q+(len(xs)-1)*n for q in tri]]);mi.extend([1,1])
 add(f'Poster sloping clerestory cornice bay {i} v49',trimesh.Trimesh(verts,faces,process=False),mi,'cornice',0,{'bay':i})

prior=json.loads((R/'poster-upper-windows-v48/upper-window-geometry-v48.json').read_text());replaced_partitions=[];retained_browser_partitions=[]
for q in prior['members']:
 if q['kind']!='partition':continue
 if ' lower ' not in q['name']:
  retained_browser_partitions.append(q['name']);continue
 verts=np.array(q['verticesNative']);footprint=MultiPoint(verts[:,:2]).convex_hull;rear=np.array(footprint.exterior.coords)[:-1]
 for i in [13,14]:
  b=bays[i];out=[]
  for a,c in zip(rear,np.roll(rear,-1,axis=0)):
   va=np.dot(a-b['center'][:2],b['rad'][:2])-.46;vc=np.dot(c-b['center'][:2],b['rad'][:2])-.46
   if va>=0:out.append(a)
   if (va>=0)!=(vc>=0):out.append(a+(c-a)*va/(va-vc))
  rear=np.array(out)
 rearpoly=Polygon(rear);assert rearpoly.is_valid and rearpoly.area>0
 # Each section is independently closed. The lower section still follows the
 # original room footprint, while the upper section stops behind the facade.
 for suffix,poly,z0,z1 in [('lower',footprint,float(verts[:,2].min()),4.44),('rear',rearpoly,4.44,float(verts[:,2].max()))]:
  vv=[];ff=[];lookup={}
  def vid(p,z):
   key=tuple(np.round([*p,z],8))
   if key not in lookup:lookup[key]=len(vv);vv.append(key)
   return lookup[key]
  tris=[t for t in triangulate(poly) if poly.covers(t)];assert abs(sum(t.area for t in tris)-poly.area)<1e-7
  for tri in tris:
   p=np.array(tri.exterior.coords)[:3]
   for z in [z0,z1]:ff.append([vid(a,z) for a in p])
  p=np.array(poly.exterior.coords)
  for a,c in zip(p[:-1],p[1:]):
   ids=[vid(a,z0),vid(c,z0),vid(c,z1),vid(a,z1)];ff.extend([[ids[0],ids[1],ids[2]],[ids[0],ids[2],ids[3]]])
  name=q['name'].replace(' lower v48',' '+suffix+' v49');add(name,trimesh.Trimesh(vv,ff,process=False),[3]*len(ff),'partition',0,{'replaces':q['name']})
 replaced_partitions.append(q['name'])

np.savez_compressed(O/'arch-removal-v49.npz',**plans)
out={'revision':49,'sourceNativeSha256':S['sourceNativeSha256'],'sourceObjects':S['objects'],'sourceGeometryFile':'poster-arches-v49/source-arches-v49.npz','camera':S['camera'],'clipHeight':4.44,'arches':records,'members':members,'replacedPartitions':replaced_partitions,'retainedBrowserPartitions':retained_browser_partitions,'structuralProbeSpecifications':probe_specs,'referenceMeasurementUncertaintyPixels':1.5,'changes':{k:{'clip':int((p==2).sum()),'remove':int((p==1).sum())} for k,p in plans.items() if p.any()},'materials':['Reference-calibrated upper facade pigments v48','Poster upper window recessed faces v48','Poster upper window glazing edge v48',prior['members'] and S['objects'][16]['materials'][0]],'scope':'Observed pointed and small arched recess groups, fitted lower cornice and real molded surrounds. Hidden arches, back surfaces and gray-panel interpretation remain inferred.','oneToOneComplete':False};(O/'arch-geometry-v49.json').write_text(json.dumps(out,separators=(',',':')));print('ARCHES_49_GEOMETRY',len(records),'arches',len(members),'solids',sum(len(q['triangles']) for q in members),'triangles',out['changes'])
