import json,subprocess,sys,time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
R=Path(__file__).resolve().parents[1];d=json.loads((R/'analysis/source-manifest.json').read_text(encoding='utf8'))
rows=[x for x in d['parts'] if not x['id'].startswith('B')]
def run(row):
 n=row['id'];start=time.time();folder=R/'analysis/geometry_logs';folder.mkdir(exist_ok=True)
 saved=R/'analysis/validated_parts'/(n+'.json')
 if saved.exists():return json.loads(saved.read_text(encoding='utf8'))
 with (folder/(n+'.log')).open('w',encoding='utf8') as log:
  p=subprocess.run([sys.executable,str(R/'scripts/finish_quality_geometry.py'),n],stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW,timeout=600)
 print('PART_RESULT',n,p.returncode,round(time.time()-start,1),flush=True)
 if p.returncode:raise RuntimeError(n+' failed: '+(folder/(n+'.log')).read_text(encoding='utf8')[-2000:])
 return json.loads((R/'analysis/validated_parts'/(n+'.json')).read_text(encoding='utf8'))
results=[];errors=[]
with ThreadPoolExecutor(max_workers=2) as ex:
 futures={ex.submit(run,row):row['id'] for row in rows}
 for f in as_completed(futures):
  try:results.append(f.result())
  except Exception as e:errors.append({'part':futures[f],'error':str(e)})
(R/'analysis/geometry_errors.json').write_text(json.dumps(errors,ensure_ascii=False,indent=2),encoding='utf8')
assert not errors,errors
results.sort(key=lambda x:next(i for i,r in enumerate(rows) if r['id']==x['row']['id']))
d['parts']=[x['row'] for x in results];d['export_validation']=[x['report'] for x in results];d['quality_revision']='白模可靠版：实体重建、钢架加厚、游离景物接到底托、白门把手接缝修正。'
(R/'交付文件/零件清单.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
(R/'analysis/final-geometry-checks.json').write_text(json.dumps([x['report'] for x in results],ensure_ascii=False,indent=2),encoding='utf8')
print('ALL_PARTS_VERIFIED',len(results),flush=True)
