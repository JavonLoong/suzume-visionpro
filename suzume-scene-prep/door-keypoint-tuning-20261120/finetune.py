import sys,time,json,random
from pathlib import Path
sys.path.insert(0,'D:/虚拟C盘/JavonLoongSkill/suzume-scene-prep/door-keypoint-model-20261118')
from train import Doors,loss_fn,Loader
from common import *
from concurrent.futures import ThreadPoolExecutor
root=Path(__file__).resolve().parent
torch.manual_seed(20261120);np.random.seed(20261120);random.seed(20261120);torch.set_num_threads(4)
synthetic=Doors(['D:/虚拟C盘/JavonLoongSkill/suzume-scene-prep/door-keypoint-train-20261118','D:/虚拟C盘/JavonLoongSkill/suzume-scene-prep/door-keypoint-dataset-20261118'],'train',True)
real=Doors([root/'training-real'],'train',True)
net=DoorNet().cuda();net.load_state_dict(torch.load('D:/suzume-door-fix-20261120/door_net_step100.pt',map_location='cuda',weights_only=True));net.train()
for mod in net.modules():
    if isinstance(mod,torch.nn.BatchNorm2d):mod.eval()
opt=torch.optim.AdamW(net.parameters(),lr=1e-5,weight_decay=1e-4);scaler=torch.amp.GradScaler()
pool=ThreadPoolExecutor(6);t=time.time();print('start',len(synthetic),len(real),flush=True)
for step in range(600):
    tasks=[pool.submit(synthetic.__getitem__,np.random.randint(len(synthetic))) for _ in range(8)]+[pool.submit(real.__getitem__,np.random.randint(len(real))) for _ in range(4)]
    batch=[torch.stack(a).cuda() for a in zip(*[t.result() for t in tasks])];img,heat,off,mask,_=batch
    opt.zero_grad(set_to_none=True)
    with torch.autocast('cuda',dtype=torch.float16):out=net(img)
    loss,hl,ol=loss_fn(out,heat,off,mask);scaler.scale(loss).backward();scaler.step(opt);scaler.update()
    if step%20==19:print(step+1,round(loss.item(),4),round(time.time()-t,1),flush=True)
    if step in [199,399,599]:torch.save(net.state_dict(),root/f'door_net_step{step+1}.pt')
print('TRAIN_DONE',flush=True)
