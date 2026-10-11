from pathlib import Path
import json,numpy as np,trimesh
from scipy.spatial import ConvexHull
from shapely.geometry import Polygon
from shapely.ops import triangulate
from PIL import Image
R=Path(__file__).parent;O=R/'poster-ground-v52';S=json.loads((O/'source-ground-v52.json').read_text());src=np.load(O/'source-ground-v52.npz');C=np.array(S['camera']['position']);rot=np.array(S['camera']['rotation']);f=S['camera']['focalPixels'];rng=np.random.default_rng(52052);members=[]
V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103');im=np.array(Image.open(V/'reference-hires.jpg').convert('RGB').resize((708,1000)))
edges=(np.arange(33)-16.5)*np.pi/16;edges[13:21]=[-.745387,-.567705,-.415142,-.217486,.006904,.147421,.411245,.678266];bays={}
for i in range(11,19):
 a0,a1=edges[i:i+2];a=(a0+a1)/2;h=(a1-a0)/2;rad=np.array([np.sin(a),np.cos(a),0]);t=np.array([np.cos(a),-np.sin(a),0]);bays[i]={'rad':rad,'t':t,'center':rad*23.5*np.cos(h),'chord':23.5*np.cos(h),'w':47*np.sin(h)+.022,'half':h}
def ray(u,v):return rot@np.array([(u-354)/f,(500-v)/f,-1])
def project(p):
 q=(np.asarray(p)-C)@rot;return np.stack((354+f*q[...,0]/-q[...,2],500-f*q[...,1]/-q[...,2]),axis=-1)
def waterpoint(u,v,z=.025):
 d=ray(u,v);return C+d*(z-C[2])/d[2]
def lift(u,v,depth=-.20):
 d=ray(u,v)
 for b in bays.values():
  p=C+d*np.dot(b['center']-b['rad']*depth-C,b['rad'])/np.dot(d,b['rad']);x=np.dot(p-b['center'],b['t'])
  if abs(x)<b['w']/2+.04:return p
 raise ValueError((u,v))
def linear(x):
 x=np.asarray(x)/255;return np.where(x<=.04045,x/12.92,((x+.055)/1.055)**2.4)
def add(name,m,kind,mat=0,metadata=None):
 m.fix_normals();assert m.is_watertight and m.volume>0,(name,m.is_watertight,m.volume)
 base=linear([65,99,99]) if mat==0 else linear([75,105,99]);v=np.asarray(m.vertices);variation=1+.10*np.sin(v[:,0]*5.13+v[:,1]*2.7)+.055*np.cos(v[:,0]*17.3-v[:,1]*11.7);gain=np.interp(project(v)[:,0],[0,150,300],[.50,.60,.77]) if mat==0 else np.full(len(v),.60);rgba=np.c_[base[None,:]*variation[:,None]*gain[:,None],np.ones(len(v))]
 members.append({'name':name,'kind':kind,'verticesNative':v.round(8).tolist(),'triangles':m.faces.tolist(),'materialIndices':[mat]*len(m.faces),'colors':rgba.astype('f4').tolist(),**(metadata or {})})
def solid_rings(bottom,top):
 vv=np.concatenate([bottom,top]);n=len(bottom);ff=[]
 for j in range(1,n-1):ff.extend([[0,j+1,j],[n,n+j,n+j+1]])
 for j in range(n):k=(j+1)%n;ff.extend([[j,k,n+k],[j,n+k,n+j]])
 return trimesh.Trimesh(vv,ff,process=False)

# Preserve the former interior floor elevation behind the facade, while the
# oversized projection into the flooded courtyard is removed.
for i in [13,15,16]:
 b=bays[i];front=-.19;back=-4.55;fw=(b['chord']-front)*np.tan(b['half'])+.012;bw=(b['chord']-back)*np.tan(b['half'])+.012;xy=np.array([b['center']+b['t']*x-b['rad']*d for x,d in [(-fw,front),(fw,front),(bw,back),(-bw,back)]]);bottom=xy.copy();top=xy.copy();bottom[:,2]=-.22;top[:,2]=.865
 add(f'Poster retained rear floor bay {i} v52',solid_rings(bottom,top),'rear floor',1,{'bay':i,'interiorFloorZ':.865,'frontInwardDepth':front})

# A shallow closed sediment ribbon follows the observed waterline in camera
# space, with genuine world-space extent and tapered, submerged edges.
shore=np.array([[-55,704],[-20,705],[0,706],[15,706.8],[33,705.7],[45,706.3],[61,706.6],[76,708],[91,705.4],[105,705.8],[122,705.4],[132,707.3],[148,707.6],[163,707.9],[176,708.2],[188,708.9],[202,708.3],[216,708.0],[230,708.4],[242,707.7],[253,707.6],[264,707.0],[279,707.9],[296,707.2],[310,707.2],[332,707.2],[350,707],[375,706.5]])
prior=json.loads((R/'poster-foreground-v51/foreground-geometry-v51.json').read_text());roots=[]
for q in prior['members']:
 if 'root' in q:roots.append(np.array(q['root']))
for q in prior['plantRegions']:
 if 'root' in q:roots.append(np.array(q['root']))
ns=217;nt=19;us=np.linspace(-55,375,ns);vv=[]
for u in us:
 edge_v=np.interp(u,shore[:,0],shore[:,1])+.10*np.sin(u*1.73);front=waterpoint(u,edge_v);back=lift(u,696)
 toward=C[:2]-back[:2];toward/=np.linalg.norm(toward);gap=np.dot(front[:2]-back[:2],toward)
 if gap<.48:front[:2]+=toward*(.48-gap)
 for t in np.linspace(0,1,nt):
  p=(1-t)*back+t*front;p[2]=.022+.158*(1-t)**1.35+.003*np.sin(u*.67+t*15)*np.sin(np.pi*t)
  # The tiny irregular rim reaches the water; the whole lower shell is submerged.
  if t==1:p[2]=.025
  vv.append(p)
vv=np.array(vv);ff=[]
for i in range(ns-1):
 for j in range(nt-1):
  a=i*nt+j;b=a+nt;c=b+1;d=a+1;ff.extend([[a,b,c],[a,c,d]])
border=[i*nt for i in range(ns)]+[(ns-1)*nt+j for j in range(1,nt)]+[i*nt+nt-1 for i in range(ns-2,-1,-1)]+[j for j in range(nt-2,0,-1)]
lower=vv[border].copy();lower[:,2]=-.20;n0=len(vv);vv=np.concatenate([vv,lower]);bottom_polygon=Polygon(lower[:,:2]);bottom_triangles=list(__import__('shapely').constrained_delaunay_triangles(bottom_polygon).geoms);assert abs(sum(q.area for q in bottom_triangles)-bottom_polygon.area)<1e-7;lookup={tuple(p.round(8)):j for j,p in enumerate(lower[:,:2])}
for j,a in enumerate(border):k=(j+1)%len(border);b=border[k];ff.extend([[a,n0+j,n0+k],[a,n0+k,b]])
for triangle in bottom_triangles:ff.append([n0+lookup[tuple(np.array(p).round(8))] for p in list(triangle.exterior.coords)[:3]])
add('Poster irregular shallow shoreline v52',trimesh.Trimesh(vv,ff,process=False),'shoreline',0,{'referenceWaterline708':shore.tolist(),'submergedBottomZ':-.20,'rootMounds':len(roots),'depthInferred':True})

# Root collars join the existing fixed vegetation to sediment, including the
# small foreground clumps beyond the continuous bank outline.
for j,root in enumerate(roots):
 angles=np.linspace(0,2*np.pi,12,endpoint=False);radius=.36 if root[2]>.16 else .27;ring=np.c_[np.cos(angles),np.sin(angles)]*radius*(1+.09*np.sin(angles*3+j))[:,None]+root[:2];small=root[:2]+(ring-root[:2])*.17
 bottom=np.c_[ring,np.full(12,-.20)];outer=np.c_[ring,np.full(12,.006)];upper=np.c_[small,np.full(12,.07)];v=np.concatenate([bottom,outer,upper]);faces=[]
 for layer in range(2):
  for k in range(12):a=layer*12+k;b=layer*12+(k+1)%12;faces.extend([[a,b,b+12],[a,b+12,a+12]])
 for k in range(1,11):faces.extend([[0,k+1,k],[24,24+k,24+k+1]])
 add(f'Poster sediment root collar {j} v52',trimesh.Trimesh(v,faces,process=False),'root soil',0,{'vegetationRoot':root.tolist(),'soilTopZ':.07})

# Main observed rock silhouettes. The hidden rear ring gives each rock volume.
rocks=[('left small shard',[[30,705.0],[34,704.5],[38.5,701.9],[40,702.2],[40.4,703.7],[44,704.2],[45.5,705.0]],.35),('low left stone',[[70.7,707.0],[71.4,705.5],[74.0,704.0],[81.8,704.2],[84.5,705.1],[85.5,707.1]],.62),('entrance broken slab',[[90,705.4],[92,703.8],[97,701.4],[104.5,698.7],[114,698.4],[119.7,699.4],[124.8,704.5]],.85),('chair front stone',[[130.6,707.0],[133.3,703.8],[137.6,702.6],[153.5,703.0],[157.6,704.9],[160.3,707.1]],.58),('pipe small fragment',[[183.5,710.2],[185.0,706.7],[188.1,706.0],[190.2,709.1],[190.0,711.0],[186.0,711.7]],.25),('right isolated stone',[[266.0,708.1],[266.7,705.7],[269.4,704.5],[272.2,704.7],[271.3,707.6],[269.3,708.8]],.33)]
for label,outline,depth in rocks:
 uv=np.array(outline);centeruv=uv.mean(0);anchor=waterpoint(centeruv[0],uv[:,1].max(),.025);normal=C-anchor;normal[2]=0;normal/=np.linalg.norm(normal);pts=[]
 for u,v in uv:
  d=ray(u,v);p=C+d*np.dot(anchor-C,normal)/np.dot(d,normal);pts.append(p)
 pts=np.array(pts);mid=pts.mean(0);rear=mid+(pts-mid)*.80-normal*depth;rear[:,2]=np.maximum(rear[:,2],-.045);m=trimesh.convex.convex_hull(np.concatenate([pts,rear]));add('Poster observed '+label+' v52',m,'rock',1,{'referenceSilhouette708':outline,'hiddenDepthMeters':depth,'depthInferred':True})

# Replace the column's box footings with chipped solids, keeping a broad upper
# contact around the original steel rather than relocating its measured base.
for row in S['extraObjects']:
 if row['key'] not in ['extra8','extra9','extra10','extra53']:continue
 old=src[row['key']+'_vertices'];lo=old.min(0);hi=old.max(0);mid=(lo+hi)/2;size=hi-lo;angle=np.linspace(0,2*np.pi,12,endpoint=False);radii=1+rng.uniform(-.10,.06,12);xy=np.c_[np.cos(angle)*size[0]*.55,np.sin(angle)*size[1]*.55]*radii[:,None]+mid[:2]
 low=np.c_[xy,np.full(12,lo[2])];high=np.c_[mid[:2]+(xy-mid[:2])*.81,np.full(12,hi[2])]
 # Keep the chair's support top large enough for both original bent leg frames.
 if row['key']=='extra53':high[:,:2]=mid[:2]+(xy-mid[:2])*.99
 add(row['name'],solid_rings(low,high),'chipped support',1,{'replacesObject':row['name'],'sourceKey':row['key'],'topZPreserved':float(hi[2]),'supportShapeInferred':True})

# Small fragments remain full solids; their sparse placement follows the bank,
# with none added to the open central water.
for j in range(28):
 u=rng.uniform(0,308);edge_v=np.interp(u,shore[:,0],shore[:,1]);p=waterpoint(u,edge_v-rng.uniform(.35,1.3),.035);width=rng.uniform(.055,.18);height=rng.uniform(.025,.065);theta=np.linspace(0,2*np.pi,6,endpoint=False);rad=rng.uniform(.75,1.12,6);xy=p[:2]+np.c_[np.cos(theta)*width,np.sin(theta)*width*.62]*rad[:,None];lower=np.c_[xy,np.full(6,-.035)];upper=np.c_[p[:2]+(xy-p[:2])*.75,np.full(6,.035+height)];add(f'Poster bank fragment {j} v52',solid_rings(lower,upper),'fragment',1)

# A closed broken footing meets the underside of the lowest stair tread.
facade50=json.loads((R/'poster-lower-facade-v50/lower-facade-geometry-v50.json').read_text());step=np.array(next(q for q in facade50['members'] if q['name']=='Poster entrance v50 step 2')['verticesNative']);cheeks=[np.array(q['verticesNative']) for q in facade50['members'] if q['name'].startswith('Poster entrance v50 stair cheek')];xy=np.concatenate([step,*cheeks])[:,:2];hull=ConvexHull(xy);outline=xy[hull.vertices];center=outline.mean(0);outline=center+(outline-center)*1.025;bottom=np.c_[outline,np.full(len(outline),-.20)];top=np.c_[outline,np.full(len(outline),step[:,2].min()+.003)];add('Poster broken stair foundation v52',solid_rings(bottom,top),'stair foundation',1,{'lowestTreadBaseZ':float(step[:,2].min()),'supportTopZ':float(step[:,2].min()+.003)})

# Replant only the lower stem segments; preserve leaf blades and grass tips.
# Ground samples use barycentric interpolation over the actual new solids.
plant_edits=[];ground_parts=[q for q in members if q['kind'] in ['shoreline','root soil']]
def ground_height(xy):
 hits=[]
 for q in ground_parts:
  pts=np.array(q['verticesNative']);tri=pts[np.array(q['triangles'])];a=tri[:,0,:2];b=tri[:,1,:2]-a;c=tri[:,2,:2]-a;det=b[:,0]*c[:,1]-b[:,1]*c[:,0];valid=abs(det)>1e-10;det=np.where(valid,det,1);d=np.asarray(xy)-a;u=(d[:,0]*c[:,1]-d[:,1]*c[:,0])/det;v=(b[:,0]*d[:,1]-b[:,1]*d[:,0])/det;inside=valid&(u>=-1e-8)&(v>=-1e-8)&(u+v<=1+1e-8)
  if inside.any():hits.extend((tri[:,0,2]+u*(tri[:,1,2]-tri[:,0,2])+v*(tri[:,2,2]-tri[:,0,2]))[inside])
 assert hits,xy
 return max(hits)
for q in prior['members']:
 if 'root' not in q:continue
 root=np.array(q['root']);p=np.array(q['verticesNative']);new=p.copy();target=ground_height(root[:2])+.001;delta=target-root[2]
 if q['kind']=='foliage':
  for branch in range(max(5,q['leafCount']//22)):
   ix=branch*20+np.array([0,1,2,3,4,5,18]);new[ix,2]+=delta
 elif q['kind']=='grass':
  for blade in range(q['blades']):
   first=blade*30;base=p[first:first+4].mean(0);base_target=ground_height(base[:2])+.001;dz=base_target-base[2]
   for ring in range(7):new[first+ring*4:first+(ring+1)*4,2]+=dz*(1-ring/6)**2
   new[first+28,2]+=dz
 indices=np.flatnonzero(np.max(abs(new-p),axis=1)>1e-10);plant_edits.append({'name':q['name'],'kind':q['kind'],'sourceVertexSha256':__import__('hashlib').sha256(p.astype('f4').tobytes()).hexdigest(),'vertexIndices':indices.tolist(),'positionsNative':new[indices].round(8).tolist(),'oldRoot':root.tolist(),'newRoot':[float(root[0]),float(root[1]),float(target)],'leafBladesOrGrassTipsPreserved':True})

out={'revision':52,'sourceNativeSha256':S['sourceNativeSha256'],'sourceObjects':S['objects']+S['extraObjects'][:7],'sourceGeometryFile':'poster-ground-v52/source-ground-v52.npz','camera':S['camera'],'members':members,'plantRootEdits':plant_edits,'materials':['Poster wet ground pigments v52','Poster broken stone pigments v52'],'newMaterials':[{'name':'Poster wet ground pigments v52','clone':'Poster fine foliage pigments v51','attribute':'surface_color','roughness':.97},{'name':'Poster broken stone pigments v52','clone':'Poster fine foliage pigments v51','attribute':'surface_color','roughness':.91}],'scope':'Observed shallow left bank, major rock silhouettes, chipped column supports and lowered exterior plinth; unseen depths and unobserved surfaces inferred.','oneToOneComplete':False}
(O/'ground-geometry-v52.json').write_text(json.dumps(out,separators=(',',':')),encoding='utf-8');print('GROUND_52_BUILT',len(members),'closed assemblies',sum(len(q['triangles']) for q in members),'triangles',len(roots),'root mounds')
