from pathlib import Path
import json,numpy as np,trimesh,cv2
from PIL import Image
from scipy.interpolate import CubicSpline
from scipy.cluster.vq import kmeans2
R=Path(__file__).parent;O=R/'poster-foreground-v51';V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103');S=json.loads((O/'source-foreground-v51.json').read_text());C=np.array(S['camera']['position']);rot=np.array(S['camera']['rotation']);f=S['camera']['focalPixels'];rng=np.random.default_rng(51051);members=[];plant_stats=[]
image=np.array(Image.open(V/'reference-hires.jpg').convert('RGB').resize((708,1000)));hsv=cv2.cvtColor(image,cv2.COLOR_RGB2HSV);green=(hsv[:,:,0]>=33)&(hsv[:,:,0]<=94)&(image[:,:,1].astype(float)>image[:,:,0]*1.07)&(image[:,:,1].astype(float)>image[:,:,2]*.98)&(hsv[:,:,1]>20)
edges=(np.arange(33)-16.5)*np.pi/16;edges[13:21]=[-.745387,-.567705,-.415142,-.217486,.006904,.147421,.411245,.678266];bays={}
for i in range(12,18):
 a0,a1=edges[i:i+2];a=(a0+a1)/2;h=(a1-a0)/2;r=np.array([np.sin(a),np.cos(a),0]);t=np.array([np.cos(a),-np.sin(a),0]);bays[i]={'rad':r,'t':t,'center':r*23.5*np.cos(h),'chord':23.5*np.cos(h),'w':47*np.sin(h)+.022}
def lift(u,v,i=None,depth=.7):
 ray=np.array([(u-354)/f,(500-v)/f,-1])@rot.T
 for j,b in ([(i,bays[i])] if i is not None else bays.items()):
  p=C+ray*np.dot(b['center']-b['rad']*depth-C,b['rad'])/np.dot(ray,b['rad']);x=np.dot(p-b['center'],b['t'])
  if i is not None or abs(x)<b['w']/2+.01:return p,j
 raise ValueError((u,v))
def local(i,x,z,d):
 b=bays[i];return b['center']+b['t']*x-b['rad']*d+[0,0,z]
def project(p):
 q=(np.asarray(p)-C)@rot;return np.stack((354+f*q[...,0]/-q[...,2],500-f*q[...,1]/-q[...,2]),axis=-1)
def linear(c):
 c=np.asarray(c)/255;return np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4)
def add(name,mesh,kind,mat=0,colors=None,metadata=None):
 mesh.fix_normals();assert mesh.is_watertight and mesh.volume>0,(name,mesh.is_watertight,mesh.volume)
 if colors is None:colors=np.ones((len(mesh.vertices),4))
 materials=np.full(len(mesh.faces),mat,int)
 if mat==0:
  facing=np.sum(mesh.face_normals*(C-mesh.triangles_center)/np.linalg.norm(C-mesh.triangles_center,axis=1)[:,None],axis=1);materials[facing<-.15]=1
 members.append({'name':name,'kind':kind,'verticesNative':mesh.vertices.round(8).tolist(),'triangles':mesh.faces.tolist(),'materialIndices':materials.tolist(),'colors':np.asarray(colors,dtype='f4').tolist(),**(metadata or {})})
def tube(points,radius,sides=10,cap=True):
 p=np.asarray(points);radius=np.broadcast_to(np.asarray(radius),(len(p),));vv=[];ff=[]
 tangents=np.gradient(p,axis=0);tangents/=np.linalg.norm(tangents,axis=1)[:,None];a=np.cross(tangents[0],[0,0,1])
 if np.linalg.norm(a)<.1:a=np.cross(tangents[0],[0,1,0])
 a/=np.linalg.norm(a)
 for k,t in enumerate(tangents):
  a=a-t*np.dot(a,t);a/=np.linalg.norm(a);b=np.cross(t,a)
  for theta in np.linspace(0,2*np.pi,sides,endpoint=False):vv.append(p[k]+radius[k]*(np.cos(theta)*a+np.sin(theta)*b))
 for k in range(len(p)-1):
  for j in range(sides):jj=(j+1)%sides;ff.extend([[k*sides+j,k*sides+jj,(k+1)*sides+jj],[k*sides+j,(k+1)*sides+jj,(k+1)*sides+j]])
 if cap:
  first=len(vv);vv.extend([p[0],p[-1]])
  for j in range(sides):jj=(j+1)%sides;ff.extend([[first,jj,j],[first+1,(len(p)-1)*sides+j,(len(p)-1)*sides+jj]])
 m=trimesh.Trimesh(vv,ff,process=False);m.fix_normals();return m
def smooth(points,count=24):
 p=np.asarray(points);t=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))];return CubicSpline(t,p,axis=0)(np.linspace(0,t[-1],count))
def solid_box(name,center,axes,size,kind,mat=0):
 m=trimesh.creation.box(extents=size);M=np.eye(4);M[:3,:3]=np.array(axes).T;M[:3,3]=center;m.apply_transform(M);add(name,m,kind,mat)

# Lower rusted pipe: the ends, collars and upright return are modeled volumes.
b=bays[15];center,_=lift(219,693.2,15,.85);z=center[2];left,_=lift(172.0,693.2,15,.85);right,_=lift(264,693.2,15,.85);xl=np.dot(left-b['center'],b['t']);xr=np.dot(right-b['center'],b['t']);n=48;vv=[];ff=[]
for x,radius in [(xl,.155),(xr,.155),(xl,.135),(xr,.135)]:
 for th in np.linspace(0,2*np.pi,n,endpoint=False):vv.append(local(15,x,z+radius*np.sin(th),.85+radius*np.cos(th)))
for a,c in [(0,1),(3,2),(2,0),(1,3)]:
 for j in range(n):k=(j+1)%n;ff.extend([[a*n+j,a*n+k,c*n+k],[a*n+j,c*n+k,c*n+j]])
add('Poster low corroded hollow pipe v51',trimesh.Trimesh(vv,ff,process=False),'pipe',metadata={'referenceCenter':[219,693.2],'radius':.155,'hollow':True})
for j,u in enumerate([204.0,234.5]):
 p,_=lift(u,693.2,15,.85);x=np.dot(p-b['center'],b['t']);add(f'Poster pipe collar {j} v51',tube([local(15,x-.025,z,.85),local(15,x+.025,z,.85)],.178,32),'pipe')
return_pixels=[[243.4,698.1],[242.5,686],[243.1,682.5],[245.5,681.5],[251.5,681.7],[258,682.1]];return_points=np.array([lift(u,v,15,1.19)[0] for u,v in return_pixels]);add('Poster curved standpipe v51',tube(smooth(return_points,60),.047,12),'standpipe',metadata={'referencePath':return_pixels})
for j,index in enumerate([0,2]):
 p=return_points[index];add(f'Poster standpipe joint {j} v51',tube([p-[0,0,.037],p+[0,0,.037]],.064,16),'standpipe')
foot=return_points[0].copy();foot[2]=max(.07,foot[2]-.035);solid_box('Poster standpipe foot v51',foot-[0,0,.04],[b['t'],b['rad'],[0,0,1]],[.18,.20,.08],'support')

# The observed discarded item reads as a worn chair, not two box-shaped units.
b=bays[14];chair_center,_=lift(149.4,685.9,14,.63);cx=np.dot(chair_center-b['center'],b['t']);seat=chair_center[2];top=lift(149.4,675.4,14,.34)[0][2];floor=seat-.405;half=.29;backd=.38;frontd=.91
frame_local=[[-half,seat+.035,backd],[-half,top-.045,backd-.105],[-half+.045,top,backd-.115],[half-.045,top,backd-.115],[half,top-.045,backd-.105],[half,seat+.035,backd]]
frame=np.array([local(14,cx+x,h,d) for x,h,d in frame_local]);add('Poster discarded chair back frame v51',tube(smooth(frame,60),.018,10),'chair',metadata={'referenceBackTop':[149.4,675.4],'inferredObjectType':'discarded chair'})
for side in [-1,1]:
 pts=[local(14,cx+side*half,floor,frontd+.035),local(14,cx+side*half,seat-.025,frontd),local(14,cx+side*half,seat,backd),local(14,cx+side*half,floor,backd-.075)];add(f'Poster chair leg frame {side} v51',tube(smooth(pts,32),.016,10),'chair')
 add(f'Poster chair side brace {side} v51',tube([local(14,cx+side*half,floor+.07,frontd),local(14,cx+side*half,seat-.08,backd)],.009,8),'chair')
for j,d in enumerate([frontd,backd]):add(f'Poster chair seat crossbar {j} v51',tube([local(14,cx-half,seat,d),local(14,cx+half,seat,d)],.014,10),'chair')
# Closed thin back upholstery, with rounded upper corners and a shallow bow.
outline=[[-half+.025,seat+.04],[-half+.025,top-.062],[-half+.072,top-.025],[half-.068,top-.025],[half-.025,top-.062],[half-.025,seat+.04]];vv=[]
for layer in [-.008,.008]:
 for x,h in outline:
  d=backd-(h-seat)/(top-seat)*.115+layer;vv.append(local(14,cx+x,h,d))
ff=[];nn=len(outline)
for j in range(1,nn-1):ff.extend([[0,j,j+1],[nn,nn+j+1,nn+j]])
for j in range(nn):k=(j+1)%nn;ff.extend([[j,k,nn+k],[j,nn+k,nn+j]])
add('Poster chair worn back panel v51',trimesh.Trimesh(vv,ff,process=False),'chair')
solid_box('Poster chair seat panel v51',local(14,cx,seat-.023,(frontd+backd)/2),[b['t'],-b['rad'],[0,0,1]],[half*1.88,frontd-backd,.026],'chair')
solid_box('Poster chair landing stone v51',local(14,cx,floor-.075,(frontd+backd)/2),[b['t'],-b['rad'],[0,0,1]],[.81,.85,.15],'support')

def leaf(base,axis,length,width,normal):
 axis=axis/np.linalg.norm(axis);normal=normal-axis*np.dot(normal,axis);normal/=np.linalg.norm(normal);side=np.cross(axis,normal)
 outline=np.array([[0,0],[-.27,.20],[-.48,.50],[-.40,.72],[0,1],[.40,.72],[.48,.50],[.27,.20]])
 vv=[base+side*x*width+axis*y*length for x,y in outline];vv.extend([base+axis*length*.48+normal*.0025,base+axis*length*.48-normal*.0012]);ff=[]
 for j in range(8):k=(j+1)%8;ff.extend([[8,j,k],[9,k,j]])
 m=trimesh.Trimesh(vv,ff,process=False);m.fix_normals();return m
def combine_parts(name,parts,colors,kind,meta):
 m=trimesh.util.concatenate(parts);col=np.concatenate(colors);add(name,m,kind,2,col,meta)
def foliage_color(u,v):
 pixel=image[int(np.clip(v,0,999)),int(np.clip(u,0,707))];base=linear(pixel)*.70
 # Preserve muted blue-green variation; very dark samples retain some light.
 return np.clip(base,[.010,.018,.013],[.12,.18,.135])
regions=[('left margin',[0,687,30,705],[17,701],150,.85),('left window shrub',[39,670,75,700],[58,698],330,.85),('pier growth',[76,654,100,699],[86,698],250,.46),('entry left growth',[96,653,111,698],[100,697],150,.35),('pipe left thicket',[175,680,211,707],[195,704],360,1.40),('pipe ground creeper',[207,696,247,708],[226,706],180,1.65),('return pipe growth',[232,683,250,701],[241,702],100,1.43),('right ground growth',[259,690,303,710],[280,706],230,1.4)]
for label,bounds,rootuv,count,depth in regions:
 x0,y0,x1,y1=bounds;yy,xx=np.where(green[y0:y1,x0:x1]);assert len(xx)>5,(label,'no reference foliage pixels');pixels=np.c_[xx+x0,yy+y0];chosen=pixels[rng.integers(0,len(pixels),count)]+rng.uniform(-.3,.3,(count,2));root,bi=lift(*rootuv,depth=depth);root[2]=max(.10,root[2]);points=[]
 for u,v in chosen:
  p,_=lift(u,v,bi,depth+rng.uniform(-.11,.16));p[2]=max(root[2]+.02,p[2]);points.append(p)
 points=np.array(points);branch_count=max(5,count//22);centers,labels=kmeans2(points,branch_count,minit='points',seed=51051);parts=[];colors=[];stemcolor=np.array([.027,.038,.024,1.])
 for center in centers:
  low=root+(center-root)*.42;low[2]-=.06;part=tube([root,low,center],np.array([.006,.004,.0025]),6);parts.append(part);colors.append(np.tile(stemcolor,(len(part.vertices),1)))
 for j,(p,(u,v)) in enumerate(zip(points,chosen)):
  length=rng.uniform(.06,.13);width=length*rng.uniform(.35,.65);axis=rng.normal(0,.55,3);axis[2]+=rng.uniform(.1,1.3);axis/=np.linalg.norm(axis);normal=(C-p)/np.linalg.norm(C-p)+rng.normal(0,.5,3);base=p-axis*length*.48;m=leaf(base,axis,length,width,normal);color=foliage_color(u,v)*rng.uniform(.82,1.10);col=np.tile(np.r_[color,1],(len(m.vertices),1));col[-2,:3]*=1.07;col[-1,:3]*=.78;parts.append(m);colors.append(col)
  branch=centers[labels[j]];middle=(branch+base)/2;middle[2]+=.018;petiole=tube([branch,middle,base],np.array([.0024,.0016,.0008]),5);parts.append(petiole);colors.append(np.tile(stemcolor,(len(petiole.vertices),1)))
 combine_parts('Poster fine '+label+' v51',parts,colors,'foliage',{'leafCount':count,'referenceBounds':bounds,'referenceGreenPixels':len(pixels),'root':root.tolist(),'depthInferred':True});plant_stats.append({'name':label,'leaves':count,'eligiblePixels':len(pixels)})

# Narrow grass blades grow from several reference-observed patches.
for k,(u,v,height,count) in enumerate([(180,697,.60,28),(196,697,.83,34),(216,697,.57,26),(238,703,.24,20),(28,699,.31,18)]):
 root,bi=lift(u,v,depth=1.20);root[2]=max(.10,root[2]);parts=[];colors=[]
 for j in range(count):
  base=root+rng.normal(0,[.12,.08,.012]);h=height*rng.uniform(.50,1.10);lean=rng.normal(0,[.21,.18,0]);tip=base+lean+[0,0,h];mid=(base+tip)/2+lean*.10;part=tube(smooth([base,mid,tip],7),np.linspace(rng.uniform(.004,.009),.00045,7),4);parts.append(part);colors.append(np.tile([.037,.063,.037,1],(len(part.vertices),1)))
 combine_parts(f'Poster fine grass patch {k} v51',parts,colors,'grass',{'blades':count,'root':root.tolist()})

# A fixed 3D climbing vine wraps the observed steel column, not a billboard.
steel=json.loads((R/'poster-left-steel-v44/steel-geometry-v44.json').read_text());line=np.array(next(q for q in steel['members'] if q['name']=='Poster left middle bowed I-column v44')['centerlineNative']);zs=np.linspace(.24,3.60,90);right_axis=rot[:,0];p=np.stack([np.interp(zs,line[:,2],line[:,j]) for j in range(3)],axis=1);toward=C-p;toward[:,2]=0;toward/=np.linalg.norm(toward,axis=1)[:,None];p-=right_axis*(.16+.025*np.sin(zs*9))[:,None];p+=toward*.065;parts=[tube(p,.006,6)];colors=[np.tile([.027,.038,.024,1],(len(parts[0].vertices),1))]
for j in range(2,len(p)-2):
 for side in [-1,1]:
  base=p[j];axis=-right_axis*(.75 if side==-1 else -.25)+np.array([0,0,.45])+rng.normal(0,.22,3);axis/=np.linalg.norm(axis);length=rng.uniform(.055,.10);target=base+axis*.03;m=leaf(target,axis,length,length*.64,toward[j]+rng.normal(0,.45,3));parts.append(m);colors.append(np.tile([.035,.071,.042,1],(len(m.vertices),1)));pet=tube([base,target],.0014,5);parts.append(pet);colors.append(np.tile([.027,.038,.024,1],(len(pet.vertices),1)))
combine_parts('Poster fine steel-climbing vine v51',parts,colors,'foliage',{'leafCount':172,'attachedColumn':'Poster left middle bowed I-column v44','depthInferred':True})

# Sparse trailing ivy along the facade follows the observed wavering route.
uvline=np.array([[91,583],[94,596],[92,611],[94,628],[94,643],[96,658],[96,674],[101,690]]);vpath=smooth(np.array([lift(u,v,depth=.34)[0] for u,v in uvline]),95);parts=[tube(vpath,np.linspace(.004,.006,len(vpath)),6)];colors=[np.tile([.028,.04,.028,1],(len(parts[0].vertices),1))]
for j in range(1,len(vpath)-1):
 for side in [-1,1]:
  base=vpath[j];axis=right_axis*side+.5*np.array([0,0,1])+rng.normal(0,.4,3);axis/=np.linalg.norm(axis);length=rng.uniform(.05,.095);m=leaf(base+axis*.022,axis,length,length*.6,C-base+rng.normal(0,.5,3));parts.append(m);colors.append(np.tile([.036,.071,.047,1],(len(m.vertices),1)));pet=tube([base,base+axis*.023],.0013,5);parts.append(pet);colors.append(np.tile([.028,.04,.028,1],(len(pet.vertices),1)))
combine_parts('Poster thin facade climbing trail v51',parts,colors,'foliage',{'leafCount':186,'referencePath':uvline.tolist(),'depthInferred':True})

out={'revision':51,'sourceNativeSha256':S['sourceNativeSha256'],'sourceObjects':S['objects'],'sourceGeometryFile':'poster-foreground-v51/source-foreground-v51.npz','camera':S['camera'],'members':members,'materials':['Reference-calibrated upper facade pigments v48','Poster upper window recessed faces v48','Poster fine foliage pigments v51'],'newMaterial':{'name':'Poster fine foliage pigments v51','clone':'Individual three-dimensional ivy leaves vertex pigments.001','attribute':'surface_color','roughness':.96},'plantRegions':plant_stats,'oldIvyRemovalFile':'ivy-removal-v51.json','oldPropRemovalFile':'prop-removal-v51.npz','oneToOneComplete':False,'scope':'Observed foreground pipe, inferred discarded chair, smaller volumetric foliage, fine grass and climbing stems. Unseen foliage depth and hidden object structure remain inferred.'}
(O/'foreground-geometry-v51.json').write_text(json.dumps(out,separators=(',',':')));print('FOREGROUND_51_BUILT',len(members),'members',sum(len(q['triangles']) for q in members),'triangles',sum(q.get('leafCount',0) for q in members),'leaves','pipeZ',z,'chairSeat',seat,'chairFloor',floor)
