from pathlib import Path
import json,numpy as np,trimesh
from scipy.interpolate import CubicSpline
R=Path(__file__).parent;O=R/'poster-low-rails-v53';S=json.loads((O/'source-low-rails-v53.json').read_text());C=np.array(S['camera']['position']);rot=np.array(S['camera']['rotation']);f=S['camera']['focalPixels'];rng=np.random.default_rng(53053);members=[];anchors=[]
edges=(np.arange(33)-16.5)*np.pi/16;edges[13:21]=[-.745387,-.567705,-.415142,-.217486,.006904,.147421,.411245,.678266];bays={}
for i in range(12,17):
 a0,a1=edges[i:i+2];a=(a0+a1)/2;h=(a1-a0)/2;rad=np.array([np.sin(a),np.cos(a),0]);t=np.array([np.cos(a),-np.sin(a),0]);bays[i]={'rad':rad,'t':t,'center':rad*23.5*np.cos(h),'w':47*np.sin(h)+.022}
def ray(u,v):return rot@np.array([(u-354)/f,(500-v)/f,-1])
def lift(u,v,depth=1.65,bay=13):
 b=bays[bay];d=ray(u,v);return C+d*np.dot(b['center']-b['rad']*depth-C,b['rad'])/np.dot(d,b['rad'])
def project(p):
 q=(np.asarray(p)-C)@rot;return np.stack((354+f*q[...,0]/-q[...,2],500-f*q[...,1]/-q[...,2]),axis=-1)
def linear(x):
 x=np.array(x)/255;return np.where(x<=.04045,x/12.92,((x+.055)/1.055)**2.4)
G=json.loads((R/'poster-ground-v52/ground-geometry-v52.json').read_text());ground_parts=[q for q in G['members'] if q['kind'] in ['shoreline','root soil','rock','fragment','stair foundation','chipped support']]
def ground_height(xy):
 hits=[]
 for q in ground_parts:
  pts=np.array(q['verticesNative']);tri=pts[np.array(q['triangles'])];a=tri[:,0,:2];b=tri[:,1,:2]-a;c=tri[:,2,:2]-a;det=b[:,0]*c[:,1]-b[:,1]*c[:,0];valid=abs(det)>1e-10;det=np.where(valid,det,1);d=np.asarray(xy)-a;u=(d[:,0]*c[:,1]-d[:,1]*c[:,0])/det;v=(b[:,0]*d[:,1]-b[:,1]*d[:,0])/det;inside=valid&(u>=-1e-8)&(v>=-1e-8)&(u+v<=1+1e-8)
  if inside.any():hits.extend((tri[:,0,2]+u*(tri[:,1,2]-tri[:,0,2])+v*(tri[:,2,2]-tri[:,0,2]))[inside])
 assert hits,xy
 return max(hits)
def colors(v,kind):
 palette=[linear([135,167,174])*.52,linear([75,88,82])*.60,linear([42,63,61])*.65];p=np.asarray(v);wear=np.sin(p[:,0]*33.3+p[:,1]*17.8+p[:,2]*5.2)*np.sin(p[:,0]*13.5-p[:,2]*28.7);base=np.tile(palette[kind],(len(p),1));variation=.92+.08*np.sin(p[:,0]*9.2+p[:,1]*4.3)
 if kind==0:
  loss=np.clip((wear-.32)*2.3,0,.85);base=base*(1-loss[:,None])+palette[1]*loss[:,None]
 return np.c_[base*variation[:,None],np.ones(len(p))]
def add(name,m,kind,mat=0,meta=None):
 m.fix_normals();assert m.is_watertight and m.volume>0,(name,m.is_watertight,m.volume);members.append({'name':name,'kind':kind,'verticesNative':m.vertices.round(8).tolist(),'triangles':m.faces.tolist(),'materialIndices':[mat]*len(m.faces),'colors':colors(m.vertices,mat).astype('f4').tolist(),**(meta or {})})
def resample(points,step=.04,curved=False):
 p=np.array(points);t=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))];n=max(2,int(t[-1]/step)+1);tt=np.linspace(0,t[-1],n)
 if curved and len(p)>2:return CubicSpline(t,p,axis=0)(tt)
 return np.stack([np.interp(tt,t,p[:,i]) for i in range(3)],axis=1)
def tube(points,radius=.023,sides=8,curved=False):
 p=resample(points,curved=curved);vv=[];ff=[];t=np.gradient(p,axis=0);t/=np.linalg.norm(t,axis=1)[:,None];a=np.cross(t[0],[0,0,1])
 if np.linalg.norm(a)<.1:a=np.cross(t[0],[0,1,0])
 a/=np.linalg.norm(a)
 for center,axis in zip(p,t):
  a-=axis*np.dot(a,axis);a/=np.linalg.norm(a);b=np.cross(axis,a)
  for th in np.linspace(0,2*np.pi,sides,endpoint=False):vv.append(center+radius*(np.cos(th)*a+np.sin(th)*b))
 for k in range(len(p)-1):
  for j in range(sides):a0=k*sides+j;b0=k*sides+(j+1)%sides;ff.extend([[a0,b0,b0+sides],[a0,b0+sides,a0+sides]])
 first=len(vv);vv.extend([p[0],p[-1]])
 for j in range(sides):k=(j+1)%sides;ff.extend([[first,k,j],[first+1,(len(p)-1)*sides+j,(len(p)-1)*sides+k]])
 return trimesh.Trimesh(vv,ff,process=False)
def screen_rail(label,uv,depth,rad=.023,curved=False,mat=0):
 p=np.array([lift(u,v,depth) for u,v in uv]);add('Poster low frame '+label+' v53',tube(p,rad,8,curved),'frame',mat,{'referencePath708':uv,'inwardDepth':depth});anchors.append({'name':label,'referencePixels':uv,'centerlineNative':p.tolist()});return p
def box(label,center,axes,size,kind,mat=0):
 m=trimesh.creation.box(extents=size);M=np.eye(4);M[:3,:3]=np.array(axes).T;M[:3,3]=center;m.apply_transform(M);add(label,m,kind,mat)

# Visible low frame fragments, separate from the actual entrance stair edges.
back=screen_rail('upper back rail',[[10.7,680.6],[29.5,680.7],[49.6,680.75]],.65,.023)
mid=screen_rail('short lower back rail',[[42.3,687.3],[51,687.2],[59.0,687.2]],.65,.021)
front=screen_rail('lower front rail',[[10.8,692.2],[25.0,692.4],[42.4,692.0]],.95,.024)
screen_rail('sagging inner rail',[[42.5,692.0],[47,693.0],[51.5,694.9],[55.7,695.8]],.90,.018,True,1)
arm=screen_rail('bent right outer frame',[[69.2,680.2],[73.3,681.2],[76.4,683.2],[78.7,687.5],[79.2,697.5]],1.36,.030,True)
screen_rail('bent right inner frame',[[69.2,680.2],[69.2,686.4],[71.3,686.5],[72.6,688.0],[72.4,696.1]],1.77,.025,True)
screen_rail('front damaged upright',[[24.9,688.3],[25.6,690.0],[25.5,693.2],[25.8,699.2]],.90,.017,True,1)

# Foot extensions and small shoes meet the actual sediment surface. The hidden
# connections are inferred, while the visible rails keep the measured paths.
feet=[]
for label,uv,depth,upper in [('left rear',[11.3,680.65],.65,None),('middle rear',[42.4,687.3],.65,None),('left front',[11.0,692.2],.95,None),('middle front',[42.4,692.0],.95,None),('right outer',[79.2,697.5],1.36,arm[-1]),('right inner',[72.4,696.1],1.77,None)]:
 top=lift(*uv,depth) if upper is None else upper;p=top.copy();p[2]=ground_height(p[:2])+.001;assert p[2]<top[2];add('Poster low frame '+label+' grounded leg v53',tube([p,top],.019 if 'front' in label else .023),'leg',0,{'groundContactNative':p.tolist(),'referenceUpper':uv});box('Poster low frame '+label+' foot shoe v53',p+[0,0,.004],[bays[13]['t'],bays[13]['rad'],[0,0,1]],[.075,.083,.012],'shoe',1);feet.append(p.tolist())

# Short closed, broken boards; gaps and the obscuring foliage remain open.
for j,(u0,u1,v,depth,width,height) in enumerate([(11.8,39.8,688.2,.67,.11,.105),(12.4,24.8,690.1,.87,.28,.035),(29.1,40.5,690.05,.87,.28,.035),(43.2,50.9,688.6,.67,.10,.10)]):
 a=lift(u0,v,depth);b=lift(u1,v,depth);axis=b-a;length=np.linalg.norm(axis);axis/=length;depth_axis=np.cross([0,0,1],axis);depth_axis/=np.linalg.norm(depth_axis);up=np.cross(axis,depth_axis);m=trimesh.creation.box(extents=[length,width,height]);M=np.eye(4);M[:3,:3]=np.array([axis,depth_axis,up]).T;M[:3,3]=(a+b)/2;m.apply_transform(M);add(f'Poster low frame broken board {j} v53',m,'board',2,{'observedExtent708':[u0,u1,v],'hiddenThicknessInferred':True})

# Narrow straps and ground-bearing supports beneath the large horizontal pipe.
pipe=next(q for q in json.loads((R/'poster-foreground-v51/foreground-geometry-v51.json').read_text())['members'] if q['name']=='Poster low corroded hollow pipe v51');pv=np.array(pipe['verticesNative']);center_z=(pv[:,2].min()+pv[:,2].max())/2;b=bays[15];pipe_feet=[]
for j,u in enumerate([203.5,219.5,234.5]):
 at=lift(u,693.2,.85,15);x=np.dot(at-b['center'],b['t']);theta=np.linspace(-np.pi/2,np.pi/2,33);vv=[];ff=[]
 for xx,radius in [(x-.023,.184),(x+.023,.184),(x-.023,.154),(x+.023,.154)]:
  for th in theta:vv.append(b['center']+b['t']*xx-b['rad']*(.85+radius*np.cos(th))+[0,0,center_z+radius*np.sin(th)])
 n=len(theta)
 for a,c in [(0,1),(3,2),(2,0),(1,3)]:
  for k in range(n-1):ff.extend([[a*n+k,a*n+k+1,c*n+k+1],[a*n+k,c*n+k+1,c*n+k]])
 for k in [0,n-1]:ff.extend([[k,n+k,3*n+k],[k,3*n+k,2*n+k]])
 contact=b['center']+b['t']*x-b['rad']*(.85+.154)+[0,0,center_z]
 add(f'Poster pipe exposed strap {j} v53',trimesh.Trimesh(vv,ff,process=False),'pipe strap',1,{'referenceU':u,'innerSurfaceNative':contact.tolist(),'outwardNative':(-b['rad']).tolist()})
 p=b['center']+b['t']*x-b['rad']*1.039;p[2]=ground_height(p[:2])+.001;top=p.copy();top[2]=center_z+.228;box(f'Poster pipe support upright {j} v53',(p+top)/2,[b['t'],-b['rad'],[0,0,1]],[.042,.034,top[2]-p[2]],'pipe support',1);box(f'Poster pipe support foot {j} v53',p+[0,0,.005],[b['t'],-b['rad'],[0,0,1]],[.11,.14,.014],'shoe',1);pipe_feet.append(p.tolist())
 for h in [center_z+.11,center_z-.105]:
  a=b['center']+b['t']*x-b['rad']*1.05+[0,0,h];add(f'Poster pipe support bolt {j} {h:.3f} v53',tube([a,a-b['rad']*.018],.011,6),'bolt',0)

out={'revision':53,'sourceNativeSha256':S['sourceNativeSha256'],'sourceObjects':S['objects'],'sourceGeometryFile':'poster-low-rails-v53/source-low-rails-v53.npz','camera':S['camera'],'members':members,'materials':['Poster faded low frame paint v53','Poster corroded low frame metal v53','Poster damaged low frame boards v53'],'newMaterials':[{'name':'Poster faded low frame paint v53','clone':'Poster fine foliage pigments v51','roughness':.85,'metallic':.07},{'name':'Poster corroded low frame metal v53','clone':'Poster fine foliage pigments v51','roughness':.94,'metallic':.12},{'name':'Poster damaged low frame boards v53','clone':'Poster fine foliage pigments v51','roughness':.97,'metallic':0}],'frameGroundContacts':feet,'pipeGroundContacts':pipe_feet,'observedCenterlines':anchors,'scope':'Observed broken low frame and pipe straps/supports. Ambiguous fixture identity, concealed connections and depth inferred. Entrance stair edges are not duplicated as rails.','oneToOneComplete':False}
(O/'low-rails-geometry-v53.json').write_text(json.dumps(out,separators=(',',':')),encoding='utf-8');print('LOW_RAILS_53_BUILT',len(members),sum(len(q['triangles']) for q in members),'triangles')
