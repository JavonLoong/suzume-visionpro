import json,math,sys,warnings
from pathlib import Path
import numpy as np,trimesh
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R.parent/'print-400mm-20261030/.deps'))
import manifold3d as mf
warnings.filterwarnings('ignore');np.random.seed(1040);A=R/'analysis/assembly_meshes'
d=json.loads((R/'交付文件/零件清单.json').read_text(encoding='utf8'));checks=[];bodies={};thickness=[]
def load(n):
 q=np.load(A/(n+'.npz'));mesh=trimesh.Trimesh(q['vertices'],q['faces'],process=False)
 body=mf.Manifold(mf.Mesh64(q['vertices'],q['faces'].astype('uint64')));assert body.status()==mf.Error.NoError,n
 return mesh,body
for row in d['parts']:
 n=row['id'];mesh,body=load(n);bodies[n]=body
 if n[0] not in 'WS' or '_附件' in n:continue
 i=int(n[1:3])-1;radius=180 if n[0]=='W' else 134
 for off in [-10,10]:
  a=math.radians(i*45+22.5+off);hole=mf.Manifold.cylinder(1.6,1.62,circular_segments=64).translate((radius*math.cos(a),radius*math.sin(a),5.2))
  vol=(body^hole).volume();assert vol<.001,(n,'blocked socket',vol)
  checks.append({'part':n,'socket_angle':i*45+22.5+off,'intrusion_mm3':vol})
 if n[0]=='S':
  points,faces=trimesh.sample.sample_surface(mesh,1500);norm=mesh.face_normals[faces]
  keep=points[:,2]>10;points=points[keep];norm=norm[keep]
  hit,rid,_=mesh.ray.intersects_location(points-norm*.0002,-norm,multiple_hits=False)
  t=np.linalg.norm(hit-(points-norm*.0002)[rid],axis=1);t=t[t>.001]
  thickness.append({'part':n,'sample_count':len(t),'p05_mm':float(np.percentile(t,5)),'median_mm':float(np.median(t)),'fraction_below_08':float((t<.8).mean())})
 print('FIT_CHECKED',n,flush=True)
for i in range(1,9):
 w=f'W{i:02d}_环形建筑';s=f'S{i:02d}_钢架';v=(bodies[w]^bodies[s]).volume();assert v<.01,(w,s,'assembly collision',v)
 checks.append({'pair':[w,s],'interference_mm3':v})
door=[]
for angle in [0,15,30,45,60,75,90]:
 moved=bodies['D02_六格门扇'].translate((-5.5,2.2,0)).rotate((0,0,angle)).translate((5.5,-2.2,0))
 v=(moved^bodies['D01_门框与台阶']).volume();assert v<.001,(angle,v)
 door.append({'angle':angle,'interference_mm3':v})
report={'mounting_sockets_and_assembly':checks,'door_angles':door,'steel_normal_ray_samples':thickness,'sampling_limit':'抽样只用于检查细杆改善；锐边、杆端和倒角处厚度自然趋近0，不把抽样最小值当作全部结构的最小厚度。'}
(R/'analysis/final-fit-checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print('FIT_COMPLETE',len(checks),'STEEL',thickness,flush=True)
