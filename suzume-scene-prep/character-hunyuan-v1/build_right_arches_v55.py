from pathlib import Path
import json,numpy as np,trimesh
from shapely.geometry import Polygon,box,Point
from shapely import constrained_delaunay_triangles
from scipy.interpolate import PchipInterpolator
R=Path(__file__).parent;O=R/'poster-right-arches-v55';S=json.loads((O/'source-right-arches-v55.json').read_text());A=np.load(O/'source-right-arches-v55.npz');C=np.array(S['camera']['position']);rot=np.array(S['camera']['rotation']);f=S['camera']['focalPixels'];radius=23.3;theta0=.147421;theta1=.678266;members=[];records=[];probes=[];plans={q['key']:np.zeros(q['triangles'],'u1') for q in S['objects']};cuts=[]
for a0,a1 in [(.147421,.411245),(.411245,.678266)]:
 a=(a0+a1)/2;h=(a1-a0)/2;r=np.array([np.sin(a),np.cos(a),0]);t=np.array([np.cos(a),-np.sin(a),0]);chord=23.5*np.cos(h);w=47*np.sin(h)+.022;cuts.append({'x':[-w/2-.14,w/2+.14],'d':[-.65002,.80002],'z':[4.44002,6.50],'center':(r*chord).tolist(),'tangent':t.tolist(),'radial':r.tolist()})
for q in S['objects']:
 p=A[q['key']+'_vertices'][A[q['key']+'_faces']]
 for cut in cuts:
  x=(p-cut['center'])@np.array(cut['tangent']);d=-(p-cut['center'])@np.array(cut['radial']);z=p[:,:,2];candidate=(x.max(1)>=cut['x'][0])&(x.min(1)<=cut['x'][1])&(d.max(1)>=cut['d'][0])&(d.min(1)<=cut['d'][1])&(z.max(1)>=cut['z'][0])&(z.min(1)<=cut['z'][1]);plans[q['key']][candidate]=3

def lift(u,v):
 ray=rot@np.array([(u-354)/f,(500-v)/f,-1]);a=np.dot(ray[:2],ray[:2]);b=2*np.dot(C[:2],ray[:2]);c=np.dot(C[:2],C[:2])-radius**2;roots=np.roots([a,b,c]);t=max(roots);p=C+t*ray;return np.array([radius*np.arctan2(p[0],p[1]),p[2]])
def world(p):
 p=np.asarray(p);th=p[...,0]/radius;r=radius-p[...,2];return np.stack([r*np.sin(th),r*np.cos(th),p[...,1]],axis=-1)
def addmesh(name,v,faces,mi,kind,subdiv=0,meta=None):
 mesh=trimesh.Trimesh(v,faces,process=False);mesh.fix_normals();assert mesh.is_watertight and mesh.volume>0,(name,mesh.is_watertight,mesh.volume);mi=np.array(mi)
 for _ in range(subdiv):mesh=mesh.subdivide();mi=np.repeat(mi,4)
 verts=world(mesh.vertices);m=trimesh.Trimesh(verts,mesh.faces,process=False);m.fix_normals();assert m.is_watertight and m.volume>0;members.append({'name':name,'kind':kind,'verticesNative':m.vertices.round(8).tolist(),'triangles':m.faces.tolist(),'materialIndices':mi.tolist(),'curvedSurfaceNormals':True,**(meta or {})})
def solid(name,poly,front,back,kind,subdiv=0,frontmat=0,side=1,meta=None):
 assert poly.is_valid and poly.geom_type=='Polygon' and poly.area>1e-9,(name,poly.geom_type);vv=[];ff=[];mi=[];lookup={}
 def vertex(p,d):
  key=tuple(np.round([p[0],p[1],d],9))
  if key not in lookup:lookup[key]=len(vv);vv.append(key)
  return lookup[key]
 tris=list(constrained_delaunay_triangles(poly).geoms);assert abs(sum(t.area for t in tris)-poly.area)<1e-7
 for tri in tris:
  pts=np.asarray(tri.exterior.coords)[:3]
  for d,mat in [(front,frontmat),(back,side)]:ff.append([vertex(p,d) for p in pts]);mi.append(mat)
 for ring in [poly.exterior,*poly.interiors]:
  points=np.array(ring.coords)
  for a,b in zip(points[:-1],points[1:]):
   ids=[vertex(a,front),vertex(b,front),vertex(b,back),vertex(a,back)];ff.extend([[ids[0],ids[1],ids[2]],[ids[0],ids[2],ids[3]]]);mi.extend([side,side])
 addmesh(name,vv,ff,mi,kind,subdiv,meta)

top_pixels=[[430,571.1],[440,573.6],[450,575.7],[460,577.4],[470,578.5],[480,578.0],[500,576.8],[520,575.8],[540,574.6],[560,573.6],[580,572.3],[600,571.0],[620,570.0],[640,568.4],[660,567.4],[680,566.0],[700,564.5],[715,563.5]]
bottom_pixels=[[430,580.0],[440,582.2],[450,583.9],[460,585.1],[470,585.2],[480,584.9],[500,583.6],[520,582.5],[540,581.4],[560,580.1],[580,578.7],[600,577.7],[620,576.0],[640,574.4],[660,573.0],[680,571.6],[700,570.0],[715,568.8]]
def profile(points):
 p=np.array([lift(*uv) for uv in points]);return PchipInterpolator(p[:,0],p[:,1])
top=profile(top_pixels);bottom=profile(bottom_pixels);x0=theta0*radius;x1=theta1*radius;xx=np.linspace(x0,x1,161);wallpoly=Polygon([[x0,4.44],[x1,4.44],*np.c_[xx[::-1],bottom(xx[::-1])].tolist()]);holes=[]
cap_data=json.loads((O/'arch-cap-measurements-v55.json').read_text())
for q in cap_data:
 u,a,ap,rise,base=q['fitted'];th=np.linspace(np.pi,0,49);uv=np.c_[u+a*np.cos(th),ap+rise*(1-np.sin(th))-.04*a*np.cos(th)];uv=np.vstack([[u-a,base+.04*a],uv,[u+a,base-.04*a]]);poly=Polygon([lift(*p) for p in uv]);records.append({'id':'large '+str(q['id']),'kind':'large','reference':q['fitted'],'polygon':poly,'apexUV':[u,ap],'baseOcclusionInferred':q['id']>=3})
for j,(u,a,ap,base) in enumerate([[446.3,1.35,594.6,600.4],[451.1,1.3,594.2,600.2],[498.6,1.35,593.3,598.8],[505.1,1.3,593.0,598.5],[511.5,1.25,592.8,598.3]]):
 th=np.linspace(np.pi,0,25);uv=np.vstack([[u-a,base],np.c_[u+a*np.cos(th),ap+a*(1-np.sin(th))],[u+a,base]]);poly=Polygon([lift(*p) for p in uv]);records.append({'id':'small '+str(j),'kind':'small','reference':[u,a,ap,base],'polygon':poly,'apexUV':[u,ap]})
# The pointed arch at the left is a decorative recessed panel.
u,a,ap,base,rise=460.7,3.55,588.7,599.4,3.2;tt=np.linspace(0,1,25);p=np.array([[-a,ap+rise],[-a,ap+rise*.38],[-a*.35,ap+.25],[0,ap]]);left=(1-tt[:,None])**3*p[0]+3*(1-tt[:,None])**2*tt[:,None]*p[1]+3*(1-tt[:,None])*tt[:,None]**2*p[2]+tt[:,None]**3*p[3];curve=np.vstack([left,np.c_[-left[:-1,0][::-1],left[:-1,1][::-1]]])+[u,0];poly=Polygon([lift(*p) for p in np.vstack([[u-a,base],curve,[u+a,base]])]);records.append({'id':'left pointed','kind':'pointed','reference':[u,a,ap,base],'polygon':poly,'apexUV':[u,ap]})
for rec in records:
 poly=rec.pop('polygon');hole=poly.intersection(wallpoly);assert hole.geom_type=='Polygon' and hole.area>0;holes.append(hole);tag='Poster right '+rec['id']+' v55';width=.022 if rec['kind']=='small' else .045;outer=poly.buffer(width,join_style=2);solid(tag+' molded surround',outer.difference(poly),.075,-.10,'surround',1,meta={'archId':rec['id']});solid(tag+' inner bead',poly.buffer(width*.45,join_style=2).difference(poly.buffer(width*.12,join_style=2)),.094,.072,'molding',0,meta={'archId':rec['id']});solid(tag+' recessed insert',hole.buffer(.003,join_style=2).intersection(wallpoly),-.105,-.16,'insert',2,side=2 if rec['kind']=='large' else 1,meta={'archId':rec['id'],'hiddenBackingInferred':True});p=hole.representative_point();point=np.array([p.x,p.y,.03]);w=world(point);normal=np.array([np.sin(p.x/radius),np.cos(p.x/radius),0]);probes.append({'archId':rec['id'],'point':w.tolist(),'direction':normal.tolist(),'distance':.105})

panel=Polygon([lift(*p) for p in [[470.4,584.9],[492.1,583.8],[493.8,598.7],[493.7,600.0],[470.4,600.3]]]).intersection(wallpoly);assert panel.geom_type=='Polygon';holes.append(panel);solid('Poster right broad gray recess v55',panel,-.085,-.17,'insert',3,meta={'hiddenBackingInferred':True});p=panel.representative_point();probes.append({'archId':'broad gray recess','point':world([p.x,p.y,.03]).tolist(),'direction':[float(np.sin(p.x/radius)),float(np.cos(p.x/radius)),0],'distance':.10})
stub=Polygon([lift(*p) for p in [[480.0,599.6],[480.0,594.8],[483.8,593.0],[484.2,593.3],[484.2,599.5]]]);solid('Poster right broken recess masonry stub v55',stub,.045,-.15,'broken stub',2)
for hole in holes:wallpoly=wallpoly.difference(hole)
assert wallpoly.geom_type=='Polygon';solid('Poster curved right upper wall v55',wallpoly,0,-.52,'wall',3)

base_pixels=[[438,602.3],[450,601.8],[470,601.6],[490,601.0],[510,600.5]]+[[q['fitted'][0],q['fitted'][4]] for q in cap_data]+[[715,587.7]];base=profile(base_pixels)
def sweep(name,section,kind,meta=None):
 xs=np.linspace(x0-.006,x1+.006,180);vv=[];ff=[];mi=[];sections=[]
 for x in xs:
  shape=np.array(section(x));assert Polygon(shape).is_valid;sections.append(shape)
  for depth,z in shape:vv.append([x,z,depth])
 n=len(sections[0]);caps=constrained_delaunay_triangles(Polygon(sections[0])).geoms
 for tri in caps:
  ids=[int(np.argmin(np.linalg.norm(sections[0]-p,axis=1))) for p in np.array(tri.exterior.coords)[:3]];ff.extend([ids,[q+(len(xs)-1)*n for q in ids]]);mi.extend([1,1])
 for k in range(len(xs)-1):
  for j in range(n):jj=(j+1)%n;ff.extend([[k*n+j,k*n+jj,(k+1)*n+jj],[k*n+j,(k+1)*n+jj,(k+1)*n+j]]);mi.extend([0,0])
 addmesh(name,vv,ff,mi,kind,0,meta)
sweep('Poster right graded lower cornice v55',lambda x:np.array([[-.04,.025],[.11,.025],[.16,.010],[.16,-.047],[.29,-.068],[.32,-.102],[.30,-.160],[.12,-.207],[-.04,-.207]])+[0,float(base(x))],'cornice')
sweep('Poster right sloping crown band v55',lambda x:[[-.20,float(bottom(x))+.012],[.13,float(bottom(x))+.012],[.23,float(bottom(x))+.075],[.24,float(top(x))-.036],[.34,float(top(x))-.018],[.34,float(top(x))+.043],[.045,float(top(x))+.055],[-.20,float(top(x))+.035]],'crown')
sweep('Poster right roof transition strip v55',lambda x:[[.045,float(top(x))+.053],[-.55,5.94],[-1.10,5.94],[-1.10,5.78],[-.55,5.78],[.045,float(top(x))-.107]],'roof',{'rearTopZ':5.94,'hiddenTransitionInferred':True})
# Short projecting lintel above the left pointed-and-small recess group.
p=np.array([lift(*q) for q in [[442.0,586.1],[468.8,586.1],[468.8,587.1],[442.0,587.1]]]);solid('Poster right left recess lintel v55',Polygon(p),.145,-.06,'lintel',2)

np.savez_compressed(O/'right-arches-removal-v55.npz',**plans)
out={'revision':55,'sourceNativeSha256':S['sourceNativeSha256'],'sourceObjects':S['objects'],'sourceGeometryFile':'poster-right-arches-v55/source-right-arches-v55.npz','camera':S['camera'],'surfaceRadius':radius,'clipHeight':4.44,'cutVolumes':cuts,'arches':records,'members':members,'structuralProbeSpecifications':probes,'materials':['Poster calibrated right arcade pigments v55','Poster upper window recessed faces v48','Poster upper window glazing edge v48'],'replacedObjects':['Poster right lower cornice bay 18 v54','Poster right lower cornice bay 19 v54'],'roofRearTopZ':5.94,'oneToOneComplete':False,'scope':'Right upper decorative arcade: ten large arches, five small recesses, one pointed recess, broad gray recess, curved wall, graded cornices and roof transition. Hidden backing, beam-occluded bases and rear depth inferred.'};(O/'right-arches-geometry-v55.json').write_text(json.dumps(out,separators=(',',':')));print('RIGHT_ARCHES_55_BUILT',len(members),sum(len(q['triangles']) for q in members),[(k,int((v>0).sum())) for k,v in plans.items() if v.any()])
