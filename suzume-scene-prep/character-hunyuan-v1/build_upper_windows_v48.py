from pathlib import Path
import json,hashlib,numpy as np,trimesh,cv2
from PIL import Image
from shapely.geometry import box,Polygon
from shapely.ops import triangulate

R=Path(__file__).parent;O=R/'poster-upper-windows-v48';F=R/'poster-fascia-v47';V=Path('C:/Users/15410/.codex/visualizations/2026/10/09/01a11f38-1f1d-7dc0-912a-5e87b1c5f103')
native=F/'Suzume_dual_scene_fascia_v47.blend';sha=hashlib.sha256(native.read_bytes()).hexdigest();assert sha==json.loads((F/'release-v47.json').read_text())['nativeSha256']
S=json.loads((F/'source-fascia-v47.json').read_text());D=np.load(F/'source-fascia-v47.npz');C=np.array(S['camera']['position']);rot=np.array(S['camera']['rotation']);f=S['camera']['focalPixels'];plans={q['key']:np.zeros(q['triangles'],'u1') for q in S['objects']}
edges=(np.arange(33)-16.5)*np.pi/16;edges[13:21]=[-.745387,-.567705,-.415142,-.217486,.006904,.147421,.411245,.678266]
bays={}
for i in [13,14]:
 a0,a1=edges[i:i+2];a=(a0+a1)/2;h=(a1-a0)/2;rad=np.array([np.sin(a),np.cos(a),0]);t=np.array([np.cos(a),-np.sin(a),0]);chord=23.5*np.cos(h);w=2*23.5*np.sin(h)+.022;bays[i]={'angle':a,'half':h,'rad':rad,'t':t,'chord':chord,'w':w,'center':rad*chord}
 # Remove the old upper wall and trim the small solid band above the arches.
 for row in S['objects']:
  key=row['key'];v=D[key+'_vertices'];pts=v[D[key+'_faces']];x=(pts-bays[i]['center'])@t;d=-(pts-bays[i]['center'])@rad;z=pts[:,:,2]
  inside=(abs(x)<=w/2+2e-5).all(1)&(d>=-.35002).all(1)&(d<=.00002).all(1)&(z.max(1)<=6.42002)&(z.max(1)>5.48+1e-5)
  plans[key][inside]=2
# Remove complete old bay-13 glass and frame components, including painted faces.
old=json.loads((O/'upper-window-components-v48.json').read_text())['components'];removed_windows=[]
for q in old:
 if 960<=q['component']<=1097:
  removed_windows.append(q['component'])
  for key,ids in q['parts'].items():plans[key][ids]=1

members=[];partitions=[]
def append_mesh(name,m,matids,kind,subdivide=0,extra=None):
 m.fix_normals();assert m.is_watertight and m.volume>0,(name,m.is_watertight,m.volume)
 mats=np.array(matids,int)
 for _ in range(subdivide):
  # Trimesh subdivision preserves face order in groups of four.
  m=m.subdivide();mats=np.repeat(mats,4)
 assert len(m.faces)==len(mats) and m.is_watertight
 record={'name':name,'kind':kind,'verticesNative':m.vertices.round(8).tolist(),'triangles':m.faces.tolist(),'materialIndices':mats.tolist()}
 if extra:record.update(extra)
 members.append(record)

# The reference window crosses this inferred room boundary. Rebuild both
# overlapping room dividers with an open upper storey, retaining their lower
# footprint and roof contact rather than leaving a divider inside the glass.
for i,side in [(13,1),(14,-1)]:
 b=bays[i];h=b['half'];rad=b['rad'];t=b['t'];theta=-side*h
 center=rad*(b['chord']+2.30)+t*side*(b['w']/2+2.3*np.tan(h)-.05)+[0,0,3.66]
 M=np.stack([t*np.cos(theta)+rad*np.sin(theta),[0,0,1],t*np.sin(theta)-rad*np.cos(theta)],axis=1);size=np.array([.22,5.62,4.6/np.cos(h)])
 removed={}
 for row in S['objects']:
  key=row['key'];q=((D[key+'_vertices']-center)@M)[D[key+'_faces']];inside=np.all(abs(q)<=size/2+1e-5,axis=(1,2));planar=np.any(np.all(abs(abs(q)-size/2)<1e-5,axis=1),axis=1);sel=inside&planar
  if sel.any():plans[key][sel]=1;removed[key]=int(sel.sum())
 assert removed.get('mesh18')==162,(i,removed)
 partitions.append({'bay':i,'side':side,'removed':removed,'center':center.tolist(),'matrix':M.tolist(),'size':size.tolist()})
 for low,high,label in [(.85,5.48,'lower'),(6.42,6.47,'roof contact')]:
  m=trimesh.creation.box(extents=[.22,high-low,size[2]]);cc=center.copy();cc[2]=(low+high)/2;m.vertices=np.asarray(m.vertices)@M.T+cc
  centers=m.triangles_center;norm=m.face_normals;direction=C-centers;direction/=np.linalg.norm(direction,axis=1)[:,None];facing=np.sum(norm*direction,axis=1);paint=(facing>.58)&(np.linalg.norm(centers[:,:2],axis=1)<24.02)
  append_mesh(f'Poster upper-storey divider bay {i} {label} v48',m,np.where(paint,0,3),'partition',2)

def unproject_x(b,u,v):
 ray=np.array([(u-354)/f,(500-v)/f,-1])@rot.T;distance=np.dot(b['center']-C,b['rad'])/np.dot(ray,b['rad']);p=C+distance*ray;return float(np.dot(p-b['center'],b['t']))
# Manually observed exterior frame edges; the leftmost opening is partly offscreen.
windows=[{'id':0,'u':[-7.5,18.5],'midV':567,'z':[5.54,6.06]},
         {'id':1,'u':[53,77],'midV':571,'z':[5.52,6.06]},
         {'id':2,'u':[82.5,106],'midV':573,'z':[5.50,6.06]},
         {'id':3,'u':[110.5,134],'midV':574.5,'z':[5.49,6.055]}]
holes={i:[] for i in bays};parts=[]
for w in windows:
 for i,b in bays.items():
  left,right=[unproject_x(b,u,w['midV']) for u in w['u']];x0=max(left,-b['w']/2);x1=min(right,b['w']/2)
  if x1<=x0:continue
  z0,z1=w['z'];holes[i].append(box(x0,z0,x1,z1));parts.append({'id':w['id'],'bay':i,'x':[x0,x1],'z':[z0,z1],'leftExterior':bool(left>=-b['w']/2),'rightExterior':bool(right<=b['w']/2)})

def extrude_section(poly,b,front,back):
 # Triangulate cap polygons and explicitly build all outer and opening reveals.
 vertices=[];faces=[];mats=[];lookup={}
 def vertex(p,depth):
  x,z=p;xx=x*(b['chord']-depth)/b['chord'];pos=b['center']+b['t']*xx-b['rad']*depth+[0,0,z];key=tuple(np.round(pos,9))
  if key not in lookup:lookup[key]=len(vertices);vertices.append(pos)
  return lookup[key]
 tris=[t for t in triangulate(poly) if poly.covers(t)];assert abs(sum(t.area for t in tris)-poly.area)<1e-8
 for tri in tris:
  p=np.asarray(tri.exterior.coords)[:3]
  for depth,mat in [(front,0),(back,1)]:faces.append([vertex(q,depth) for q in p]);mats.append(mat)
 for ring in [poly.exterior,*poly.interiors]:
  points=np.asarray(ring.coords)
  for a,bb in zip(points[:-1],points[1:]):
   q=[vertex(a,front),vertex(bb,front),vertex(bb,back),vertex(a,back)];faces.extend([[q[0],q[1],q[2]],[q[0],q[2],q[3]]]);mats.extend([1,1])
 return trimesh.Trimesh(vertices,faces,process=False),mats

for i,b in bays.items():
 poly=box(-b['w']/2,5.48,b['w']/2,6.42)
 for hole in holes[i]:poly=poly.difference(hole)
 assert poly.geom_type=='Polygon'
 m,mat=extrude_section(poly,b,0,-.35);append_mesh(f'Poster corrected clerestory wall bay {i} v48',m,mat,'wall',3,{'bay':i,'openingAreaSquareMeters':float(sum(h.area for h in holes[i]))})

def frame_box(name,b,x0,x1,z0,z1,front,back,kind,side_material=1):
 m,mat=extrude_section(box(x0,z0,x1,z1),b,front,back);mat=[0 if k==0 else side_material for k in mat];append_mesh(name,m,mat,kind,2 if kind=='glass' else 1)
for p in parts:
 b=bays[p['bay']];x0,x1=p['x'];z0,z1=p['z'];prefix=f'Poster observed upper window {p["id"]} bay {p["bay"]}'
 frame_box(prefix+' upper frame v48',b,x0-.018,x1+.018,z1-.012,z1+.025,.034,-.043,'frame')
 frame_box(prefix+' lower frame v48',b,x0-.018,x1+.018,z0-.022,z0+.017,.04,-.045,'frame')
 for edge,flag in [(x0,p['leftExterior']),(x1,p['rightExterior'])]:
  if flag:frame_box(prefix+(' left' if edge==x0 else ' right')+' jamb v48',b,edge-.018,edge+.018,z0-.008,z1+.008,.035,-.055,'frame')
 frame_box(prefix+' solid glazing v48',b,x0+.010 if p['leftExterior'] else x0,x1-.010 if p['rightExterior'] else x1,z0+.012,z1-.01,-.022,-.030,'glass',2)
for w in windows:
 u=sum(w['u'])/2
 for i,b in bays.items():
  x=unproject_x(b,u,w['midV'])
  if abs(x)<b['w']/2:
   frame_box(f'Poster observed upper window {w["id"]} central mullion v48',b,x-.012,x+.012,w['z'][0]+.009,w['z'][1]-.009,.028,-.033,'frame');break

# Rebuild the same masked, graded surface atlas at its source resolution.
# It remains fixed UV surface color on the new solids, with actual openings.
src=np.asarray(Image.open(V/'reference-hires.jpg').convert('RGB'))[:,:,::-1];official=np.asarray(Image.open(V/'reference-official.jpg').convert('RGB'))[:,:,::-1];H,W=src.shape[:2];mask=np.zeros((H,W),np.uint8);cropmask=np.asarray(Image.open(V/'facade-exclusion-mask-v9.png').convert('L'));mask[1410:2010,:]=cropmask
small=cv2.resize(src,(354,500),interpolation=cv2.INTER_AREA).astype('f4')/255;known=np.zeros((500,354),bool);known[280:348]=True;known &= cv2.resize(mask,(354,500),interpolation=cv2.INTER_AREA)<=20
fit=np.linalg.lstsq(np.c_[small[known],np.ones(known.sum())],official[known].astype('f4')/255,rcond=None)[0]
crop=src[1410:2010];graded=np.clip(np.c_[crop.reshape(-1,3)/255,np.ones(600*2000)]@fit,0,1).reshape(600,2000,3)
# These two foreground hangers were missing from the original exclusion mask.
# Without removing them they appear twice when the camera rotates.
thinmask=np.zeros((600,2000),np.uint8)
rod_paths=[[[159,1568],[164,1599],[174,1634],[188,1673],[191,1685]],[[333,1587],[337,1610],[340,1625]]]
for path in rod_paths:cv2.polylines(thinmask,[np.array(path,np.int32)-[0,1410]],False,255,10)
texture=cv2.inpaint(np.rint(graded*255).astype('u1'),cv2.bitwise_or(cropmask,thinmask),9,cv2.INPAINT_TELEA);Image.fromarray(texture[:,:,::-1]).save(O/'upper-facade-pigments-v48.png')
old_image=O/'original-facade-pigments-v48.png';assert hashlib.sha256(old_image.read_bytes()).hexdigest()=='0a3213ef7c7033e4b5d3b8c9ff43d630f0118aeb8d23867c3c9d36834f3a5498'
old_pixels=np.asarray(Image.open(old_image).convert('RGB'));smallmask=(cv2.resize(thinmask,(1100,330),interpolation=cv2.INTER_AREA)>0).astype('u1')*255;clean=cv2.inpaint(old_pixels,smallmask,5,cv2.INPAINT_TELEA);assert np.array_equal(old_pixels[smallmask==0],clean[smallmask==0]);Image.fromarray(clean).save(O/'clean-facade-pigments-v48.png');Image.fromarray(smallmask).save(O/'thin-rod-exclusion-mask-v48.png')
cleanup={'sourcePackedImageSha256':hashlib.sha256(old_image.read_bytes()).hexdigest(),'sourceResolution':[1100,330],'maskPixels':int((smallmask>0).sum()),'outsideMaskPixelsPreservedExactly':True,'removedForegroundPaths2000x2824':rod_paths,'cleanImageSha256':hashlib.sha256((O/'clean-facade-pigments-v48.png').read_bytes()).hexdigest(),'limits':'Only the two observed thin foreground hanger traces are removed. Hidden color is interpolated; physical hanger tip alignment still needs refinement.'};(O/'facade-cleanup-v48.json').write_text(json.dumps(cleanup,indent=2))
np.savez_compressed(O/'upper-window-removal-v48.npz',**plans)
out={'revision':48,'sourceNativeSha256':sha,'sourceObjects':S['objects'],'camera':S['camera'],'sourceGeometryFile':'poster-fascia-v47/source-fascia-v47.npz','clipHeight':5.48,'manualWindowObservations':windows,'windowParts':parts,'members':members,'replacedPartitions':partitions,'removedWindowComponents':removed_windows,'changes':{k:{'removedTriangles':int((p==1).sum()),'clippedTriangles':int((p==2).sum())} for k,p in plans.items() if p.any()},'atlasBounds':[0,1410,2000,2010],'atlasResolution':[2000,600],'atlasSha256':hashlib.sha256((O/'upper-facade-pigments-v48.png').read_bytes()).hexdigest(),'cleanAtlasSha256':cleanup['cleanImageSha256'],'scope':'Actual wall apertures, fixed-UV solid glazing, frames and upper-storey partition clearance. View-dependent glazing reflection and concealed construction remain approximations.','oneToOneComplete':False}
(O/'upper-window-geometry-v48.json').write_text(json.dumps(out,separators=(',',':')));print('UPPER_WINDOWS_48_GEOMETRY',len(members),'closed solids',sum(len(q['triangles']) for q in members),'triangles',out['changes'])
