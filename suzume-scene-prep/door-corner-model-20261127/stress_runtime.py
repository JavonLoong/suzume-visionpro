import sys,json,math,time
from pathlib import Path
import numpy as np,cv2,torch
O=Path('D:/虚拟C盘/学习秋/单门内沿贴合训练_20261125')
OUTPUT=Path(__file__).resolve().parent
sys.path.insert(0,'D:/虚拟C盘/JavonLoongSkill/suzume-scene-prep/door-keypoint-model-20261118')
from common import *
torch.set_num_threads(4);cv2.setNumThreads(0)
selected=json.loads((O/'模型交付/模型核验.json').read_text(encoding='utf-8'))['selected']
cases=[]
modes=['normal','small20pct','tiny10pct','offset_left','offset_right','roll_minus12','roll_plus12','dark','bright','blur','jpeg','perspective','one_corner_occluded']
for p in sorted((O/'dataset/labels').glob('*.json')):
 l=json.loads(p.read_text(encoding='utf-8'));gray=imread_gray(O/'dataset'/l['image']);kp=np.array(l['keypoints'])[:,:2];size=max(kp.max(0)-kp.min(0))
 for mode in modes:
  fill=.10 if mode=='tiny10pct' else .20 if mode=='small20pct' else .45
  theta=math.radians(-12 if mode=='roll_minus12' else 12 if mode=='roll_plus12' else 0)
  A=make_affine((kp.max(0)+kp.min(0))/2,size/(fill*IN_H),theta)
  if mode.startswith('offset_'):
   target=np.array([IN_W*(.25 if mode=='offset_left' else .75),IN_H*.5]);A[:,2]-=A[:,:2]@(target-np.array([IN_W/2,IN_H/2]))
  img=sample(pyramid(gray),A);pts=to_input(A,kp)
  if mode=='dark':img=np.clip(img.astype(float)*.4,0,255).astype(np.uint8)
  if mode=='bright':img=np.clip(img.astype(float)*1.3+25,0,255).astype(np.uint8)
  if mode=='blur':img=cv2.GaussianBlur(img,(0,0),1.4)
  if mode=='jpeg':_,buf=cv2.imencode('.jpg',img,[cv2.IMWRITE_JPEG_QUALITY,30]);img=cv2.imdecode(buf,0)
  if mode=='perspective':
   H=cv2.getPerspectiveTransform(np.float32([[0,0],[384,0],[384,288],[0,288]]),np.float32([[25,16],[359,0],[384,288],[0,265]]))
   img=cv2.warpPerspective(img,H,(384,288),borderMode=cv2.BORDER_REPLICATE);pts=cv2.perspectiveTransform(pts[None].astype(np.float32),H)[0]
  if mode=='one_corner_occluded':
   x,y=np.rint(pts[2]).astype(int);cv2.rectangle(img,(x-7,y-7),(x+7,y+7),90,-1)
  cases.append((p.stem,mode,img,pts))
import refinement as local
net=DoorNet().cuda().eval();net.load_state_dict(torch.load(O/'step600.pt',map_location='cuda',weights_only=True))
expert=local.CornerNet().cuda().eval();expert.load_state_dict(torch.load(OUTPUT/('step'+sys.argv[1]+'.pt'),map_location='cuda',weights_only=True))
rows=[]
with torch.inference_mode():
 def run(x):return net(torch.from_numpy(x).cuda()).cpu().numpy()[0]
 for source,mode,img,kp in cases:
  result=detect(run,img,passes=2);found=result is not None and result[1].min()>=.5
  baseline=result[0] if found else None;updated=baseline;accepted=False
  if found:
   k=float(local.patch_scale(baseline));inputs=[];maps=[]
   for j in range(4):
    patch,A=local.runtime_crop(img,baseline[j],k,j);inputs.append(patch[None].astype(np.float32)/255);maps.append(A)
   point,conf=local.decode(expert(torch.from_numpy(np.stack(inputs)).cuda()).cpu().numpy())
   candidate=np.array([maps[j][:,:2]@point[j]+maps[j][:,2] for j in range(4)])
   width=(np.linalg.norm(baseline[1]-baseline[0])+np.linalg.norm(baseline[3]-baseline[2]))/2
   accepted=bool(conf.min()>=.4 and (np.linalg.norm(candidate-baseline,axis=1)<=max(1.5,width*.08)).all())
   if accepted:updated=candidate
  height=max(np.linalg.norm(kp[2]-kp[0]),np.linalg.norm(kp[3]-kp[1]));width=(np.linalg.norm(kp[1]-kp[0])+np.linalg.norm(kp[3]-kp[2]))/2
  olderr=float(np.linalg.norm(baseline-kp,axis=1).max()) if found else None
  err=float(np.linalg.norm(updated-kp,axis=1).max()) if found else None
  rows.append({'source':source,'mode':mode,'detected':bool(found),'accepted':accepted,'baseline_error':olderr,'candidate_error':err,'baseline_coarse':bool(found and olderr<=.05*height),'candidate_coarse':bool(found and err<=.05*height),'baseline_strict':bool(found and olderr<=.01*width),'candidate_strict':bool(found and err<=.01*width)})
summary={}
for mode in modes:
 rs=[r for r in rows if r['mode']==mode]
 summary[mode]={k:sum(r[k] for r in rs) for k in ['detected','accepted','baseline_coarse','candidate_coarse','baseline_strict','candidate_strict']}
passed=all(s['candidate_coarse']>=s['baseline_coarse'] for s in summary.values())
(OUTPUT/('runtime_stress_'+sys.argv[1]+'.json')).write_text(json.dumps({'scope':'117 transforms from 9 same-source training images; not independent physical accuracy','passes_no_regression_gate':passed,'summary':summary,'rows':rows},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(summary));print('STRESS_GATE',passed,flush=True)
