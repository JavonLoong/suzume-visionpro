from pathlib import Path
import json,sys,time,hashlib
import numpy as np,torch,onnx,onnxruntime as ort
from refinement import *
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'edge-validation'))
from evaluate_lines import ev,baseline
candidate=json.loads((ROOT/'runtime_all_four_step6000_threshold0.5_evaluation.json').read_text(encoding='utf-8'))
for group,b in baseline['summary'].items():
 c=candidate['summary'][group]
 assert c['coarse_accurate']>=b['accurate_within_5pct_height'],group
assert json.loads((ROOT/'final_stress_6000.json').read_text(encoding='utf-8'))['passes_no_regression_gate']
net=CornerNet().cpu().eval();net.load_state_dict(torch.load(ROOT/'step6000.pt',map_location='cpu',weights_only=True))
path=ROOT/'door_corner.onnx';torch.onnx.export(net,torch.rand(4,1,64,64),str(path),opset_version=9,input_names=['patches'],output_names=['maps'],dynamo=False)
onnx.checker.check_model(str(path));options=ort.SessionOptions();options.intra_op_num_threads=4
session=ort.InferenceSession(str(path),sess_options=options,providers=['CPUExecutionProvider'])
fixture=ROOT/'reference';fixture.mkdir(exist_ok=True);rows=[];differences=[];times=[];render_count=0
with torch.inference_mode():
 for i,(row,case) in enumerate(zip(baseline['rows'],ev.eval_cases)):
  if not row['detected']:continue
  if row['group']=='render_val':
   render_count+=1
   if render_count%9!=0:continue
  points=np.asarray(row['points']);k=float(patch_scale(points));patches=[];maps=[]
  for j in range(4):
   patch,A=runtime_crop(case[3][0],points[j],k,j);patches.append(patch[None]/255);maps.append(A)
  inputs=np.stack(patches).astype(np.float32);start=time.perf_counter();output=session.run(None,{'patches':inputs})[0];times.append((time.perf_counter()-start)*1000)
  expected=net(torch.from_numpy(inputs)).numpy();differences.append(float(np.abs(output-expected).max()))
  local,conf=decode(output);refined=np.array([maps[j][:,:2]@local[j]+maps[j][:,2] for j in range(4)])
  width=(np.linalg.norm(points[1]-points[0])+np.linalg.norm(points[3]-points[2]))/2
  accepted=bool(conf.min()>=.5 and (np.linalg.norm(refined-points,axis=1)<=max(1.5,width*.08)).all())
  gray=case[3][0];name=f'{i:04d}.gray';(fixture/name).write_bytes(gray.tobytes())
  rows.append({'image':name,'width':gray.shape[1],'height':gray.shape[0],'input':points.ravel().tolist(),'output':(refined if accepted else points).ravel().tolist(),'scores':conf.astype(float).tolist(),'accepted':accepted,'group':row['group']})
assert max(differences)<.0001,max(differences)
(fixture/'reference.json').write_text(json.dumps({'cases':rows},ensure_ascii=False,indent=2),encoding='utf-8')
report={'model':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'checkpoint':'step6000.pt',
 'onnx_max_abs_error':max(differences),'fixture_cases':len(rows),'cpu_onnx_batch4_ms_median':float(np.median(times[2:])),
 'parameters':sum(p.numel() for p in net.parameters()),'policy':'All 4 corners score >= 0.5 and all displacements <= max(1.5 px, 0.08 * predicted width); otherwise preserve all original corners.',
 'development_metrics':candidate['summary'],'headset_tested':False,'independent_real_accuracy_verified':False,'apk_integrated':False}
(ROOT/'模型核验.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False),flush=True)
