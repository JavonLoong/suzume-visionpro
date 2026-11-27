from pathlib import Path
import sys,json,time,copy
import numpy as np,torch,cv2
from refinement import *
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'edge-validation'))
from evaluate_lines import ev,baseline,metrics

def evaluate(net):
 predictions=[];start=time.time();net.eval()
 with torch.inference_mode():
  for row,case in zip(baseline['rows'],ev.eval_cases):
   assert row['image']==case[1]
   if not row['detected']:predictions.append(None);continue
   points=np.asarray(row['points']);k=float(patch_scale(points));patches=[];maps=[]
   for index in range(4):
    patch,A=crop(case[3][0],points[index],k,index);patches.append(patch[None].astype(np.float32)/255);maps.append(A)
   output=net(torch.from_numpy(np.stack(patches)).cuda()).cpu().numpy()
   local,scores=decode(output);refined=np.array([maps[j][:,:2]@local[j]+maps[j][:,2] for j in range(4)])
   predictions.append({'points':refined.tolist(),'scores':scores.astype(float).tolist()})
 return predictions,time.time()-start

if __name__=='__main__':
 summaries=json.loads((ROOT/'summaries.json').read_text(encoding='utf-8')) if (ROOT/'summaries.json').exists() else {'baseline':metrics(baseline['rows'])}
 net=CornerNet().cuda()
 for step in ([int(x) for x in sys.argv[1:]] or [300,600,1000]):
  path=ROOT/f'step{step}.pt'
  if not path.exists():continue
  net.load_state_dict(torch.load(path,map_location='cuda',weights_only=True));predictions=json.loads((ROOT/f'step{step}_predictions.json').read_text(encoding='utf-8'));elapsed=0
  (ROOT/f'step{step}_predictions.json').write_text(json.dumps(predictions),encoding='utf-8')
  for threshold in (.3,.4,.5):
   rows=copy.deepcopy(baseline['rows']);applied=0
   for row,prediction in zip(rows,predictions):
    if prediction is None:continue
    original=np.array(row['points']);refined=np.array(prediction['points'])
    width=(np.linalg.norm(original[1]-original[0])+np.linalg.norm(original[3]-original[2]))/2
    good=(np.array(prediction['scores'])>=threshold)&(np.linalg.norm(refined-original,axis=1)<=max(1.5,width*.08))
    good[:]=bool(good.all());original[good]=refined[good];row['points']=original.tolist();row['local_confidence']=prediction['scores'];row['refined_corners']=int(good.sum());applied+=int(good.sum())
   name=f'all_four_step{step}_threshold{threshold}';summaries[name]=metrics(rows)
   (ROOT/(name+'_evaluation.json')).write_text(json.dumps({'summary':summaries[name],'rows':rows},ensure_ascii=False,indent=2),encoding='utf-8')
   print(name,'applied',applied,'evaluation_seconds',round(elapsed,2),json.dumps(summaries[name]),flush=True)
 (ROOT/'summaries.json').write_text(json.dumps(summaries,ensure_ascii=False,indent=2),encoding='utf-8')
 print('CORNER_EVAL_DONE',flush=True)
