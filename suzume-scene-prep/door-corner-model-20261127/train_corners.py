from pathlib import Path
import json,time,math,sys
import numpy as np,torch,cv2
from concurrent.futures import ThreadPoolExecutor
from refinement import *

ROOT=Path(__file__).resolve().parent
torch.set_num_threads(4);cv2.setNumThreads(0);torch.manual_seed(20261127)
render=items(Path('D:/虚拟C盘/JavonLoongSkill/suzume-scene-prep/door-keypoint-train-20261118'))
opened=[x for x in render if x[3]>=30]
screen=items(Path('D:/suzume-door-tuning-20261120/training-real'))
ai=items(Path('D:/虚拟C盘/学习秋/单门内沿贴合训练_20261125/dataset'))
net=CornerNet().cuda();optimizer=torch.optim.AdamW(net.parameters(),lr=.0005,weight_decay=.0001)
scaler=torch.amp.GradScaler();pool=ThreadPoolExecutor(4);rng=np.random.RandomState(20261127)
config={'seed':20261127,'steps':1000,'batch':64,'parameters':sum(p.numel() for p in net.parameters()),
 'mix':{'render_open':32,'render_any':16,'screen_train':8,'ai_same_source':8},'headset_tested':False,'independent_new_real_images':0,
 'corner_order':['BL','BR','TL','TR'],'crop_size':64,'crop_span_width_fraction':.5,'minimum_source_span':12,'maximum_source_span':160,
 'label_scope':'Visible inner-aperture corners; original global model supplies all evaluation candidates.'}
(ROOT/'config.json').write_text(json.dumps(config,ensure_ascii=False,indent=2),encoding='utf-8')
start=time.time()
for step in range(1,1001):
 net.train();jobs=[]
 for source,n in [(opened,32),(render,16),(screen,8),(ai,8)]:
  for _ in range(n):
   item=source[rng.randint(len(source))];seed=int(rng.randint(2147483647))
   jobs.append(pool.submit(training_sample,item,np.random.RandomState(seed)))
 batch=[j.result() for j in jobs];images=torch.from_numpy(np.stack([x[0] for x in batch])).cuda();targets=torch.from_numpy(np.stack([x[1] for x in batch])).cuda()
 for group in optimizer.param_groups:group['lr']=.0005*(.15+.85*(1+math.cos(math.pi*(step-1)/1000))/2)
 optimizer.zero_grad(set_to_none=True)
 with torch.autocast('cuda',dtype=torch.float16):output=net(images)
 loss=loss_fn(output,targets);assert torch.isfinite(loss)
 scaler.scale(loss).backward();scaler.unscale_(optimizer);torch.nn.utils.clip_grad_norm_(net.parameters(),5);scaler.step(optimizer);scaler.update()
 if step%50==0:print('STEP',step,'loss',round(loss.item(),4),'seconds',round(time.time()-start,1),flush=True)
 if step in (300,600,1000):torch.save(net.state_dict(),ROOT/f'step{step}.pt')
pool.shutdown();print('CORNER_TRAIN_DONE',flush=True)
