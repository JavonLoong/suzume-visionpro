import sys,json,re,hashlib,time
from pathlib import Path
sys.path.insert(0,'D:/虚拟C盘/JavonLoongSkill/suzume-scene-prep/door-keypoint-model-20261118')
from common import *
torch.set_num_threads(4);torch.manual_seed(20261120);root=Path(__file__).resolve().parent;old=Path('D:/suzume-door-fix-20261120')
synthetic=Path('D:/虚拟C盘/JavonLoongSkill/suzume-scene-prep/door-keypoint-train-20261118');labels=[json.loads(p.read_text(encoding='utf8')) for p in sorted((synthetic/'labels').glob('*.json'))];pos=[l for l in labels if l['split']=='val' and l.get('door_present',True)][:200];neg=[l for l in labels if l['split']=='val' and not l.get('door_present',True)]
cases=[]
def add(im,kp,kind,name,variants):
 for variant,g in enumerate(variants):
  pyr=pyramid(g);lo,hi=kp.min(0),kp.max(0);size=max(hi-lo)
  for fill in ([.3,.45,.6] if kind=='real' else [.4]):
   h=min(max(size/fill,72),g.shape[0],g.shape[1]*.75);w=h*4/3;ctr=np.clip((lo+hi)/2,[w/2,h/2],[g.shape[1]-w/2,g.shape[0]-h/2]);cases.append((kind,name,variant,fill,pyr,make_affine(ctr,h/IN_H),kp))
for l in pos:
 im=imread_gray(synthetic/l['image']);kp=np.array(l['keypoints'])[:,:2];add(im,kp,'synthetic',l['image'],[im])
for n in ['001','002','004']:
 l=json.loads((old/'real/labels'/f'{n}.json').read_text());im=imread_gray(old/'real'/l['image']);kp=np.array(l['keypoints'])[:,:2]
 variants=[im,np.clip(im.astype(float)*.65,0,255).astype('uint8'),np.clip(im.astype(float)*1.2+15,0,255).astype('uint8'),cv2.GaussianBlur(im,(0,0),1.2),cv2.GaussianBlur(im,(0,0),2.0),np.clip((im.astype(float)/255)**1.7*255,0,255).astype('uint8')];add(im,kp,'real',n,variants)
negative=[]
for l in neg:
 im=imread_gray(synthetic/l['image']);pyr=pyramid(im)
 for ratio in [1,.5,.25]:negative.append((pyr,make_affine((im.shape[1]*.5,im.shape[0]*.5),im.shape[1]/IN_W*ratio)))
for n in ['005','006']:
 im=imread_gray(old/'real/images'/f'{n}.pgm');pyr=pyramid(im)
 for xx in [.25,.5,.75]:
  for yy in [.25,.5,.75]:negative.append((pyr,make_affine((im.shape[1]*xx,im.shape[0]*yy),1.5)))
results={}
with torch.no_grad():
 for name,path in [('baseline',old/'door_net_step100.pt')]+[(str(n),root/f'door_net_step{n}.pt') for n in [200,400,600]]:
  net=DoorNet().cuda().eval();net.load_state_dict(torch.load(path,map_location='cuda',weights_only=True));run=lambda x:net(torch.from_numpy(x).cuda()).float().cpu().numpy()[0]
  def pred(pyr,A):
   p,c=decode(run(sample(pyr,A).astype(np.float32)[None,None]/255));return to_source(A,p),c
  counts={k:dict(total=0,detected=0,errors=[]) for k in ['real','synthetic']};rows=[]
  for kind,n,v,fill,pyr,A,kp in cases:
   count=counts[kind];count['total']+=1;p,c=pred(pyr,A)
   if c.min()>=.3:p,c=pred(pyr,crop_affine(p))
   found=bool(c.min()>=.5);err=float(np.linalg.norm(p-kp,axis=1).max());rows.append(dict(kind=kind,name=n,variant=v,fill=fill,found=found,error=err,min_conf=float(c.min())))
   if found:count['detected']+=1;count['errors'].append(err)
  false=0
  for pyr,A in negative:
   p,c=pred(pyr,A)
   if c.min()>=.3:p,c=pred(pyr,crop_affine(p));false+=int(c.min()>=.5)
  for count in counts.values():
   errors=count.pop('errors');count['median_error']=float(np.median(errors)) if errors else None;count['p90_error']=float(np.percentile(errors,90)) if errors else None
  results[name]=dict(metrics=counts,negative_crops=len(negative),false_positive_crops=false,rows=rows)
  print(name,counts,'false',false,'/',len(negative),flush=True)
(root/'robust-evaluation.json').write_text(json.dumps(results,indent=2))
