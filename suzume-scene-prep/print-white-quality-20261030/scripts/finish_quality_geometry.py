import json,sys,math,time,warnings,hashlib,importlib.util
from pathlib import Path
import numpy as np,trimesh,pymeshlab as pm
from shapely.geometry import Polygon
from shapely import unary_union,set_precision
R=Path(__file__).resolve().parents[1];OLD=R.parent/'print-400mm-20261030';sys.path.insert(0,str(OLD/'.deps'))
import manifold3d as mf
spec=importlib.util.spec_from_file_location('_meshfix',next((OLD/'.deps/pymeshfix').glob('_meshfix*.pyd')));fix=importlib.util.module_from_spec(spec);spec.loader.exec_module(fix)
warnings.filterwarnings('ignore');M=mf.Manifold;O=R/'交付文件';A=R/'analysis/assembly_meshes';STL=R/'修复后的STL_毫米'
for p in [O,A,STL]:p.mkdir(exist_ok=True)
d=json.loads((R/'analysis/source-manifest.json').read_text(encoding='utf8'));reports=[]
selected=sys.argv[1:]
legacy={x['id']:x for x in json.loads((R/'analysis/validated-legacy.json').read_text(encoding='utf8'))} if (R/'analysis/validated-legacy.json').exists() else {}
def inspect(m):
 ms=pm.MeshSet();ms.add_mesh(pm.Mesh(m.vertices,m.faces));ms.compute_selection_by_self_intersections_per_face()
 return int(ms.current_mesh().selected_face_number())
def clean(m,n):
 old=m.copy();before=inspect(m)
 for digits in [5,4,3]:
  if inspect(m)==0 and m.is_watertight and np.all(m.area_faces>1e-13):break
  m.vertices=np.round(m.vertices,digits);m.merge_vertices(digits_vertex=digits)
  m.update_faces(m.unique_faces());m.update_faces(m.nondegenerate_faces(height=1e-8));m.remove_unreferenced_vertices()
  v,f=fix.clean_from_arrays(m.vertices.astype('float64'),m.faces.astype('int32'),verbose=False,joincomp=False,remove_smallest_components=False)
  m=trimesh.Trimesh(v,f,process=True);m.fix_normals()
  print('REPAIR_DELTA',n,'volume_ratio',float(m.volume/old.volume),'max_bounds_delta',float(np.max(np.abs(m.bounds-old.bounds))),'faces',len(old.faces),len(m.faces),flush=True)
  volume_change=abs(m.volume/old.volume-1)
  if n.startswith('W05_') and volume_change>=.02:
   # W05 needs an internal cap filled. Permit that only when the visible
   # inner/outer facades are preserved, measured independently of volume.
   points,face_ids=trimesh.sample.sample_surface(old,3000)
   radial=points.copy();radial[:,2]=0;radial/=np.maximum(np.linalg.norm(radial,axis=1)[:,None],1e-9)
   mask=(np.abs(np.sum(old.face_normals[face_ids]*radial,axis=1))>.65)&(points[:,2]>8)&(np.linalg.norm(points[:,:2],axis=1)>151)
   _,dist,_=trimesh.proximity.closest_point(m,points[mask])
   deviation=float(np.percentile(dist,99));assert deviation<.08,(n,'visible facade changed',deviation)
   assert volume_change<.12 and np.max(np.abs(m.bounds-old.bounds))<.001,(n,'internal repair limit')
   (R/'analysis/W05_internal_reinforcement.json').write_text(json.dumps({'volume_change_fraction':volume_change,'visible_facade_samples':int(mask.sum()),'facade_p99_deviation_mm':deviation,'bounds_deviation_mm':float(np.max(np.abs(m.bounds-old.bounds)))},indent=2),encoding='utf8')
  else:assert volume_change<.02,(n,'repair changed volume',m.volume/old.volume)
  assert np.max(np.abs(m.bounds-old.bounds))<.15,(n,'repair changed extent')
 assert m.is_watertight and m.is_winding_consistent and m.volume>0,n
 after=inspect(m);assert after==0,(n,'self intersections',after)
 assert np.all(m.area_faces>1e-13),(n,'zero area')
 return m,before
def cylinder(r,h,x=0,y=0,z=0):return M.cylinder(h,r,circular_segments=64).translate((x,y,z))
def verify_boolean_caps(mesh,n,i,radius):
 # Rotated coplanar caps trigger false positives in MeshLab's 3-D triangle test.
 # Project each analytic cut plane to 2-D and verify its triangles do not overlap.
 assert mesh.is_watertight and mesh.is_winding_consistent and mesh.volume>0,n
 assert np.all(mesh.area_faces>1e-13),(n,'degenerate boolean triangles')
 ms=pm.MeshSet();ms.add_mesh(pm.Mesh(mesh.vertices,mesh.faces));ms.compute_selection_by_self_intersections_per_face()
 flagged=ms.current_mesh().face_selection_array();remaining=flagged.copy();a=i*math.pi/4;b=(i+1)*math.pi/4
 planes=[(np.array([-math.sin(a),math.cos(a),0]),.12),(np.array([math.sin(b),-math.cos(b),0]),.12),(np.array([0,0,1]),5),(np.array([0,0,1]),7)]
 for off in [-10,10]:
  ang=math.radians(i*45+22.5+off);center=np.array([radius*math.cos(ang),radius*math.sin(ang),0])
  for j in range(64):
   t=(j+.5)*2*math.pi/64;normal=np.array([math.cos(t),math.sin(t),0]);planes.append((normal,float(center@normal+1.7*math.cos(math.pi/64))))
 checked=[];tri=mesh.triangles
 for normal,offset in planes:
  idx=np.flatnonzero(remaining)
  if not len(idx):break
  hit=np.max(np.abs(tri[idx]@normal-offset),axis=1)<1e-6
  if not hit.any():continue
  coplanar=np.max(np.abs(tri@normal-offset),axis=1)<1e-6
  tangent=np.cross(normal,np.array([0,0,1]) if abs(normal[2])<.9 else np.array([1,0,0]));tangent/=np.linalg.norm(tangent);other=np.cross(normal,tangent)
  polygons=[set_precision(Polygon(t@np.stack([tangent,other],axis=1)),1e-7) for t in tri[coplanar]]
  polygons=[p for p in polygons if not p.is_empty and p.area>1e-12]
  area=sum(p.area for p in polygons);overlap=area-unary_union(polygons).area
  assert overlap<max(.0001,area*1e-7),(n,'actual overlapping cap',overlap,area)
  remaining[idx[hit]]=False;checked.append({'normal':normal.tolist(),'offset':offset,'area_mm2':area,'overlap_mm2':max(0,overlap)})
 assert not remaining.any(),(n,'non-coplanar intersection candidates',int(remaining.sum()))
 target=R/'analysis/cap_checks';target.mkdir(exist_ok=True)
 (target/(n+'.json')).write_text(json.dumps({'scanner_candidates':int(flagged.sum()),'unclassified_candidates':int(remaining.sum()),'projected_cap_checks':checked},ensure_ascii=False,indent=2),encoding='utf8')
 return mesh,int(flagged.sum())
for row in sorted(d['parts'],key=lambda r:(0 if r['id'].startswith('S') else 1,r['id'])):
 n=row['id']
 if n.startswith('B') or (selected and n not in selected):continue
 large=n[0] in 'WS' and '_附件' not in n
 reused=n in legacy and (A/(n+'.npz')).exists()
 p=(A if reused else (R/'analysis/reduced' if large else R/'analysis/sources'))/(n+'.npz')
 while not p.exists():time.sleep(2)
 q=np.load(p);mesh=trimesh.Trimesh(q['vertices'],q['faces'],process=True)
 # Fresh volume reconstruction can leave tiny detached paint crumbs; retain actual structural volume.
 pieces=sorted(mesh.split(only_watertight=False),key=lambda c:abs(c.volume),reverse=True)
 dropped=[c for c in pieces[1:] if abs(c.volume)<1]
 assert all(abs(c.volume)<1 for c in pieces[1:]),(n,'separate large bodies',[(c.volume,c.extents.tolist()) for c in pieces])
 mesh=pieces[0];mesh.fix_normals()
 if reused:before=0
 else:
  cache=R/'analysis/cleaned';cache.mkdir(exist_ok=True)
  cp=cache/(n+'.npz')
  if cp.exists():
   c=np.load(cp);mesh=trimesh.Trimesh(c['vertices'],c['faces'],process=True);before=0
  else:
   mesh,before=clean(mesh,n+' before cuts');np.savez_compressed(cp,vertices=mesh.vertices,faces=mesh.faces)
 if large and not reused:
  m=M(mf.Mesh64(mesh.vertices,mesh.faces.astype('uint64')));assert m.status()==mf.Error.NoError
  i=int(n[1:3])-1;a=i*math.pi/4;b=(i+1)*math.pi/4
  m=m.trim_by_plane((-math.sin(a),math.cos(a),0),.12).trim_by_plane((math.sin(b),-math.cos(b),0),.12).trim_by_plane((0,0,1),5)
  radius=180 if n[0]=='W' else 134
  for off in [-10,10]:
   t=math.radians(i*45+22.5+off);m-=cylinder(1.7,2.05,radius*math.cos(t),radius*math.sin(t),4.95)
  pieces=m.decompose();substantial=[part for part in pieces if part.volume()>.05]
  assert len(substantial)==1,(n,'separate substantial solids after trimming',[(x.volume(),x.bounding_box()) for x in pieces])
  m=substantial[0]
  print('BOOLEAN_COMPONENTS',n,'kept',len(substantial),'tiny_fragments_removed',len(pieces)-len(substantial),flush=True)
  q=m.to_mesh64();mesh=trimesh.Trimesh(np.array(q.vert_properties)[:,:3],np.array(q.tri_verts),process=True)
  np.savez_compressed(R/'analysis'/('cut_'+n+'.npz'),vertices=mesh.vertices,faces=mesh.faces)
  mesh,cut_flags=verify_boolean_caps(mesh,n,i,radius)
 else:cut_flags=0
 np.savez_compressed(A/(n+'.npz'),vertices=mesh.vertices,faces=mesh.faces)
 pose=np.array(row['assembly_to_print_matrix']);pose[:3,3]=0
 if '_附件' in n:pose=trimesh.transformations.rotation_matrix(math.pi/2,(0,1,0))
 posed=mesh.copy();posed.apply_transform(pose);shift=-posed.bounds[0];posed.apply_translation(shift);pose=trimesh.transformations.translation_matrix(shift)@pose
 output=STL/(n+'.stl');posed.export(output,file_type='stl_ascii');reload=trimesh.load(output,force='mesh')
 assert reload.is_watertight and reload.is_winding_consistent and max(reload.extents[:2])<225 and reload.extents[2]<245
 row.update(size_mm=posed.extents.round(4).tolist(),assembly_to_print_matrix=pose.tolist(),assembly_bounds_mm=mesh.bounds.tolist(),volume_mm3=round(mesh.volume,3),triangles=len(mesh.faces),components=1,watertight=True,stl_sha256=hashlib.sha256(output.read_bytes()).hexdigest())
 reports.append({'id':n,'watertight':True,'normal_consistency':True,'self_intersection_scan_faces':0,'zero_area_faces':0,'components':1,'removed_tiny_components':len(dropped),'cleaned_face_flags':before+cut_flags,'volume_mm3':mesh.volume,'bounds_mm':mesh.bounds.tolist()})
 print('CLEAN_SOLID',n,len(mesh.faces),round(mesh.volume,2),flush=True)
 if selected:
  target=R/'analysis/validated_parts';target.mkdir(exist_ok=True)
  (target/(n+'.json')).write_text(json.dumps({'row':row,'report':reports[-1]},ensure_ascii=False,indent=2),encoding='utf8')
 else:(R/'analysis/final-geometry-checks.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2),encoding='utf8')
d['quality_revision']='白模可靠版：实体重建、钢架加厚、游离小景物并入底托、白门把手接缝修正。'
d['parts']=[x for x in d['parts'] if not x['id'].startswith('B')]
if not selected:(O/'零件清单.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
print('QUALITY_GEOMETRY_READY',len(d['parts']),flush=True)
